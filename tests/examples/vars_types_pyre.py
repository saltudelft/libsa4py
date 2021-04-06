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
    foo_x, foo_y = 256, [10, 9, 8]

    def __init__(self, t='default'):
        self.x = [1, 2, 3]
        self.y = t
        self.l, self.k = (45, 35), 'OOooOO'

    def local_vars(self):
        x = ('Hello', 'World')
        f, g = 2.16, 200
        res = PI + f



