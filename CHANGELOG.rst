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
