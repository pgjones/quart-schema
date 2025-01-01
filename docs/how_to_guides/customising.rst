Customising the OpenAPI schema
==============================

The generation of the OpenAPI schema by Quart-Schema can be customised
by changing the :attr:`QuartSchema.openapi_provider_class`. For
example to only include routes within a specific blueprint named
``bp``,

.. code-block:: python

    from quart_schema import OpenAPIProvider, QuartSchema

    class BlueprintOnlyOpenAPIProvider(OpenAPIProvider):
        def __init__(self, blueprint_name: str, app: Quart, extension: QuartSchema) -> None:
            super().__init__(app, extension)
            self._blueprint_prefix = f"{blueprint_name}."

        def generate_rules(self) -> Iterable[Rule]:
            for rule in self._app.url_map.iter_rules():
                hidden = getattr(
                    self._app.view_functions[rule.endpoint], QUART_SCHEMA_HIDDEN_ATTRIBUTE, False
                )
                if rule.endpoint.beginswith(self._blueprint_prefix) and not hidden and not rule.websocket:
                    yield rule

    quart_schema = QuartSchema(app, openapi_provider_class=CustomerOpenAPIProvider)


It is also possible to alter how the operation ID is generated,

.. code-block:: python

    from quart_schema import OpenAPIProvider, QuartSchema

    class CustomOperationIdOpenAPIProvider(OpenAPIProvider):
        def operation_id(self, method: str, func: Callable) -> Optional[str]:
            return func.__name__

    quart_schema = QuartSchema(app, openapi_provider_class=CustomerOpenAPIProvider)

There are many more aspects that can be customised, see the
:class:`OpenAPIProvider` for options.

Custom routes
-------------

It is also possible to combine the above into a custom route,

.. code-block:: python

    @blueprint.get("/custom.json")
    async def custom_openapi():
        schema = BlueprintOnlyOpenAPIProvider(blueprint.name, current_app, quart_schema).schema()
        return current_app.json.response(schema)

Please note this assumes the blueprint is not nested as the name will
be prefixed with the parents blueprint's names.
