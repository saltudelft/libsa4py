from libsa4py.utils import mk_dir_not_exist, write_file, read_file, save_json
from libsa4py.cst_pipeline import TypeAnnotatingProjects
import unittest
import shutil

test_file = """from pathlib import Path
x = 12
l = [(1, 2)]
class Foo:
    foo_v = 'Hello, Foo!'
    class Delta:
        foo_d = 'Hello, Delta!'
    foo_p = Path('/home/foo/bar')
    def __init__():
        def foo_inner(c, d):
            pass
    def foo_fn(self, y):
        def foo_inner(a, b, c, d):
            pass
        d = {"foo": True}
        return d
def Bar(x=['apple', 'orange']):
    v = x
    l = lambda e: e+1
    return v
"""

test_file_exp = """from pathlib import Path
x: int = 12
l: typing.List[typing.Tuple[int, int]] = [(1, 2)]
class Foo:
    foo_v: str = 'Hello, Foo!'
    class Delta:
        foo_d = 'Hello, Delta!'
    foo_p: pathlib.Path = Path('/home/foo/bar')
    def __init__():
        def foo_inner(c, d):
            pass
    def foo_fn(self, y)-> typing.Dict[str, bool]:
        def foo_inner(a, b, c, d):
            pass
        d: typing.Dict[str, bool] = {"foo": True}
        return d
def Bar(x: typing.List[str]=['apple', 'orange'])-> typing.List[str]:
    v: typing.List[str] = x
    l = lambda e: e+1
    return v
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
        from libsa4py.cst_extractor import Extractor
        save_json('./tmp_ta/type_apply.json', Extractor.extract(read_file('./tmp_ta/type_apply.py')).to_dict())

    def test_type_apply_pipeline(self):
        ta = TypeAnnotatingProjects('./tmp_ta', None)
        ta.process_project('./examples/type_apply_ex.json')

        self.assertEqual(test_file_exp, read_file('./tmp_ta/type_apply.py'))

    # @classmethod
    # def tearDownClass(cls):
    #     shutil.rmtree("./tmp_ta/")
