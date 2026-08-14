from itertools import zip_longest
from typing import Any, Callable


def snake_to_camel(snake: Any) -> Any:
    if isinstance(snake, str):
        return _snake_to_camel(snake)
    elif isinstance(snake, (dict, list, tuple)):
        return _convert_keys(snake, _snake_to_camel)
    else:
        return snake


def _snake_to_camel(snake: str) -> str:
    head, *tail = snake.split("_")
    return head + "".join(part.capitalize() for part in tail)


def camel_to_snake(camel: Any) -> Any:
    if isinstance(camel, str):
        return _camel_to_snake(camel)
    elif isinstance(camel, (dict, list, tuple)):
        return _convert_keys(camel, _camel_to_snake)
    else:
        return camel


def _camel_to_snake(camel: str) -> str:
    if camel == "":
        return ""

    result = [camel[0]]
    for lchar, char, rchar in zip_longest(camel, camel[1:], camel[2:], fillvalue=""):
        if char.isupper() and (
            lchar.islower() or lchar.isnumeric() or rchar.islower() or rchar.isnumeric()
        ):
            result.append("_")
        result.append(char)
    return "".join(result).lower()


def snake_to_kebab(snake: Any) -> Any:
    if isinstance(snake, str):
        return _snake_to_kebab(snake)
    elif isinstance(snake, (dict, list, tuple)):
        return _convert_keys(snake, _snake_to_kebab)
    else:
        return snake


def _snake_to_kebab(snake: str) -> str:
    return snake.replace("_", "-")


def kebab_to_snake(kebab: Any) -> Any:
    if isinstance(kebab, str):
        return _kebab_to_snake(kebab)
    elif isinstance(kebab, (dict, list, tuple)):
        return _convert_keys(kebab, _kebab_to_snake)
    else:
        return kebab


def _kebab_to_snake(kebab: str) -> str:
    return kebab.replace("-", "_")


def _convert_keys(values: Any, convert: Callable[[str], str]) -> Any:
    if isinstance(values, dict):
        return {convert(key): _convert_keys(value, convert) for key, value in values.items()}
    elif isinstance(values, list):
        return [_convert_keys(elem, convert) for elem in values]
    elif isinstance(values, tuple):
        return tuple(_convert_keys(elem, convert) for elem in values)
    else:
        return values
