Configuring Quart-Schema
========================

The following configuration options are used by Quart-Schema. They
should be set as part of the standard `Quart configuration
<https://pgjones.gitlab.io/quart/how_to_guides/configuration.html>`_.

================================== ===================
Configuration key                  type
---------------------------------- -------------------
QUART_SCHEMA_CONVERSION_PREFERENCE str
QUART_SCHEMA_SWAGGER_JS_URL        str
QUART_SCHEMA_SWAGGER_CSS_URL       str
QUART_SCHEMA_REDOC_JS_URL          str
QUART_SCHEMA_PYDANTIC_DUMP_OPTIONS PydanticDumpOptions
QUART_SCHEMA_CONVERT_CASING        bool
================================== ===================

which allow the js and css for the documentation UI to be changed and
configured.

The Pydantic Dump Options should be a dictionary ``dict[str, Any]``
and will be passed to Pydantic's model_dump method as keyword
arguments. The options are typed via
:class:`~quart_schema.PydanticDumpOptions`.
