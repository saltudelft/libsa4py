"""
This file is an example for testing representation of modules, classes, and functions
"""

from os import path
import math

CONSTANT = "Hello Python!"


class MyClass:
    cls_var: int = 10

    def __init__(self, y: float) -> None:
        self.y = y

    def cls_fn(self, c: int) -> float:
        n = c + 14
        return MyClass.cls_var + c / (2 + n)


def my_fn(x: int) -> int:
    return x + 10
