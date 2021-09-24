"""
An example for testing type propagation throughout the file
"""

$int$: int = 10
$typing.Any$ = 400 + $int$

def $int$($int$: int, $typing.Any$) -> int:
    $int$: int = $int$ + 12 + $typing.Any$  # arg. x usage
    return $int$ + $int$  # local var. y + module CONSTANT

class Bar:
    $float$: float = 2.13  # class var. me
    $typing.Any$ = 12 + $float$ + $int$   # class var. me + module CONSTANT
    def $None$(self):
        self.$float$: float = 10.5 + Bar.$float$  # local var. c + Class var. me
        self.$typing.Any$ = self.$float$ + $int$  # local var. c + module CONSTANT
    def $float$(self, $float$: float) -> float:
        return self.$typing.Any$ + $float$ + 3.14