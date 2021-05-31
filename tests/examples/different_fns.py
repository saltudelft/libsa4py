"""
This example file contains different kinds of functions for testing the cst_extractor module
"""

from typing import Optional


# A function with both typed args and return type
def add(x: int, y: int) -> int:
    return x + y


# This function has no input arguments
def noargs() -> int:
    return 5


# A function with no parameters
def no_params():
    return 0


# This function has no return
def noreturn(x: int):
    print(x)


# This function returns None
def return_none(x: int) -> None:
    print(x)


# This functions returns Optional
def return_optional(y: list) -> Optional[int]:
    if len(y) == 0:
        return None
    return y


# This function has untyped input arguments
def untyped_args(x, y) -> int:
    return x + y


# This function has an inner function
def with_inner():
    def inner(x: int) -> int:
        """This is the inner function"""
        return 12 + x
    return inner(10)


# This function has varargs
def varargs(*xs: int) -> int:
    sum: int = 0
    for x in xs:
        sum += x
    return sum


# This function has untype varargs
def untyped_varargs(*xs) -> int:
    sum: int = 0
    for x in xs:
        sum += x
    return sum


# A function with keyword args
def kwarg_method(a: int, *b: int, **c: float):
    return c


# An async function
async def async_fn(y: int) -> int:
    return await y


# An abstract function with typed args
def abstract_fn(name: str) -> str: ...


# For extracting line and column no. of a function
def fn_lineno(x):
    print(x)