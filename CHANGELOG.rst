0.22.0 2025-04-27
-----------------

* Allow Blueprints to be deprecated, tagged, marked with security
  schemes.
* Support TypedDicts as a type using Pydantic for validation.
* Bugfix ServerVariable.enum should be an optional list of strings.
* Bugfix Use url_for for the openapi path in the docs templates to get
  the correct path.

0.21.0 2025-01-01
-----------------

* Add a OpenAPIProvider to allow for customisation.
* Raise a RuntimeError on request validation if neither pydantic nor
  msgspec are installed.
* Switch from ResponseHeadersValidationError to RuntimeError if a
  Response is attempted to be validated.

0.20.1 2024-12-31
-----------------

* Bugfix any converter to openapi schema
* Bugfix ensure the OpenAPI field names are camelized.
* Support Python 3.13, drop Python 3.8.

0.20.0 2024-05-20
-----------------

* Bugfix the pydantic dataclass check.
* Bugfix list model class handling and type identification.
* Bugfix form multiselect request validation.
* Bugfix the deprecate decorator was meant to be called without
  arguments (this is backwards incompatible).
* Bugfix using msgspec without attrs
* Enhance pydantic model schema generation to utilise the schema mode
  as serialization for response models.
* Support all Pydantic dump options. This replaces
  ``QUART_SCHEMA_BY_ALIAS=True`` config value with the QuartSchema
  constructor argument ``pydantic_dump_options={"by_alias: True}`` or
  the ``QUART_SCHEMA_PYDANTIC_DUMP_OPTIONS`` config value.

0.19.1 2024-02-13
-----------------

* Bugfix the Scalar template.
* Improve the error message if neither msgpec nor pydantic installed.
* Use msgpec JSON conversion if Pydantic isn't installed.

0.19.0 2024-01-22
-----------------

* Support msgspec and attrs alongside Pydantic. This results in
  pydantic being an optional extra (install quart-schema[pydantic] to
  continue previous usage).
* Add ScalaR documentation UI support.
* Switch the openapi structure classes to stdlib dataclasses.
* Improve the make_response performance for pydantic dataclasses.
* Simplify the pydantic usage via the TypeAdapter thereby allowing for
  list and dict top level models.

0.18.0 2023-11-12
-----------------

* Render Werkzeug's any() route parameters as enum in OpenAPI.
* Support Quart 0.19 onwards.
* Support Python 3.12 drop Python 3.7.
* Bugfix WebSocket validation check for convert casing config param.
* Bugfix handle status/headers when returning a Response.
* Fix pydantic deprecation warnings.

0.17.1 2023-08-29
-----------------

* Update the Swagger UI js and css versions.

0.17.0 2023-08-22
-----------------

* Support Pydantic 2 (dropping support for Pydantic 1).
* Remove constraints on Querystring and Form models (can have
  non-optional and nested structure respectively).
* Add support for querystring list parameters.
* Add support for operationID.
* Add provision support for File types.
* Bugfix check if the headers value not body type matches.
* Bugfix cope with returned responses.

0.16.0 2023-05-08
-----------------

* Switch to app.json.dumps rather than json.dumps in schema cmd, so as
  to use any specific JSON encoding.
* Restore usage of the pydantic encoder by default, to match the
  pydantic decoding.
* Add documentation only decorators matching the validation versions.

0.15.0 2023-02-27
-----------------

* Consistently apply casing conversion. This ensures that Quart-Schema
  does not affect the general JSONProvider and hence other usages of
  JSON conversions. This could introduce bugs if you were expecting
  this, if so please write a JSONProvider directly.
* Ensure the config convert casing setting is the authoritive source
  (not the extension attribute).
* Officially support Python 3.11.
* Bugfix casing of required fields.

0.14.3 2022-10-11
-----------------

* Bugfix JSONProvider encoding.

0.14.2 2022-10-08
-----------------

* Bugfix ensure paths are correctly merged in the generated OpenAPI
  schema.

0.14.1 2022-10-04
-----------------

* Bugfix allow_population_by_field_name.

0.14.0 2022-10-04
-----------------

* Add an info argument and model for OpenAPI info. This is backwards
  incompatible as the title and version arguments are removed.
* Switch from hide_route to hide. This is backwards incompatible as
  the decorator name has changed.
* Clarify how the OpenAPI schema is camelized when converting case
  (fix issues with incorrect casing in the openapi JSON).
* Convert the remaining input objects to Pydantic models, with
  dictionaries still accepted.
* Add deprecation decorator to mark routes as deprecated.
* Add the ability to specify external docs.
* Add QUART_SCHEMA_BY_ALIAS to the config to specify by_alias usage
  for response models.
* Bugfix JSONProvider loads convert casing usage.
* Bugfix compatibility with Quart 0.18.1, which is now the minimum
  required.

0.13.0 2022-09-04
-----------------

* Make it clear that redocs require Javascript to work.
* Add the ability to add security tags.
* Ensure the tag decorator overwrites any existing, this is a
  backwards incompatible change.
* Ensure casing conversion happens for request query string args.

0.12.0 2022-07-23
-----------------

* Increase swagger version to 4.12.0.
* Render endpoint summary not as code.
* Bugfix ignore websocket routes when generating openapi description.
* Require Quart >= 0.18
* Switch to GitHub rather than GitLab.

0.11.1 2022-02-03
-----------------

* Bugfix add auth parameter to TestClientMixin.

0.11.0 2022-02-03
-----------------

* Support validation of request headers, including the description of
  the headers in the OpenAPI schema.
* Support validation of response headers, including the description of
  the headers in the OpenAPI schema.
* Add a single decorator ``validate`` shorthand.
* Fix and improve the response summary & description, so as to match
  the OpenAPI specification.
* Add schema to the path parameters, so as to better describe and
  match the OpenAPI specification.
* Add specific errors for Querystring and header validation, so they
  can be handled differently to Request body validation if desired.
* Bugfix ensure required is set for path paramters, so as to match the
  OpenAPI specification.

0.10.0 2021-07-26
-----------------

* Add a ``quart schema`` command which outputs the QUART_APP schema to
  stdout or a file.
* Bugfix ensure the output is compliant with the openapi spec.

0.9.0 2021-07-21
----------------

* Improve the typing. This should result in less type: ignores being
  required.
* Support stdlib dataclasses, alongside the existing pydantic
  dataclass support - with the former prefered.

0.8.0 2021-05-11
----------------

* Support Quart 0.15.0 as the minimum version.
* Add spec for OpenAPI servers within openapi route.
* Make the Pydantic validation error available.
* Update to swagger-ui 3.47.1.

0.7.0 2021-03-04
----------------

* Support automatically converting between camelCased JSON and
  snake_cased model/dataclass variable names. This introduces the
  pyhumps dependency.

0.6.0 2021-02-28
----------------

* Improve testing, and support easy hypothesis testing. This allows
  Pydantic models and dataclasses to be sent from the test client.
* Bugfix correct error message.
* Bugfix response validation logic.
* Store the model type rather than derived schema (no noticeable
  impact on the public API).

0.5.0 2021-02-16
----------------

* Allow routes to be tagged.

0.4.0 2020-12-23
----------------

* Ensure models/dataclasses are converted to a dict, thereby
  preventing confusing errors when model/dataclass instances are
  returned without validation.
* Allow validation of form encoded data, in the same way JSON encoded
  data is currently validated.

0.3.0 2020-12-18
----------------

* Add the ability to hide routes from the openapi specification. This
  changes routes from default hidden to default visible.

0.2.0 2020-12-13
----------------

* Support validation of Query string parameters. Via a
  ``validate_querystring`` decorator.
* Support auto-documenting path parameters.
* Only include routes in the OpenAPI that have documented information.
* Split the route docstring into OpenAPI summary and description for
  the route.
* Add documentation UI using redoc.
* Allow the JS/CSS URLS for the documentation UI to be configured.

0.1.0 2020-12-08
----------------

* Basic initial release to test the schema usage.
