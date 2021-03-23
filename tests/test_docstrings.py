from libsa4py.cst_extractor import Extractor
from tests.constans import FN_DICT_REPR
import unittest


class TestDocstrings(unittest.TestCase):
    """
    It tests docstrings extracted from functions.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls.processed_f = Extractor().extract(open('./examples/docstrings.py', 'r').read())

    def test_basic_docstring(self):
        fn_expected = FN_DICT_REPR.copy()
        fn_expected['name'] = 'basic_docstring'
        fn_expected['docstring']['func'] = 'This is a basic docstring'

        self.assertDictEqual(fn_expected, self.processed_f['funcs'][0])

    def test_google_docstring(self):
        fn_expected = FN_DICT_REPR.copy()
        fn_expected['name'] = 'google_docstring'
        fn_expected['params'] = {'param1': '', 'param2': ''}
        fn_expected['ret_exprs'] = ['return True', 'return False']
        fn_expected['params_occur'] = {'param1': [['len', 'param2', 'param1']], 'param2': [['len', 'param2', 'param1']]}
        fn_expected['params_descr'] = {'param1': 'The first parameter.', 'param2': 'The second parameter.'}
        fn_expected['docstring'] = {'func': 'Summary line.', 'ret': 'Description of return value',
                                    'long_descr': 'Extended description of function.'}

        self.assertDictEqual(fn_expected, self.processed_f['funcs'][1])

    def test_docstring(self):
        fn_expected = FN_DICT_REPR.copy()
        fn_expected['name'] = 'rest_docstring'
        fn_expected['params'] = {'param1': '', 'param2': ''}
        fn_expected['ret_exprs'] = ['return True', 'return False']
        fn_expected['params_occur'] = {'param1': [['len', 'param2', 'param1']], 'param2': [['len', 'param2', 'param1']]}
        fn_expected['params_descr'] = {'param1': 'The first parameter.', 'param2': 'The second parameter.'}
        fn_expected['docstring'] = {'func': 'Summary line.', 'ret': 'Description of return value',
                                    'long_descr': 'Description of function.'}

        self.assertDictEqual(fn_expected, self.processed_f['funcs'][2])

    def test_numpy_docstring(self):
        fn_expected = FN_DICT_REPR.copy()
        fn_expected['name'] = 'numpy_docstring'
        fn_expected['params'] = {'param1': '', 'param2': ''}
        fn_expected['ret_exprs'] = ['return True', 'return False']
        fn_expected['params_occur'] = {'param1': [['len', 'param2', 'param1']], 'param2': [['len', 'param2', 'param1']]}
        fn_expected['ret_exprs'] = ['return True', 'return False']
        fn_expected['params_descr'] = {'param1': 'The first parameter.', 'param2': 'The second parameter.'}
        fn_expected['docstring'] = {'func': 'Summary line.', 'ret': 'Description of return value',
                                    'long_descr': 'Extended description of function.'}

        self.assertDictEqual(fn_expected, self.processed_f['funcs'][3])

    def test_no_docstring(self):
        fn_expected = FN_DICT_REPR.copy()
        fn_expected['name'] = 'no_docstring'
        fn_expected['ret_exprs'] = ['return None']
        fn_expected['docstring'] = {'func': None, 'ret': None, 'long_descr': None}
