from typing import Dict as _Dict
from typing import Tuple, Union
from libsa4py.cst_transformers import TypeQualifierResolver
from .representations import Bar
from ..test_imports import TestImports
import typing as t
import typing
from collections.abc import Sequence
from builtins import str
import numpy as np
import builtins

d: _Dict = {}
l: t.List[str] = []
q_v: typing.List[builtins.int] = [10]
l_n: t.List[Tuple[int, int]]
t_e: t.Tuple[typing.Any, ...] = ()
u_d: Union[t.List[Tuple[str, int]], t.Tuple[t.Any], t.Tuple[t.List[t.Tuple[t.Set[int]]]]] = None
c: t.Callable[..., t.List] = None
c_h: t.Callable[[t.List, t.Dict], int] = None
t_a: t.Type[t.List] = t.List
tqr: TypeQualifierResolver = TypeQualifierResolver()
lt: t.Literal["123"] = "123"
s: [] = [1, 2]
N: Union[t.List, None] = []
rl: Bar = Bar()
b: True = True
relative_i: TestImports = TestImports()

class Foo:
    foo_seq: Sequence = []
    def __init__(self, x: t.Tuple, y: t.Pattern=None):
        class Delta:
            pass
        self.x: Tuple = x
        n: np.int = np.int(12)
        d: Delta = Delta()

    def bar(self) -> np.array:
        return np.array([1, 2, 3])

    def shadow_qn(self):
        sq: str = 'Shadow qualified name'

        for str in sq:
            print(str)

u: "Foo" = Foo(t_e)
foo: Foo = Foo(t_e)
foo_t: Tuple[Foo, TypeQualifierResolver] = (Foo(t_e), TypeQualifierResolver())
