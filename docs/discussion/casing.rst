Why aren't Pydanitc aliases used for casing conversion?
=======================================================

Pydantic supports field aliases, and alias converters, that are more
commonly used to provide support for camelCased JSON keys mapped to
snake_case variable names. This however requires each Pydantic model
to be specified with a special config subclass and it isn't clear that
dataclass to dictionary conversion supports aliasing. It is for these
reasons that I decided against recommending this feature in
Quart-Schema, although it can be used if you want.
