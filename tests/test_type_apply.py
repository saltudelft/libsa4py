from libsa4py.utils import mk_dir_not_exist, write_file, read_file
from libsa4py.cst_pipeline import TypeAnnotatingProjects
import unittest
import shutil

test_file = """from pathlib import Path
x = 12
l = [(1, 2)]
class Foo:
    foo_v = 'Hello, Foo!'
    foo_p = Path('/home/foo/bar')

    def foo_fn(self):
        d = {"foo": True}
def Bar(x=['apple', 'orange']):
    v = x
"""

test_file_exp = """from pathlib import Path
x: int = 12
l: typing.List[typing.Tuple[int, int]] = [(1, 2)]
class Foo:
    foo_v: str = 'Hello, Foo!'
    foo_p: pathlib.Path = Path('/home/foo/bar')

    def foo_fn(self):
        d: typing.Dict[str, bool] = {"foo": True}
def Bar(x=['apple', 'orange']):
    v: typing.List[str] = x
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

    def test_type_apply_pipeline(self):
        ta = TypeAnnotatingProjects('./tmp_ta', None)
        ta.process_project('./examples/type_apply_ex.json')

        self.assertEqual(test_file_exp, read_file('./tmp_ta/type_apply.py'))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree("./tmp_ta/")
