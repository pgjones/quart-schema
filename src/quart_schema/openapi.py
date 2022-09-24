from typing import Any, Dict, Optional

from pydantic import AnyHttpUrl, BaseModel, Extra, root_validator


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
