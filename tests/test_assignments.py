from libsa4py.cst_extractor import Extractor
from tests.constans import FN_DICT_REPR
import unittest


class TestAssignments(unittest.TestCase):
    """
    It tests various kinds of assignments.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls.processed_f = Extractor().extract(open('./examples/assignments.py', 'r').read()).to_dict()

    def test_module_vars(self):
        module_vars_expected = {'PI': '', 'M_FOO': '', 'M_BAR': '', 'CONSTANT': 'builtins.int', 'LONG_STRING': ''}
        self.assertDictEqual(module_vars_expected, self.processed_f['variables'])

    def test_class_vars(self):
        cls_vars_expected = {'x': '', 'u': '', 'f': '', 'out_y': 'builtins.str', 'scientific_num': ''}
        self.assertDictEqual(cls_vars_expected, self.processed_f['classes'][0]['variables'])

    def test_self_vars(self):
        # TODO: implement the extraction of self vars in a multiple assignments
        self_vars_expected = {'x': 'builtins.int', 'y': '', 'b': '', 'c': '', 'error': 'typing.List'}
        self.assertDictEqual(self_vars_expected, self.processed_f['classes'][0]['funcs'][0]['variables'])

    def test_local_vars(self):
        local_vars_expected = {'f_no': 'builtins.float', 'l': 'typing.List[builtins.str]', 'foo': 'builtins.str'}
        self.assertDictEqual(local_vars_expected, self.processed_f['classes'][0]['funcs'][1]['variables'])

    def test_tuple_assign(self):
        tuple_assigns_expected = {'x': '', 'y': '', 'z': '', 'a': '', 'b': '', 'c': '', 'd': '', 'e': '', 'f': '',
                                  'g': '', 'h': ''}
        print(self.processed_f['classes'][0]['funcs'][2]['variables'])
        self.assertDictEqual(tuple_assigns_expected, self.processed_f['classes'][0]['funcs'][2]['variables'])

    def test_walrus_op(self):
        pass  # TODO: run the test conditionally based on the Python version
