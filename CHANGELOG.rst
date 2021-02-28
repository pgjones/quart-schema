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
