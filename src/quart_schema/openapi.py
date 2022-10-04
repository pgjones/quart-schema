from typing import Any, Dict, Optional

from pydantic import AnyHttpUrl, BaseModel, conlist, Extra, Field, root_validator

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal  # type: ignore


class Contact(BaseModel):
    """This describes contact information for the API.

    It can be extended as desired.

    Attributes:
        email: Contact email address.
        name: Contact name.
        url: Contact URL.
    """

    email: Optional[str] = None
    name: Optional[str] = None
    url: Optional[AnyHttpUrl] = None

    class Config:
        extra = Extra.allow


class License(BaseModel):
    """This describes license for the API.

    It can be extended as desired.

    Attributes:
        name: The name of the API.
        identifier: An SPDX license expression.
        url: A URL to the license used for the API.
    """

    name: str
    identifier: Optional[str] = None
    url: Optional[AnyHttpUrl] = None

    class Config:
        extra = Extra.allow

    @root_validator
    def check_only_identifier_or_url(cls, values: Dict[str, Any]) -> Dict[str, Any]:  # noqa: N805
        if values.get("identifier") is not None and values.get("url") is not None:
            raise ValueError("The *identifier* field is mutually exclusive of the *url* field.")
        return values


class Info(BaseModel):
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
    terms_of_service: Optional[AnyHttpUrl] = None

    class Config:
        extra = Extra.allow


class ExternalDocumentation(BaseModel):
    """A reference to external documentation.

    It can be extended as desired.

    Attributes:
        description: A description of the external docs.
        url: The URL of the external docs.
    """

    url: AnyHttpUrl
    description: Optional[str] = None

    class Config:
        extra = Extra.allow


class Tag(BaseModel):
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

    class Config:
        extra = Extra.allow


class ServerVariable(BaseModel):
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

    enum: conlist(str, min_items=1)  # type: ignore
    default: str
    description: Optional[str] = None

    class Config:
        extra = Extra.allow


class Server(BaseModel):
    """A description of the server

    It can be extended as desired..

    Attributes:
        description: The host designated by the URL. OpenAPI allows
            CommonMark syntax.
        url: A URL to the target host.
        variables: A map between a variable name and its value.
    """

    url: AnyHttpUrl
    variables: Optional[Dict[str, ServerVariable]] = None
    description: Optional[str] = None

    class Config:
        extra = Extra.allow


class SecuritySchemeBase(BaseModel):
    type: Literal["apiKey", "http", "mutualTLS", "oauth2", "openIdConnect"]
    description: Optional[str] = None

    class Config:
        extra = Extra.allow


class APIKeySecurityScheme(SecuritySchemeBase):
    type: Literal["apiKey"] = "apiKey"
    in_: Literal["query", "header", "cookie"] = Field(alias="in")
    name: str

    class Config:
        allow_population_by_field_name = True


class HttpSecurityScheme(SecuritySchemeBase):
    type: Literal["http"] = "http"
    scheme: str
    bearer_format: Optional[str] = None


class OAuth2SecurityScheme(SecuritySchemeBase):
    type: Literal["oauth2"] = "oauth2"
    flows: dict


class OpenIdSecurityScheme(SecuritySchemeBase):
    type: Literal["openIdConnect"] = "openIdConnect"
    open_id_connect_url: str
