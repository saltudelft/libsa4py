from libsa4py.cst_extractor import Extractor
from libsa4py.representations import FunctionInfo, ModuleInfo, create_output_seq, validate_output_seq
from libsa4py.nl_preprocessing import normalize_module_code
from libsa4py.exceptions import OutputSequenceException
from libsa4py.utils import read_file
import unittest

processed_f = Extractor().extract(open('./examples/representations.py', 'r').read())


class TestModuleRepresentations(unittest.TestCase):
    """
    It tests the Dict-based representation of modules
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maxDiff = None

    def test_mod_repr_dict_keys(self):
        mod_repr_dict_key_exp = ['untyped_seq', 'typed_seq', 'imports', 'variables', 'mod_var_occur', 'mod_var_ln',
                                 'classes', 'funcs', 'set', 'tc', 'no_types_annot', 'type_annot_cove']
        self.assertListEqual(mod_repr_dict_key_exp, list(processed_f.to_dict().keys()))

    def test_mod_repr_cls_dict(self):
        cls_repr_mod_exp = [{'name': 'MyClass', 'q_name': 'MyClass', 'cls_lc': ((12, 0), (23, 44)),
                             'variables': {'cls_var': 'builtins.int'},
                             'cls_var_occur': {'cls_var': [['MyClass', 'cls_var', 'c', 'n']]},
                             'cls_var_ln': {'cls_var': ((16, 4), (16, 11))},
                             'funcs': [{'name': '__init__', 'q_name': 'MyClass.__init__', 'fn_lc': ((18, 4), (19, 18)),
                                        'params': {'self': '', 'y': 'builtins.float'}, 'ret_exprs': [],
                                        'params_occur': {'self': [['self', 'y', 'y']], 'y': [['self', 'y', 'y']]},
                                        'ret_type': 'None', 'variables': {'y': ''},
                                        'fn_var_occur': {'y': [['self', 'y', 'y']]},
                                        'fn_var_ln': {'y': ((19, 8), (19, 14))},
                                        'params_descr': {'self': '', 'y': ''},
                                        'docstring': {'func': None, 'ret': None, 'long_descr': None}},
                                       {'name': 'cls_fn', 'q_name': 'MyClass.cls_fn', 'fn_lc': ((21, 4), (23, 44)),
                                        'params': {'self': '', 'c': 'builtins.int'},
                                        'ret_exprs': ['return MyClass.cls_var + c / (2 + n)'],
                                        'params_occur': {'self': [], 'c': [['n', 'c'],
                                                                           ['MyClass', 'cls_var', 'c', 'n']]},
                                        'ret_type': 'builtins.float', 'variables': {'n': ''},
                                        'fn_var_occur': {'n': [['n', 'c'], ['MyClass', 'cls_var', 'c', 'n']]},
                                        'fn_var_ln': {'n': ((22, 8), (22, 9))},
                                        'params_descr': {'self': '', 'c': ''},
                                        'docstring': {'func': None, 'ret': None, 'long_descr': None}}]},
                            {'name': 'Bar', 'q_name': 'Bar', 'cls_lc': ((26, 0), (28, 12)), 'variables': {},
                             'cls_var_occur': {}, 'cls_var_ln': {},
                             'funcs': [{'name': '__init__', 'q_name': 'Bar.__init__', 'fn_lc': ((27, 4), (28, 12)),
                                        'params': {'self': ''}, 'ret_exprs': [],
                                        'params_occur': {'self': []}, 'ret_type': '', 'variables': {},
                                        'fn_var_occur': {}, 'fn_var_ln': {}, 'params_descr': {'self': ''},
                                        'docstring': {'func': None, 'ret': None, 'long_descr': None}}]}]

        self.assertListEqual(cls_repr_mod_exp, processed_f.to_dict()['classes'])

    def test_mod_repr_fn_dict(self):
        fn_repr_mod_exp = [{'name': 'my_fn', 'q_name': 'my_fn', 'fn_lc': ((31, 0), (32, 17)),
                            'params': {'x': 'builtins.int'}, 'ret_exprs': ['return x + 10'],
                            'params_occur': {'x': []}, 'ret_type': 'builtins.int', 'variables': {}, 'fn_var_occur': {},
                            'fn_var_ln': {}, 'params_descr': {'x': ''},
                            'docstring': {'func': None, 'ret': None, 'long_descr': None}},
                           {'name': 'foo', 'q_name': 'foo', 'fn_lc': ((35, 0), (39, 16)), 'params': {}, 'ret_exprs': [],
                            'params_occur': {}, 'ret_type': 'None', 'variables': {}, 'fn_var_occur': {}, 'fn_var_ln': {},
                            'params_descr': {}, 'docstring': {'func': 'Foo docstring', 'ret': None,
                                                              'long_descr': None}}]

        self.assertListEqual(fn_repr_mod_exp, processed_f.to_dict()['funcs'])

    def test_mod_repr_set_dict(self):
        self.assertEqual(processed_f.to_dict()['set'], None)

    def test_mod_untyped_seq(self):
        mod_untyped_seq = "[docstring] [EOL] [EOL] from os import path [EOL] import math [EOL] [EOL] [comment] [EOL] " \
                          "CONSTANT = [string] [EOL] [EOL] [EOL] class MyClass : [EOL] [docstring] [EOL] cls_var = " \
                          "[number] [comment] [EOL] [EOL] def __init__ ( self , y ) : [EOL] self . y = y [EOL] [EOL] " \
                          "def cls_fn ( self , c ) : [EOL] n = c + [number] [EOL] return MyClass . cls_var + c / " \
                          "( [number] + n ) [EOL] [EOL] [EOL] class Bar : [EOL] def __init__ ( self ) : [EOL] pass " \
                          "[EOL] [EOL] [EOL] def my_fn ( x ) : [EOL] return x + [number] [EOL] [EOL] [EOL] def foo " \
                          "( ) : [EOL] [docstring] [EOL] print ( [string] ) [EOL]"

        self.assertEqual(mod_untyped_seq, processed_f.to_dict()['untyped_seq'])

    def test_mod_typed_seq(self):
        mod_typed_seq = "0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 $builtins.int$ 0 0 0 0 0 0 $None$ 0 0 0 0 " \
                        "0 0 0 0 0 0 0 0 0 0 0 $builtins.float$ 0 0 0 $builtins.int$ 0 0 0 0 0 $builtins.int$ 0 0 0 0 0 " \
                        "0 0 0 $builtins.int$ 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 $builtins.int$ 0 0 0 0 " \
                        "0 0 0 0 0 0 0 0 0 $None$ 0 0 0 0 0 0 0 0 0 0 0"

        self.assertEqual(mod_typed_seq, processed_f.to_dict()['typed_seq'])

    def test_mod_type_annot_cove(self):
        exp_type_annot_cove = 0.64
        self.assertEqual(exp_type_annot_cove, processed_f.type_annot_cove)

    def test_empty_mod_type_annot_cove(self):
        empty_mod = Extractor().extract(open('./examples/__init__.py', 'r').read())
        self.assertEqual(1.0, empty_mod.type_annot_cove)

    def test_no_type_annot(self):
        exp_no_type_annot = {'U': 4, 'D': 7, 'I': 0}
        self.assertDictEqual(exp_no_type_annot, processed_f.to_dict()['no_types_annot'])


class TestClassRepresentation(unittest.TestCase):
    """
    It tests the Dict-based representation of classes
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maxDiff = None

    def test_cls_repr_dict_keys(self):
        cls_repr_dict_keys = ['name', 'q_name', 'cls_lc', 'variables', 'cls_var_occur', 'cls_var_ln', 'funcs']
        self.assertListEqual(cls_repr_dict_keys, list((processed_f.to_dict()['classes'][0].keys())))

    def test_cls_repr_name_dict(self):
        cls_repr_name = "MyClass"
        self.assertEqual(cls_repr_name, processed_f.to_dict()['classes'][0]['name'])

    def test_cls_repr_fns_dict(self):
        fns_repr_cls_exp = [{'name': '__init__', 'q_name': 'MyClass.__init__', 'fn_lc': ((18, 4), (19, 18)),
                             'params': {'self': '', 'y': 'builtins.float'}, 'ret_exprs': [],
                             'params_occur': {'self': [['self', 'y', 'y']], 'y': [['self', 'y', 'y']]},
                             'ret_type': 'None', 'variables': {'y': ''}, 'fn_var_occur': {'y': [['self', 'y', 'y']]},
                             'fn_var_ln': {'y': ((19, 8), (19, 14))}, 'params_descr': {'self': '', 'y': ''},
                             'docstring': {'func': None, 'ret': None, 'long_descr': None}},
                            {'name': 'cls_fn', 'q_name': 'MyClass.cls_fn', 'fn_lc': ((21, 4), (23, 44)),
                             'params': {'self': '', 'c': 'builtins.int'},
                             'ret_exprs': ['return MyClass.cls_var + c / (2 + n)'],
                             'params_occur': {'self': [], 'c': [['n', 'c'], ['MyClass', 'cls_var', 'c', 'n']]},
                             'ret_type': 'builtins.float', 'variables': {'n': ''},
                             'fn_var_occur': {'n': [['n', 'c'], ['MyClass', 'cls_var', 'c', 'n']]},
                             'fn_var_ln': {'n': ((22, 8), (22, 9))}, 'params_descr': {'self': '', 'c': ''},
                             'docstring': {'func': None, 'ret': None, 'long_descr': None}}]

        self.assertListEqual(fns_repr_cls_exp, processed_f.to_dict()['classes'][0]['funcs'])

    def test_cls_type_annot_cove(self):
        # cls_repr_dict = ClassInfo()
        # cls_repr_dict.from_dict(processed_f.to_dict()['classes'][0])
        # TODO: Buggy type annotation coverage
        #print(cls_repr_dict.get_type_annot_cove())
        pass


class TestFunctionRepresentation(unittest.TestCase):
    """
    It tests the Dict-based representation of functions
    """

    def test_fn_repr_dict_keys(self):
        fn_repr_dict_keys = ['name', 'q_name', 'fn_lc', 'params', 'ret_exprs', 'params_occur', 'ret_type', 'variables',
                             'fn_var_occur', 'fn_var_ln', 'params_descr', 'docstring']
        fn_doc_repr_dict_keys = ['func', 'ret', 'long_descr']
        self.assertListEqual(fn_repr_dict_keys + fn_doc_repr_dict_keys,
                             list(processed_f.to_dict()['classes'][0]['funcs'][0].keys()) + \
                             list(processed_f.to_dict()['classes'][0]['funcs'][0]['docstring'].keys()))

    def test_fn_repr_dict(self):
        fn_repr_dict = {'name': '__init__', 'q_name': 'MyClass.__init__', 'fn_lc': ((18, 4), (19, 18)),
                        'params': {'self': '', 'y': 'builtins.float'}, 'ret_exprs': [],
                        'params_occur': {'self': [['self', 'y', 'y']], 'y': [['self', 'y', 'y']]},
                        'ret_type': 'None', 'variables': {'y': ''}, 'fn_var_occur': {'y': [['self', 'y', 'y']]},
                        'fn_var_ln': {'y': ((19, 8), (19, 14))}, 'params_descr': {'self': '', 'y': ''},
                        'docstring': {'func': None, 'ret': None, 'long_descr': None}}
        self.assertDictEqual(fn_repr_dict, processed_f.to_dict()['classes'][0]['funcs'][0])

    # def test_fn_type_annot_cove(self):
    #     fn = FunctionInfo('my_fn')
    #     fn.from_dict(processed_f.to_dict()['funcs'][0])
    #
    #     self.assertEqual(fn.get_type_annot_cove(), 1.0)


class TestOutputSequence(unittest.TestCase):
    """
    It tests the output sequence of Seq2Seq representation.
    """

    def test_normalized_module_code(self):
        self.assertEqual(normalize_module_code(processed_f.untyped_seq),
                         read_file('exp_outputs/normalized_mod_code.txt').strip())

    def test_create_output_sequence(self):
        exp_out_seq = "0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 $builtins.int$ 0 0 0 0 0 0 $None$ 0 0 0 0 0 " \
                      "0 0 0 0 0 0 0 0 0 0 $builtins.float$ 0 0 0 $builtins.int$ 0 0 0 0 0 $builtins.int$ 0 0 0 0 0 0 " \
                      "0 0 $builtins.int$ 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 $builtins.int$ 0 0 0 0 0 0 " \
                      "0 0 0 0 0 0 0 $None$ 0 0 0 0 0 0 0 0 0 0 0"

        self.assertEqual(exp_out_seq, create_output_seq(normalize_module_code(processed_f.typed_seq)))

    def test_invalid_type_alignment_with_name(self):
        # Misses one type
        malformed_out_seq = "0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 $builtins.int$ 0 0 0 0 0 0 0 0 0 0 0 " \
                      "0 0 0 0 0 0 0 0 0 0 $builtins.float$ 0 0 0 $builtins.int$ 0 0 0 0 0 $builtins.int$ 0 0 0 0 0 0 " \
                      "0 0 $builtins.int$ 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 $builtins.int$ 0 0 0 0 0 0 " \
                      "0 0 0 0 0 0 0 $None$ 0 0 0 0 0 0 0 0 0 0 0"

        self.assertRaises(OutputSequenceException, validate_output_seq,
                          normalize_module_code(processed_f.typed_seq), malformed_out_seq)

    def test_invalid_non_name_alignment(self):
        # Has an extra type
        malformed_out_seq = "0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 $builtins.int$ 0 0 0 0 0 0 $None$ 0 0 0 0 0 " \
                      "0 0 0 0 0 0 0 0 0 0 $builtins.float$ 0 0 0 $builtins.int$ 0 0 0 0 0 $builtins.int$ 0 0 0 0 0 0 " \
                      "0 0 $builtins.int$ 0 0 0 0 0 0 0 0 0 0 0 0 0 0 $builtins.int$ 0 0 0 0 0 0 0 0 0 0 $builtins.int$ 0 0 0 0 0 0 " \
                      "0 0 0 0 0 0 0 $None$ 0 0 0 0 0 0 0 0 0 0 0"

        self.assertRaises(OutputSequenceException, validate_output_seq,
                          normalize_module_code(processed_f.typed_seq), malformed_out_seq)

    def test_invalid_input_typed_seq(self):
        valid_out_typed_seq = "0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 $builtins.int$ 0 0 0 0 0 0 $None$ 0 0 0 0 0 " \
                      "0 0 0 0 0 0 0 0 0 0 $builtins.float$ 0 0 0 $builtins.int$ 0 0 0 0 0 $builtins.int$ 0 0 0 0 0 0 " \
                      "0 0 $builtins.int$ 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 $builtins.int$ 0 0 0 0 0 0 " \
                      "0 0 0 0 0 0 0 $None$ 0 0 0 0 0 0 0 0 0 0 0"

        # Don't have required spaces between tokens
        invalid_in_typed_seq = "[docstring] [EOL] [EOL] from os import path [EOL] import math [EOL] [EOL] [comment] " \
                               "[EOL] CONSTANT = [string] [EOL] [EOL] [EOL] class MyClass : [EOL] [docstring] [EOL] " \
                               "$int$ = [number] [comment] [EOL] [EOL] def $None$ ( self , y ) : [EOL] self . y = y " \
                               "[EOL] [EOL] def $float$ ( self , $int$ ) : [EOL] n = $int$+[number] [EOL] " \
                               "return MyClass . cls_var + $int$ / ( [number] + n ) [EOL] [EOL] [EOL] class Bar : " \
                               "[EOL] def __init__ ( self ) : [EOL] pass [EOL] [EOL] [EOL] def $int$ ( x ) : [EOL] " \
                               "return x + [number] [EOL] [EOL] [EOL] def $None$ ( ) : [EOL] [docstring] [EOL] print " \
                               "( [string] ) [EOL]"

        self.assertRaises(OutputSequenceException, validate_output_seq, invalid_in_typed_seq, valid_out_typed_seq)
