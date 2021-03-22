"""
This example file contains different kinds of functions for testing the cst_extractor module
"""


# A function witn both typed args and return type
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
    """This function has args as well as varargs"""
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
