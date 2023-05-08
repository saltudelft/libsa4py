from libsa4py.utils import mk_dir_not_exist, write_file, read_file, save_json
from libsa4py.cst_pipeline import TypeAnnotatingProjects
from libsa4py.cst_extractor import Extractor
from libsa4py.cst_transformers import TypeAnnotationRemover, TypeApplier
from collections import Counter
import unittest
import shutil
import libcst

test_file = """from pathlib import Path
x: int = 12
l = [(1, 2)]
c = defaultdict(int)
df = pd.DataFrame([2, 3])
dff = pd.DataFrame([1,2])
lit = "Hello!"
class Foo:
    foo_v: str = 'Hello, Foo!'
    class Delta:
        foo_d = 'Hello, Delta!'
    foo_p = Path('/home/foo/bar')
    def __init__():
        def foo_inner(c, d=lambda a,b: a == b):
            pass
    def foo_fn(self, y):
        def foo_inner(a, b, c, d, *args, **kwargs):
            pass
        d: dict = {"foo": True}
        return d
    @event.getter
    def get_e(self):
        return Foo.foo_v
    @event.setter
    def get_e(self, y):
        Foo.foo_v = y
        return Foo.foo_v
    foo_v = "No"
def Bar(x=['apple', 'orange'], *, c):
    v = x
    l = lambda e: e+1
    return v
"""

test_file_exp = """from typing import Tuple, Dict, List, Literal
from collections import defaultdict
import pandas
import pathlib
import builtins
import collections
import typing
from pathlib import Path
x: builtins.int = 12
l: typing.List[typing.Tuple[builtins.int, builtins.int]] = [(1, 2)]
c: collections.defaultdict = defaultdict(int)
df: pandas.DataFrame = pd.DataFrame([2, 3])
dff: typing.List[pandas.arrays.PandasArray] = pd.DataFrame([1,2])
lit: typing.Literal = "Hello!"
class Foo:
    foo_v: str = 'Hello, Foo!'
    class Delta:
        foo_d = 'Hello, Delta!'
    foo_p: pathlib.Path = Path('/home/foo/bar')
    def __init__():
        def foo_inner(c: str, d=lambda a,b: a == b):
            pass
    def foo_fn(self, y)-> typing.Dict[builtins.str, builtins.bool]:
        def foo_inner(a, b, c, d, *args, **kwargs):
            pass
        d: typing.Dict[builtins.str, builtins.bool] = {"foo": True}
        return d
    @event.getter
    def get_e(self):
        return Foo.foo_v
    @event.setter
    def get_e(self, y: builtins.str):
        Foo.foo_v = y
        return Foo.foo_v
    foo_v = "No"
def Bar(x: typing.List[builtins.str]=['apple', 'orange'], *, c)-> typing.List[builtins.str]:
    v: typing.List[builtins.str] = x
    l = lambda e: e+1
    return v
"""

test_local_vars = """
def f():
    x: builtin.int = 10

def g():
    x: builtin.str = "Hello World"
"""


class TestTypeAnnotatingProjects(unittest.TestCase):
    """
    It tests applying inferred type annotations to projects.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        mk_dir_not_exist('./tmp_ta')
        write_file('./tmp_ta/type_apply.py', test_file)
        # from libsa4py.cst_extractor import Extractor
        # save_json('./tmp_ta/type_apply_ex.json', Extractor.extract(read_file('./tmp_ta/type_apply.py')).to_dict())

    def test_type_apply_pipeline(self):
        ta = TypeAnnotatingProjects('./tmp_ta', None, apply_nlp=False)
        ta.process_project('./examples/type_apply_ex.json')

        exp_split = test_file_exp.splitlines()
        out_split = read_file('./tmp_ta/type_apply.py').splitlines()

        exp = """{}""".format("\n".join(exp_split[7:]))
        out = """{}""".format("\n".join(out_split[7:]))

        self.assertEqual(exp, out)
        # The imported types from typing
        self.assertEqual(Counter(" ".join(exp_split[0:7])), Counter(" ".join(out_split[0:7])))

    def test_type_apply_local_vars(self):
        """
        This tests whether type annotations for local variables with the same names are applied correctly.
        """
        mod = libcst.parse_module(test_local_vars)
        annot_org = Extractor.extract(mod.code).to_dict()

        annot_less = mod.visit(TypeAnnotationRemover())
        annot_new = libcst.metadata.MetadataWrapper(annot_less,
                                                    unsafe_skip_copy=True).visit(TypeApplier(annot_org,
                                                                                             apply_nlp=False))
        exp_split = mod.code.splitlines()
        out_split = annot_new.code.splitlines()

        exp = """{}""".format("\n".join(exp_split[1:]))
        out = """{}""".format("\n".join(out_split[2:]))
        self.assertEqual(exp, out)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree("./tmp_ta/")
