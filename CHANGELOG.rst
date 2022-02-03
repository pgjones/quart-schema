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
