from dataclasses import dataclass, field, fields
from typing import Any, Dict, Literal, Optional

import humps


class _SchemaBase:
    def schema(self, *, camelize: bool = False) -> Dict:
        result: Dict[str, Any] = {}
        for field_ in fields(self):  # type: ignore
            value = getattr(self, field_.name, None)

            if value is not None:
                name = field_.metadata.get("alias", field_.name)
                if camelize:
                    humps.camelize(name)
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

    enum: str
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
