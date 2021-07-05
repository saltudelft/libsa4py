from libsa4py.cst_extractor import Extractor
from tests.constans import FN_DICT_REPR
import unittest


class TestDifferentFns(unittest.TestCase):
    """
    It tests extracted attributes and type hints from Python functions.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls.processed_f = Extractor().extract(open('./examples/different_fns.py', 'r').read()).to_dict()

    def test_typical_fn(self):
        fn_expected = FN_DICT_REPR.copy()
        fn_expected['name'] = 'add'
        fn_expected['q_name'] = 'add'
        fn_expected['fn_lc'] = ((9, 0), (10, 16))
        fn_expected['params'] = {'x': 'builtins.int', 'y': 'builtins.int'}
        fn_expected['ret_exprs'] = ['return x + y']
        fn_expected['params_occur'] = {'x': [['x', 'y']], 'y': [['x', 'y']]}
        fn_expected['ret_type'] = 'builtins.int'
        fn_expected['params_descr'] = {'x': '', 'y': ''}

        self.assertDictEqual(fn_expected, self.processed_f['funcs'][0])

    def test_noargs_fn(self):
        fn_expected = FN_DICT_REPR.copy()
        fn_expected['name'] = 'noargs'
        fn_expected['q_name'] = 'noargs'
        fn_expected['fn_lc'] = ((14, 0), (15, 12))
        fn_expected['ret_exprs'] = ['return 5']
        fn_expected['ret_type'] = 'builtins.int'

        self.assertDictEqual(fn_expected, self.processed_f['funcs'][1])

    def test_noparams_fn(self):
        fn_expected = FN_DICT_REPR.copy()
        fn_expected['name'] = 'no_params'
        fn_expected['q_name'] = 'no_params'
        fn_expected['fn_lc'] = ((19, 0), (20, 12))
        fn_expected['ret_exprs'] = ['return 0']

        self.assertDictEqual(fn_expected, self.processed_f['funcs'][2])

    def test_noreturn(self):
        fn_expected = FN_DICT_REPR.copy()
        fn_expected['name'] = 'noreturn'
        fn_expected['q_name'] = 'noreturn'
        fn_expected['fn_lc'] = ((24, 0), (25, 12))
        fn_expected['params'] = {'x': 'builtins.int'}
        fn_expected['params_occur'] = {'x': [['print', 'x']]}
        fn_expected['params_descr'] = {'x': ''}

        self.assertDictEqual(fn_expected, self.processed_f['funcs'][3])

    def test_return_none(self):
        fn_expected = FN_DICT_REPR.copy()
        fn_expected['name'] = 'return_none'
        fn_expected['q_name'] = 'return_none'
        fn_expected['fn_lc'] = ((29, 0), (30, 12))
        fn_expected['params'] = {'x': 'builtins.int'}
        fn_expected['params_occur'] = {'x': [['print', 'x']]}
        fn_expected['ret_type'] = 'None'
        fn_expected['params_descr'] = {'x': ''}

        self.assertDictEqual(fn_expected, self.processed_f['funcs'][4])

    def test_return_optional(self):
        fn_expected = FN_DICT_REPR.copy()
        fn_expected['name'] = 'return_optional'
        fn_expected['q_name'] = 'return_optional'
        fn_expected['fn_lc'] = ((34, 0), (37, 12))
        fn_expected['params'] = {'y': 'builtins.list'}
        fn_expected['ret_exprs'] = ['return None', 'return y']
        fn_expected['params_occur'] = {'y': [['len', 'y']]}
        fn_expected['ret_type'] = 'typing.Optional[builtins.int]'
        fn_expected['params_descr'] = {'y': ''}

        self.assertDictEqual(fn_expected, self.processed_f['funcs'][5])

    def test_untyped_args(self):
        fn_expected = FN_DICT_REPR.copy()
        fn_expected['name'] = 'untyped_args'
        fn_expected['q_name'] = 'untyped_args'
        fn_expected['fn_lc'] = ((41, 0), (42, 16))
        fn_expected['params'] = {'x': '', 'y': ''}
        fn_expected['ret_exprs'] = ['return x + y']
        fn_expected['params_occur'] = {'x': [['x', 'y']], 'y': [['x', 'y']]}
        fn_expected['ret_type'] = 'builtins.int'
        fn_expected['params_descr'] = {'x': '', 'y': ''}

        self.assertDictEqual(fn_expected, self.processed_f['funcs'][6])

    def test_inner(self):
        fn_expected = FN_DICT_REPR.copy()
        fn_expected['name'] = 'inner'
        fn_expected['q_name'] = 'with_inner.<locals>.inner'
        fn_expected['fn_lc'] = ((47, 4), (49, 21))
        fn_expected['params'] = {'x': 'builtins.int'}
        fn_expected['ret_exprs'] = ['return 12 + x']
        fn_expected['params_occur'] = {'x': []}
        fn_expected['ret_type'] = 'builtins.int'
        fn_expected['params_descr'] = {'x': ''}
        fn_expected['docstring'] = {'func': 'This is the inner function', 'ret': None, 'long_descr': None}

        self.assertDictEqual(fn_expected, self.processed_f['funcs'][7])

    def test_with_inner(self):
        fn_expected = FN_DICT_REPR.copy()
        fn_expected['name'] = 'with_inner'
        fn_expected['q_name'] = 'with_inner'
        fn_expected['fn_lc'] = ((46, 0), (50, 20))
        fn_expected['ret_exprs'] = ['return inner(10)']

        self.assertDictEqual(fn_expected, self.processed_f['funcs'][8])

    def test_varargs(self):
        fn_expected = FN_DICT_REPR.copy()
        fn_expected['name'] = 'varargs'
        fn_expected['q_name'] = 'varargs'
        fn_expected['fn_lc'] = ((54, 0), (58, 14))
        fn_expected['params'] = {'xs': 'builtins.int'}
        fn_expected['ret_exprs'] = ['return sum']
        fn_expected['params_occur'] = {'xs': []}
        fn_expected['ret_type'] = 'builtins.int'
        fn_expected['variables'] = {'sum': 'builtins.int'}
        fn_expected['fn_var_occur'] = {'sum': [['sum', 'builtins', 'int'], ['sum', 'x']]}
        fn_expected['fn_var_ln'] = {'sum': ((55, 4), (55, 7))}
        fn_expected['params_descr'] = {'xs': ''}

        self.assertDictEqual(fn_expected, self.processed_f['funcs'][9])

    def test_untyped_varargs(self):
        fn_expected = FN_DICT_REPR.copy()
        fn_expected['name'] = 'untyped_varargs'
        fn_expected['q_name'] = 'untyped_varargs'
        fn_expected['fn_lc'] = ((62, 0), (66, 14))
        fn_expected['params'] = {'xs': ''}
        fn_expected['ret_exprs'] = ['return sum']
        fn_expected['params_occur'] = {'xs': []}
        fn_expected['ret_type'] = 'builtins.int'
        fn_expected['variables'] = {'sum': 'builtins.int'}
        fn_expected['fn_var_occur'] = {'sum': [['sum', 'builtins', 'int'], ['sum', 'x']]}
        fn_expected['fn_var_ln'] = {'sum': ((63, 4), (63, 7))}
        fn_expected['params_descr'] = {'xs': ''}

        self.assertDictEqual(fn_expected, self.processed_f['funcs'][10])

    def test_kwarg_method(self):
        fn_expected = FN_DICT_REPR.copy()
        fn_expected['name'] = 'kwarg_method'
        fn_expected['q_name'] = 'kwarg_method'
        fn_expected['fn_lc'] = ((70, 0), (71, 12))
        fn_expected['params'] = {'a': 'builtins.int', 'b': 'builtins.int', 'c': 'builtins.float'}
        fn_expected['ret_exprs'] = ['return c']
        fn_expected['params_descr'] = {'a': '', 'b': '', 'c': ''}
        fn_expected['params_occur'] = {'a': [], 'b': [], 'c': []}

        self.assertDictEqual(fn_expected, self.processed_f['funcs'][11])

    def test_async_fn(self):
        fn_expected = FN_DICT_REPR.copy()
        fn_expected['name'] = 'async_fn'
        fn_expected['q_name'] = 'async_fn'
        fn_expected['fn_lc'] = ((75, 0), (76, 18))
        fn_expected['params'] = {'y': 'builtins.int'}
        fn_expected['ret_exprs'] = ['return await y']
        fn_expected['params_occur'] = {'y': []}
        fn_expected['ret_type'] = 'builtins.int'
        fn_expected['params_descr'] = {'y': ''}

        self.assertDictEqual(fn_expected, self.processed_f['funcs'][12])

    def test_abstract_fn(self):
        fn_expected = FN_DICT_REPR.copy()
        fn_expected['name'] = 'abstract_fn'
        fn_expected['q_name'] = 'abstract_fn'
        fn_expected['fn_lc'] = ((80, 0), (80, 56))
        fn_expected['params'] = {'name': 'builtins.str'}
        fn_expected['params_descr'] = {'name': ''}
        fn_expected['params_occur'] = {'name': []}
        fn_expected['ret_type'] = 'builtins.str'

        self.assertDictEqual(fn_expected, self.processed_f['funcs'][13])

    def test_fn_lineno(self):
        fn_expected = FN_DICT_REPR.copy()
        fn_expected['name'] = 'fn_lineno'
        fn_expected['q_name'] = 'fn_lineno'
        fn_expected['fn_lc'] = ((84, 0), (85, 12))
        fn_expected['params'] = {'x': ''}
        fn_expected['params_descr'] = {'x': ''}
        fn_expected['params_occur'] = {'x': [['print', 'x']]}
        fn_expected['ret_type'] = ''

        self.assertDictEqual(fn_expected, self.processed_f['funcs'][14])
