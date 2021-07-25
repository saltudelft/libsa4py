"""
An example for counting type annotations
"""
# 1
m: int = 10

class Bar:
    bar_var1: float = 2.17 # 2
    bar_var2: int # 3
    def __init__(self, i: int): # 4
        self.i: int = i # 5
    # 6, 7
    def bar_fn(self, x: float, y: float) -> float: # 8
        return x + y
# 9, 10
def foo(n: str, i:bool=False):
    if i:
        z: str = "Hello" + n # 11