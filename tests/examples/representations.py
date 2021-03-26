"""
This file is an example for testing representation of modules, classes, and functions
"""

from os import path
import math

# Module-level constant
CONSTANT = "Hello Python!"


class MyClass:
    """
    My Class docstring
    """
    cls_var: int = 10  # A class variable

    def __init__(self, y: float) -> None:
        self.y = y

    def cls_fn(self, c: int) -> float:
        n = c + 14
        return MyClass.cls_var + c / (2 + n)


class Bar:
    def __init__(self):
        pass


def my_fn(x: int) -> int:
    return x + 10


def foo() -> None:
    """
    Foo docstring
    """
    print("Foo")
