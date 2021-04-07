from typing import Dict as _Dict
from typing import Tuple
import typing as t
from collections.abc import Sequence
import numpy as np
import builtins

d: _Dict = {}
l: t.List[str] = []

class Foo:
    foo_seq: Sequence = []
    def __init__(self, x: t.Tuple, y: t.Pattern):
        self.x: Tuple = x
        n: np.int = np.int(12)

    def bar(self) -> np.array:
        return np.array([1, 2, 3])
