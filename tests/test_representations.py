from libsa4py.cst_extractor import Extractor
from libsa4py.representations import FunctionInfo, ClassInfo
import unittest

processed_f = Extractor().extract(open('./examples/representations.py', 'r').read())


class TestModuleRepresentations(unittest.TestCase):
    """
    It tests the Dict-based representation of modules
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def test_mod_repr_dict_keys(self):
        mod_repr_dict_key_exp = ['untyped_seq', 'typed_seq', 'imports', 'variables', 'mod_var_occur', 'classes', 'funcs',
                                 'set', 'type_annot_cove']
        self.assertListEqual(mod_repr_dict_key_exp, list(processed_f.keys()))

    def test_mod_repr_cls_dict(self):
        cls_repr_mod_exp = [{'name': 'MyClass', 'variables': {'cls_var': 'int'},
                             'cls_var_occur': {'cls_var': [['MyClass', 'cls_var', 'c', 'n']]},
                             'funcs': [{'name': '__init__', 'params': {'self': '', 'y': 'float'}, 'ret_exprs': [],
                                        'params_occur': {'self': [['self', 'y', 'y']], 'y': [['self', 'y', 'y']]},
                                        'ret_type': 'None', 'variables': {'y': ''},
                                        'fn_var_occur': {'y': [['self', 'y', 'y']]},
                                        'params_descr': {'self': '', 'y': ''},
                                        'docstring': {'func': None, 'ret': None, 'long_descr': None}},
                                       {'name': 'cls_fn', 'params': {'self': '', 'c': 'int'},
                                        'ret_exprs': ['return MyClass.cls_var + c / (2 + n)'],
                                        'params_occur': {'self': [], 'c': [['n', 'c'],
                                                                           ['MyClass', 'cls_var', 'c', 'n']]},
                                        'ret_type': 'float', 'variables': {'n': ''},
                                        'fn_var_occur': {'n': [['n', 'c'], ['MyClass', 'cls_var', 'c', 'n']]},
                                        'params_descr': {'self': '', 'c': ''},
                                        'docstring': {'func': None, 'ret': None, 'long_descr': None}}]},
                            {'name': 'Bar', 'variables': {}, 'cls_var_occur': {},
                             'funcs': [{'name': '__init__', 'params': {'self': ''}, 'ret_exprs': [],
                                        'params_occur': {'self': []}, 'ret_type': '', 'variables': {},
                                        'fn_var_occur': {}, 'params_descr': {'self': ''},
                                        'docstring': {'func': None, 'ret': None, 'long_descr': None}}]}]

        self.assertListEqual(cls_repr_mod_exp, processed_f['classes'])

    def test_mod_repr_fn_dict(self):
        fn_repr_mod_exp = [{'name': 'my_fn', 'params': {'x': 'int'}, 'ret_exprs': ['return x + 10'],
                            'params_occur': {'x': []}, 'ret_type': 'int', 'variables': {}, 'fn_var_occur': {},
                            'params_descr': {'x': ''}, 'docstring': {'func': None, 'ret': None, 'long_descr': None}},
                           {'name': 'foo', 'params': {}, 'ret_exprs': [], 'params_occur': {}, 'ret_type': 'None',
                            'variables': {}, 'fn_var_occur': {}, 'params_descr': {},
                            'docstring': {'func': None, 'ret': None, 'long_descr': None}}]

        self.assertListEqual(fn_repr_mod_exp, processed_f['funcs'])

    def test_mod_repr_set_dict(self):
        self.assertEqual(processed_f['set'], None)

    def test_mod_untyped_seq(self):
        mod_untyped_seq = "[docstring] [EOL] [EOL] from os import path [EOL] import math [EOL] [EOL] CONSTANT =" \
                          " [string] [EOL] [EOL] [EOL] class MyClass : [EOL] cls_var = [number] [EOL] [EOL] " \
                          "def __init__ ( self , y ) : [EOL] self . y = y [EOL] [EOL] def cls_fn ( self , c ) : " \
                          "[EOL] n = c + [number] [EOL] return MyClass . cls_var + c / ( [number] + n ) [EOL] [EOL] " \
                          "[EOL] class Bar : [EOL] def __init__ ( self ) : [EOL] pass [EOL] [EOL] [EOL] def my_fn " \
                          "( x ) : [EOL] return x + [number] [EOL] [EOL] [EOL] def foo ( ) : [EOL] print ( [string] ) " \
                          "[EOL]"

        self.assertEqual(mod_untyped_seq, processed_f['untyped_seq'])

    def test_mod_typed_seq(self):
        mod_typed_seq = "0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 $int$ 0 0 0 0 0 $None$ 0 0 0 0 0 0 0 0 0 0 0 0 0" \
                        " 0 0 $float$ 0 0 0 $int$ 0 0 0 0 0 $int$ 0 0 0 0 0 0 0 0 $int$ 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0" \
                        " 0 0 0 0 0 0 0 0 0 0 $int$ 0 0 0 0 0 0 0 0 0 0 0 0 0 $None$ 0 0 0 0 0 0 0 0 0"

        self.assertEqual(mod_typed_seq, processed_f['typed_seq'])

    def test_mod_type_annot_cove(self):
        # TODO: Write for a module type annotation coverage
        pass


class TestClassRepresentation(unittest.TestCase):
    """
    It tests the Dict-based representation of classes
    """

    def test_cls_repr_dict_keys(self):
        cls_repr_dict_keys = ['name', 'variables', 'cls_var_occur', 'funcs']
        self.assertListEqual(cls_repr_dict_keys, list((processed_f['classes'][0].keys())))

    def test_cls_repr_name_dict(self):
        cls_repr_name = "MyClass"
        self.assertEqual(cls_repr_name, processed_f['classes'][0]['name'])

    def test_cls_repr_fns_dict(self):
        fns_repr_cls_exp = [{'name': '__init__', 'params': {'self': '', 'y': 'float'}, 'ret_exprs': [],
                             'params_occur': {'self': [['self', 'y', 'y']], 'y': [['self', 'y', 'y']]},
                             'ret_type': 'None', 'variables': {'y': ''}, 'fn_var_occur': {'y': [['self', 'y', 'y']]},
                             'params_descr': {'self': '', 'y': ''},
                             'docstring': {'func': None, 'ret': None, 'long_descr': None}},
                            {'name': 'cls_fn', 'params': {'self': '', 'c': 'int'},
                             'ret_exprs': ['return MyClass.cls_var + c / (2 + n)'],
                             'params_occur': {'self': [], 'c': [['n', 'c'], ['MyClass', 'cls_var', 'c', 'n']]},
                             'ret_type': 'float', 'variables': {'n': ''},
                             'fn_var_occur': {'n': [['n', 'c'], ['MyClass', 'cls_var', 'c', 'n']]},
                             'params_descr': {'self': '', 'c': ''},
                             'docstring': {'func': None, 'ret': None, 'long_descr': None}}]

        self.assertListEqual(fns_repr_cls_exp, processed_f['classes'][0]['funcs'])

    def test_cls_type_annot_cove(self):
        cls_repr_dict = ClassInfo()
        cls_repr_dict.from_dict(processed_f['classes'][0])
        # TODO: Buggy type annotation coverage
        print(cls_repr_dict.get_type_annot_cove())


class TestFunctionRepresentation(unittest.TestCase):
    """
    It tests the Dict-based representation of functions
    """

    def test_fn_repr_dict_keys(self):
        fn_repr_dict_keys = ['name', 'params', 'ret_exprs', 'params_occur', 'ret_type', 'variables', 'fn_var_occur',
                             'params_descr', 'docstring']
        fn_doc_repr_dict_keys = ['func', 'ret', 'long_descr']
        self.assertListEqual(fn_repr_dict_keys + fn_doc_repr_dict_keys,
                             list(processed_f['classes'][0]['funcs'][0].keys()) + \
                             list(processed_f['classes'][0]['funcs'][0]['docstring'].keys()))

    def test_fn_repr_dict(self):
        fn_repr_dict = {'name': '__init__', 'params': {'self': '', 'y': 'float'}, 'ret_exprs': [],
                        'params_occur': {'self': [['self', 'y', 'y']], 'y': [['self', 'y', 'y']]},
                        'ret_type': 'None', 'variables': {'y': ''}, 'fn_var_occur': {'y': [['self', 'y', 'y']]},
                        'params_descr': {'self': '', 'y': ''},
                        'docstring': {'func': None, 'ret': None, 'long_descr': None}}
        self.assertDictEqual(fn_repr_dict, processed_f['classes'][0]['funcs'][0])

    def test_fn_type_annot_cove(self):
        fn = FunctionInfo('my_fn')
        fn.from_dict(processed_f['funcs'][0])

        self.assertEqual(fn.get_type_annot_cove(), 1.0)
