Why is QuartSchema a Class not a function?
==========================================

The ``QuartSchema`` object is a class rather than a function, despite
having no state. To me this is an odd choice as it would be better as
a function. It is also something I've avoided doing elsewhere e.g. for
Quart-CORS.

``QuartSchema`` alters the Quart app instance passed to it by changing
the Websocket class type, the json encoder, and more. This is
something that I worry could surprise users. Therefore I've followed
the Flask extension standard by making it a class with an ``init_app``
method. My hope is that this better communicates to users that
QuartSchema makes alterations, as is common in Flask extensions.
