"""
An example for testing type propagation throughout the file
"""

$int$: int = 10
CONSTANT_USED = 400 + $int$

def $int$($int$: int) -> int:
    $int$: int = $int$ + 12  # arg. x usage
    return $int$ + $int$  # local var. y + module CONSTANT

class Bar:
    $float$: float = 2.13  # class var. me
    fox = 12 + $float$ + $int$   # class var. me + module CONSTANT
    def __init__(self):
        self.$float$: float = 10.5 + Bar.$float$  # local var. c + Class var. me
        self.b = self.$float$ + $int$  # local var. c + module CONSTANT
    def $float$(self, $float$: float) -> float:
        return self.c + $float$ + 3.14