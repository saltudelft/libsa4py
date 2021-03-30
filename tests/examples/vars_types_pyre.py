"""
This example is for testing the Extractor with the Pyre's inferred types
"""

PI = 3.14
no: int = 404
CONSTANT = "This is a constant var."
X, Y = 1, 2

class Foo:
    foo_num = 128
    foo_name = "Foo"

    def __init__(self, y='default'):
        self.x = [1, 2, 3]
        self.y = y

    def local_vars(self):
        x = ('Hello', 'World')
        f, g = 2.16, 200
        res = PI + f



