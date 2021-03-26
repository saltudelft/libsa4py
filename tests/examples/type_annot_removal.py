"""
An example for the removal of type annotations from a source code file.
"""

CONSTANT: int = 200
MOD: dict

def foo(x:int, l: list) -> int:
    return l[x]

class Bar:
    class_var: str = "This is Bar"
    def __init__(self, x: float) -> None:
        self.x: float = x
        self.n: set
