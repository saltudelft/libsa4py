"""
In this file example, different kinds of assignments are defined for testing.
"""

from typing import List

# Module-level constants
PI = 3.14
CONSTANT: int = 404
M_FOO, M_BAR = 2.16, 13

LONG_STRING = """Vestibulum dignissim nisi in ex vehicula viverra at et augue. Phasellus volutpat euismod gravida.
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Quisque volutpat sapien sed odio eleifend elementum."""


class Test:
    # Class variables
    x = 12
    u, f = 14, 'tests'
    out_y: str = 'Hello'
    scientific_num = 1.3e+4

    def __init__(self, x: int) -> None:
        self.x: int = x
        self.y = "Test"
        self.b, self.c = 45, 'blah'
        self.error: List

    def local_var_assings(self):
        f_no: float = 3.14
        l: List[str] = ['hi', 'world']
        foo: str

    def tuple_assigns(self):
        x, y, z = 12, 0.5, 34
        a, (b, c) = 1, (2, 3)
        d, ((e, f), (g, h)) = 4, ((5, 6), (6, 7))

    # Needs Python 3.8+ for parsing
    # def walrus_op(self):
    #     while (n := 4):
    #         print(n)