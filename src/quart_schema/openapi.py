from __future__ import annotations

import inspect
import re
from collections import defaultdict
from dataclasses import dataclass, field, fields
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Literal,
    Optional,
    Tuple,
    Type,
    TYPE_CHECKING,
)
from weakref import proxy

import humps
from quart import Quart
from werkzeug.routing.converters import AnyConverter, BaseConverter, NumberConverter
from werkzeug.routing.rules import Rule

from .conversion import model_schema
from .typing import Model
from .validation import (
    DataSource,
    QUART_SCHEMA_HEADERS_ATTRIBUTE,
    QUART_SCHEMA_QUERYSTRING_ATTRIBUTE,
    QUART_SCHEMA_REQUEST_ATTRIBUTE,
    QUART_SCHEMA_RESPONSE_ATTRIBUTE,
)

if TYPE_CHECKING:
    from .extension import QuartSchema

QUART_SCHEMA_HIDDEN_ATTRIBUTE = "_quart_schema_hidden"
QUART_SCHEMA_TAG_ATTRIBUTE = "_quart_schema_tag"
QUART_SCHEMA_OPERATION_ID_ATTRIBUTE = "_quart_schema_operation_id"
QUART_SCHEMA_SECURITY_ATTRIBUTE = "_quart_schema_security_tag"
QUART_SCHEMA_DEPRECATED_ATTRIBUTE = "_quart_schema_deprecated"

PATH_RE = re.compile("<(?:[^:]*:)?([^>]+)>")


class OpenAPIProvider:
    def __init__(self, app: Quart, extension: QuartSchema) -> None:
        self._app = proxy(app)
        self._extension = extension

    def schema(self) -> Dict[str, Any]:
        """Builds an OpenAPI specified schema of the app's routes
        given the extension's settings.

        """
        schema = {
            "openapi": "3.1.0",
            "info": self._extension.info.schema(camelize=True),
            "paths": defaultdict(dict),
            "components": {
                "schemas": {},
            },
        }
        for rule in self.generate_rules():
            path_objects, path_components = self.build_paths(rule)

            for path, path_object in path_objects.items():
                schema["paths"][path].update(path_object)  # type: ignore
            schema["components"]["schemas"].update(path_components)  # type: ignore

        if self._extension.security_schemes is not None:
            schema["components"]["securitySchemes"] = {  # type: ignore
                key: value.schema(camelize=True)
                for key, value in self._extension.security_schemes.items()
            }

        if self._extension.tags is not None:
            schema["tags"] = [tag.schema(camelize=True) for tag in self._extension.tags]
        if self._extension.security is not None:
            schema["security"] = self._extension.security
        if self._extension.servers is not None:
            schema["servers"] = [server.schema(camelize=True) for server in self._extension.servers]
        if self._extension.external_docs is not None:
            schema["externalDocs"] = self._extension.external_docs.schema(camelize=True)

        return schema

    def generate_rules(self) -> Iterable[Rule]:
        """Generate the rules to include in the schema

        This can be overridden to change which rules are included and
        the order of those rules.

        Returns:
            An iterable of the rules to include ordered as desired.

        """
        for rule in self._app.url_map.iter_rules():
            hidden = getattr(
                self._app.view_functions[rule.endpoint], QUART_SCHEMA_HIDDEN_ATTRIBUTE, False
            )
            if not hidden and not rule.websocket:
                yield rule

    def build_paths(self, rule: Rule) -> Tuple[dict, dict]:
        """Build the path objects given the rule

        This can be overridden to alter how paths are built from a rule.

        Arguments:
            rule: The rule to build paths for.

        Returns:
            Path objects keyed by the path.

        """
        func = self._app.view_functions[rule.endpoint]
        parts = rule.endpoint.rsplit(".", 1)
        blueprint = None
        if len(parts) > 1:
            blueprint = self._app.blueprints.get(parts[0])

        components = {}
        operation_object: Dict[str, Any] = {
            "parameters": [],
            "responses": {},
        }
        if func.__doc__ is not None:
            summary, *description = inspect.getdoc(func).splitlines()
            operation_object["description"] = "\n".join(description)
            operation_object["summary"] = summary

        tags: set[str] = set()
        tags |= getattr(func, QUART_SCHEMA_TAG_ATTRIBUTE, set())
        tags |= getattr(blueprint, QUART_SCHEMA_TAG_ATTRIBUTE, set())

        if len(tags) > 0:
            operation_object["tags"] = list(tags)

        if getattr(func, QUART_SCHEMA_DEPRECATED_ATTRIBUTE, None) or getattr(
            blueprint, QUART_SCHEMA_DEPRECATED_ATTRIBUTE, None
        ):
            operation_object["deprecated"] = True

        security_schemes = []
        if (schemes := getattr(func, QUART_SCHEMA_SECURITY_ATTRIBUTE, None)) is not None:
            security_schemes.extend(schemes)
        if (schemes := getattr(blueprint, QUART_SCHEMA_SECURITY_ATTRIBUTE, None)) is not None:
            security_schemes.extend(schemes)

        if len(security_schemes) > 0:
            operation_object["security"] = security_schemes

        for name, converter in rule._converters.items():
            parameter_object = self.build_path_parameter(name, converter)
            operation_object["parameters"].append(parameter_object)

        headers_model = getattr(func, QUART_SCHEMA_HEADERS_ATTRIBUTE, None)
        if headers_model is not None:
            parameter_objects, header_components = self.build_headers_parameters(headers_model)
            operation_object["parameters"].extend(parameter_objects)
            components.update(header_components)

        querystring_model = getattr(func, QUART_SCHEMA_QUERYSTRING_ATTRIBUTE, None)
        if querystring_model is not None:
            parameter_objects, querystring_components = self.build_querystring_parameters(
                querystring_model
            )
            operation_object["parameters"].extend(parameter_objects)
            components.update(querystring_components)

        request_data = getattr(func, QUART_SCHEMA_REQUEST_ATTRIBUTE, None)
        if request_data is not None:
            request_body, request_components = self.build_request_body(
                request_data[0], request_data[1]
            )
            operation_object["requestBody"] = request_body
            components.update(request_components)

        response_models = getattr(func, QUART_SCHEMA_RESPONSE_ATTRIBUTE, {})
        for status_code in response_models.keys():
            response_model, headers_model = response_models[status_code]
            response_object, response_components = self.build_response_object(
                response_model, headers_model
            )
            operation_object["responses"][status_code] = response_object
            components.update(response_components)

        path = re.sub(PATH_RE, r"{\1}", rule.rule)
        paths = {path: {}}  # type: ignore

        for method in self.generate_methods(rule):
            per_method_operation_object = operation_object.copy()

            operation_id = self.operation_id(method, func)
            if operation_id is not None:
                per_method_operation_object["operationId"] = operation_id

            paths[path][method.lower()] = per_method_operation_object
        return paths, components

    def build_path_parameter(self, name: str, converter: BaseConverter) -> Dict[str, Any]:
        """Build the openapi path parameter objects based on the converter.

        The can be overridden to alter how path parameter objects are built.

        Arguments:
            name: The name of the paramter.
            converter: The converter used.

        Returns:
            The built parameter object.

        """
        schema: Dict[str, Any]
        if isinstance(converter, AnyConverter):
            schema = {"enum": list(converter.items)}
        elif isinstance(converter, NumberConverter):
            schema = {"type": "number"}
        else:
            schema = {"type": "string"}

        return {
            "name": name,
            "in": "path",
            "required": True,
            "schema": schema,
        }

    def build_querystring_parameters(
        self, model: Type[Model]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Build the openapi parameter objects based on the querystring model.

        The can be overridden to alter how parameter objects are built.

        Arguments:
            model: The model of the querystring data.

        Returns:
            A tuple of the built parameter objects and component definitions.

        """
        schema = model_schema(
            model, preference=self._app.config["QUART_SCHEMA_CONVERSION_PREFERENCE"]
        )
        definitions, schema = _split_convert_definitions(
            schema, self._app.config["QUART_SCHEMA_CONVERT_CASING"]
        )
        parameters = []
        for name, type_ in schema["properties"].items():
            param = {"name": name, "in": "query", "schema": type_}

            for attribute in ("description", "required", "deprecated"):
                if attribute in type_:
                    param[attribute] = type_.pop(attribute)

            parameters.append(param)

        return parameters, definitions

    def build_headers_parameters(
        self, model: Type[Model]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Build the openapi parameter objects based on the headers model.

        The can be overridden to alter how parameter objects are built.

        Arguments:
            model: The model of the headers data.

        Returns:
            A tuple of the built parameter objects and component definitions.

        """
        schema = model_schema(
            model, preference=self._app.config["QUART_SCHEMA_CONVERSION_PREFERENCE"]
        )
        definitions, schema = _split_definitions(schema)
        parameters = []
        for name, type_ in schema["properties"].items():
            param = {"name": humps.kebabize(name), "in": "header", "schema": type_}

            for attribute in ("description", "required", "deprecated"):
                if attribute in type_:
                    param[attribute] = type_.pop(attribute)

            parameters.append(param)

        return parameters, definitions

    def build_request_body(
        self, model: Type[Model], source: DataSource
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Build the openapi request body object based on the model.

        The can be overridden to alter how request body objects are built.

        Arguments:
            model: The model the request accepts
            source: The encoding source of the data

        Returns:
            A tuple of the built request body object and component definitions.

        """
        schema = model_schema(
            model, preference=self._app.config["QUART_SCHEMA_CONVERSION_PREFERENCE"]
        )
        definitions, schema = _split_convert_definitions(
            schema, self._app.config["QUART_SCHEMA_CONVERT_CASING"]
        )

        if source == DataSource.JSON:
            encoding = "application/json"
        elif source == DataSource.FORM_MULTIPART:
            encoding = "multipart/form-data"
        else:
            encoding = "application/x-www-form-urlencoded"

        request_body = {
            "content": {
                encoding: {
                    "schema": schema,
                },
            },
        }
        return request_body, definitions

    def build_response_object(
        self, model: Type[Model], headers_model: Optional[Type[Model]]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Build the openapi response object based on the model.

        The can be overridden to alter how reponse objects are built.

        Arguments:
            model: The model the response returns

        Returns:
            A tuple of the built response object and component definitions.

        """
        schema = model_schema(
            model,
            preference=self._app.config["QUART_SCHEMA_CONVERSION_PREFERENCE"],
            schema_mode="serialization",
        )
        definitions, schema = _split_convert_definitions(
            schema, self._app.config["QUART_SCHEMA_CONVERT_CASING"]
        )
        response_object = {
            "content": {
                "application/json": {
                    "schema": schema,
                },
            },
            "description": "",
        }
        if model.__doc__ is not None:
            response_object["description"] = inspect.getdoc(model)

        if headers_model is not None:
            schema = model_schema(
                headers_model,
                preference=self._app.config["QUART_SCHEMA_CONVERSION_PREFERENCE"],
            )
            header_definitions, schema = _split_definitions(schema)
            definitions.update(header_definitions)
            response_object["content"]["headers"] = {  # type: ignore
                humps.kebabize(name): {
                    "schema": type_,
                }
                for name, type_ in schema["properties"].items()
            }
        return response_object, definitions

    def generate_methods(self, rule: Rule) -> Iterable[str]:
        """Generate the methods to include for the rule

        This can be overridden to change which methods are included
        and the order of those methods.

        Returns:
            An iterable of the methods to include ordered as desired.

        """
        for method in rule.methods:
            if method == "HEAD" or (method == "OPTIONS" and rule.provide_automatic_options):  # type: ignore # noqa: E501
                continue

            yield method

    def operation_id(self, method: str, func: Callable) -> Optional[str]:
        """Return a unique operation ID or None

        Override this to alter how the operation ID is generated.

        Arguments:
            method: The method of the operation.
            func: The route handler for the operation

        Returns:
            The operation ID or None if there is no operation ID.

        """
        id_ = getattr(func, QUART_SCHEMA_OPERATION_ID_ATTRIBUTE, func.__name__)
        return f"{method.lower()}_{id_}"


class _SchemaBase:
    def schema(self, *, camelize: bool = False) -> Dict:
        result: Dict[str, Any] = {}
        for field_ in fields(self):  # type: ignore
            value = getattr(self, field_.name, None)

            if value is not None:
                name = field_.metadata.get("alias", field_.name)
                if camelize:
                    name = humps.camelize(name)
                result[name] = value
        return result


@dataclass
class Contact(_SchemaBase):
    """This describes contact information for the API.

    It can be extended as desired.

    Attributes:
        email: Contact email address.
        name: Contact name.
        url: Contact URL.
    """

    email: Optional[str] = None
    name: Optional[str] = None
    url: Optional[str] = None


@dataclass
class License(_SchemaBase):
    """This describes license for the API.

    It can be extended as desired.

    Attributes:
        name: The name of the API.
        identifier: An SPDX license expression.
        url: A URL to the license used for the API.
    """

    name: str
    identifier: Optional[str] = None
    url: Optional[str] = None

    def __post_init__(self) -> None:
        if self.identifier is not None and self.url is not None:
            raise ValueError("The *identifier* field is mutually exclusive of the *url* field.")


@dataclass
class Info(_SchemaBase):
    """This provides meta data about the API.

    It can be extended as desired.

    Attributes:
        description: A description of the API. OpenAPI allows
            CommonMark syntax.
        summary: Short summary of the API.
        terms_of_service: A URL link to the terms
        title: The title of the API.
        version: The version of the API documentation.
    """

    title: str
    version: str
    contact: Optional[Contact] = None
    description: Optional[str] = None
    license: Optional[License] = None
    summary: Optional[str] = None
    terms_of_service: Optional[str] = None


@dataclass
class ExternalDocumentation(_SchemaBase):
    """A reference to external documentation.

    It can be extended as desired.

    Attributes:
        description: A description of the external docs.
        url: The URL of the external docs.
    """

    url: str
    description: Optional[str] = None


@dataclass
class Tag(_SchemaBase):
    """A Metadata tag for a route or OpenAPI-operation.

    Attributes:
        description: A description for the tag. OpenAPI allows
            CommonMark syntax.
        external_docs: An extenal documentation description.
        name: The name of the tag.
    """

    name: str
    description: Optional[str] = None
    external_docs: Optional[ExternalDocumentation] = None


@dataclass
class ServerVariable(_SchemaBase):
    """A description of a Server Variable for server URL template
    substitution.

    It can be extended as desired.

    Attributes:
        enum: An enumeration of string values to be used if the
            substitution options are from a limited set.
        default: The default value to use for substitution.
        description: A description for the server variable. OpenAPI
            allows CommonMark syntax.
    """

    enum: Optional[List[str]]
    default: str
    description: Optional[str] = None

    def __post_init__(self) -> None:
        if len(self.enum) < 1:
            raise ValueError("Must be at least one enum value")


@dataclass
class Server(_SchemaBase):
    """A description of the server

    It can be extended as desired..

    Attributes:
        description: The host designated by the URL. OpenAPI allows
            CommonMark syntax.
        url: A URL to the target host.
        variables: A map between a variable name and its value.
    """

    url: str
    variables: Optional[Dict[str, ServerVariable]] = None
    description: Optional[str] = None


class SecuritySchemeBase(_SchemaBase):
    description: Optional[str] = None
    type: Literal["apiKey", "http", "mutualTLS", "oauth2", "openIdConnect"]


@dataclass
class APIKeySecurityScheme(SecuritySchemeBase):
    name: str
    in_: Literal["query", "header", "cookie"] = field(metadata={"alias": "in"})
    type: Literal["apiKey"] = "apiKey"


@dataclass
class HttpSecurityScheme(SecuritySchemeBase):
    scheme: str
    bearer_format: Optional[str] = None
    type: Literal["http"] = "http"


@dataclass
class OAuth2SecurityScheme(SecuritySchemeBase):
    flows: dict
    type: Literal["oauth2"] = "oauth2"


@dataclass
class OpenIdSecurityScheme(SecuritySchemeBase):
    open_id_connect_url: str
    type: Literal["openIdConnect"] = "openIdConnect"


def _split_definitions(schema: dict) -> Tuple[dict, dict]:
    new_schema = schema.copy()
    definitions = new_schema.pop("$defs", {})
    return definitions, new_schema


def _split_convert_definitions(schema: dict, convert_casing: bool) -> Tuple[dict, dict]:
    definitions, new_schema = _split_definitions(schema)
    if convert_casing:
        new_schema = humps.camelize(new_schema)
        if "required" in new_schema:
            new_schema["required"] = [humps.camelize(field) for field in new_schema["required"]]
        definitions = {key: humps.camelize(definition) for key, definition in definitions.items()}
        for key, definition in definitions.items():
            if "required" in definition:
                definition["required"] = [humps.camelize(field) for field in definition["required"]]
    return definitions, new_schema
