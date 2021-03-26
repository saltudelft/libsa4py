"""
An example for the removal of type annotations from a source code file.
"""

CONSTANT = 200
MOD = ...

def foo(x, l):
    return l[x]

class Bar:
    class_var = "This is Bar"
    def __init__(self, x):
        self.x = x
        self.n = ...
