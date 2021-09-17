"""
An example for testing type propagation throughout the file
"""

CONSTANT: int = 10
CONSTANT_USED = 400 + CONSTANT

def foo(x: int) -> int:
    y: int = x + 12  # arg. x usage
    return y + CONSTANT  # local var. y + module CONSTANT

class Bar:
    me: float = 2.13  # class var. me
    fox = 12 + me + CONSTANT   # class var. me + module CONSTANT
    def __init__(self):
        self.c: float = 10.5 + Bar.me  # local var. c + Class var. me
        self.b = self.c + CONSTANT  # local var. c + module CONSTANT
    def bar_method(self, x: float) -> float:
        return self.c + x + 3.14