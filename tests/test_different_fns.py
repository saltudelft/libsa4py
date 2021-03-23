from libsa4py.cst_extractor import Extractor
from tests.constans import FN_DICT_REPR
import unittest


class TestExtractor(unittest.TestCase):
    """
    It tests extracted attributes and type hints from a Python source code file.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setUp(self):
        self.processed_f = Extractor().extract(open('./examples/different_fns.py', 'r').read())

    def test_typical_fn(self):
        fn_expected = FN_DICT_REPR.copy()
        fn_expected['name'] = 'add'
        fn_expected['params'] = {'x': 'int', 'y': 'int'}
        fn_expected['ret_exprs'] = ['return x + y']
        fn_expected['params_occur'] = {'x': [['x', 'y']], 'y': [['x', 'y']]}
        fn_expected['ret_type'] = 'int'
        fn_expected['params_descr'] = {'x': '', 'y': ''}

        self.assertDictEqual(fn_expected, self.processed_f['funcs'][0])

    def test_noargs_fn(self):
        fn_expected = FN_DICT_REPR.copy()
        fn_expected['name'] = 'noargs'
        fn_expected['ret_exprs'] = ['return 5']
        fn_expected['ret_type'] = 'int'

        self.assertDictEqual(fn_expected, self.processed_f['funcs'][1])

    def test_noparams_fn(self):
        fn_expected = FN_DICT_REPR.copy()
        fn_expected['name'] = 'no_params'
        fn_expected['ret_exprs'] = ['return 0']

        self.assertDictEqual(fn_expected, self.processed_f['funcs'][2])

    def test_noreturn(self):
        fn_expected = FN_DICT_REPR.copy()
        fn_expected['name'] = 'noreturn'
        fn_expected['params'] = {'x': 'int'}
        fn_expected['params_occur'] = {'x': [['print', 'x']]}
        fn_expected['params_descr'] = {'x': ''}

        self.assertDictEqual(fn_expected, self.processed_f['funcs'][3])

    def test_return_none(self):
        print(self.processed_f['funcs'][4])

        fn_expected = FN_DICT_REPR.copy()
        fn_expected['name'] = 'return_none'
        fn_expected['params'] = {'x': 'int'}
        fn_expected['params_occur'] = {'x': [['print', 'x']]}
        fn_expected['ret_type'] = 'None'
        fn_expected['params_descr'] = {'x': ''}

        self.assertDictEqual(fn_expected, self.processed_f['funcs'][4])

    def test_return_optional(self):
        fn_expected = FN_DICT_REPR.copy()
        fn_expected['name'] = 'return_optional'
        fn_expected['params'] = {'y': 'list'}
        fn_expected['ret_exprs'] = ['return None', 'return y']
        fn_expected['params_occur'] = {'y': [['len', 'y']]}
        fn_expected['ret_type'] = 'Optional[int]'
        fn_expected['params_descr'] = {'y': ''}

        self.assertDictEqual(fn_expected, self.processed_f['funcs'][5])

    def test_untyped_args(self):
        fn_expected = FN_DICT_REPR.copy()
        fn_expected['name'] = 'untyped_args'
        fn_expected['params'] = {'x': '', 'y': ''}
        fn_expected['ret_exprs'] = ['return x + y']
        fn_expected['params_occur'] = {'x': [['x', 'y']], 'y': [['x', 'y']]}
        fn_expected['ret_type'] = 'int'
        fn_expected['params_descr'] = {'x': '', 'y': ''}

        self.assertDictEqual(fn_expected, self.processed_f['funcs'][6])

    def test_inner(self):
        fn_expected = FN_DICT_REPR.copy()
        fn_expected['name'] = 'inner'
        fn_expected['params'] = {'x': 'int'}
        fn_expected['ret_exprs'] = ['return 12 + x']
        fn_expected['params_occur'] = {'x': []}
        fn_expected['ret_type'] = 'int'
        fn_expected['params_descr'] = {'x': ''}
        fn_expected['docstring'] = {'func': 'This is the inner function', 'ret': None, 'long_descr': None}

        self.assertDictEqual(fn_expected, self.processed_f['funcs'][7])

    def test_with_inner(self):
        fn_expected = FN_DICT_REPR.copy()
        fn_expected['name'] = 'with_inner'
        fn_expected['ret_exprs'] = ['return inner(10)']

        self.assertDictEqual(fn_expected, self.processed_f['funcs'][8])

    def test_varargs(self):
        fn_expected = FN_DICT_REPR.copy()
        fn_expected['name'] = 'varargs'
        fn_expected['params'] = {'xs': 'int'}
        fn_expected['ret_exprs'] = ['return sum']
        fn_expected['params_occur'] = {'xs': []}
        fn_expected['ret_type'] = 'int'
        fn_expected['variables'] = {'sum': 'int'}
        fn_expected['fn_var_occur'] = {'sum': [['sum', 'int'], ['sum', 'x']]}
        fn_expected['params_descr'] = {'xs': ''}

        self.assertDictEqual(fn_expected, self.processed_f['funcs'][9])

    def test_untyped_varargs(self):
        fn_expected = FN_DICT_REPR.copy()
        fn_expected['name'] = 'untyped_varargs'
        fn_expected['params'] = {'xs': ''}
        fn_expected['ret_exprs'] = ['return sum']
        fn_expected['params_occur'] = {'xs': []}
        fn_expected['ret_type'] = 'int'
        fn_expected['variables'] = {'sum': 'int'}
        fn_expected['fn_var_occur'] = {'sum': [['sum', 'int'], ['sum', 'x']]}
        fn_expected['params_descr'] = {'xs': ''}

        self.assertDictEqual(fn_expected, self.processed_f['funcs'][10])

    def test_kwarg_method(self):
        fn_expected = FN_DICT_REPR.copy()
        fn_expected['name'] = 'kwarg_method'
        fn_expected['params'] = {'a': 'int', 'b': 'int', 'c': 'float'}
        fn_expected['ret_exprs'] = ['return c']
        fn_expected['params_descr'] = {'a': '', 'b': '', 'c': ''}
        fn_expected['params_occur'] = {'a': [], 'b': [], 'c': []}

        self.assertDictEqual(fn_expected, self.processed_f['funcs'][11])

    def test_async_fn(self):
        fn_expected = FN_DICT_REPR.copy()
        fn_expected['name'] = 'async_fn'
        fn_expected['params'] = {'y': 'int'}
        fn_expected['ret_exprs'] = ['return await y']
        fn_expected['params_occur'] = {'y': []}
        fn_expected['ret_type'] = 'int'
        fn_expected['params_descr'] = {'y': ''}

        self.assertDictEqual(fn_expected, self.processed_f['funcs'][12])

    def test_abstract_fn(self):
        fn_expected = FN_DICT_REPR.copy()
        fn_expected['name'] = 'abstract_fn'
        fn_expected['params'] = {'name': 'str'}
        fn_expected['params_descr'] = {'name': ''}
        fn_expected['params_occur'] = {'name': []}
        fn_expected['ret_type'] = 'str'

        self.assertDictEqual(fn_expected, self.processed_f['funcs'][13])
