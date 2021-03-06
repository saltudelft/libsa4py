from libsa4py.cst_extractor import Extractor
from libsa4py.representations import ModuleInfo
from libsa4py.utils import read_file, load_json, save_json
import unittest
import json


class TestExtractor(unittest.TestCase):
    """
    It tests the CST extractor of LibSA4Py
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls.extractor_out = Extractor().extract(read_file('./examples/representations.py'))

    def test_extractor_output(self):
        expected_out = load_json('./exp_outputs/extractor_out.json')
        expected_out = ModuleInfo.from_dict(expected_out)

        self.assertEqual(expected_out, self.extractor_out)


class TestExtractorPyre(unittest.TestCase):
    """
    It tests the CST extractor of LibSA4Py while incorporating Pyre's inferred types.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls.extractor_out = Extractor().extract(read_file('./examples/vars_types_pyre.py'),
                                                load_json('./examples/vars_types_pyre_data.json'))

    def test_module_vars_types(self):
        """
        Tests whether pyre's inferred types are incorporated into the module output representation
        """
        exp_mod_vars_types = {"PI": "float", "no": "builtins.int", "CONSTANT": "str", "X": "int", "Y": "int"}
        self.assertDictEqual(exp_mod_vars_types, self.extractor_out.to_dict()['variables'])

    def test_class_vars_types(self):
        """
        Tests whether pyre's inferred types are incorporated into the module output representation
        """
        exp_cls_vars_types = {'foo_num': 'int', 'foo_name': 'str', 'foo_x': 'int', 'foo_y': 'typing.List[int]'}
        self.assertDictEqual(exp_cls_vars_types, self.extractor_out.to_dict()['classes'][0]['variables'])

    def test_local_vars_types(self):
        self.assertDictEqual({'x': 'typing.List[int]', 'y': '', 'l': 'typing.Tuple[typing.Tuple[int, int], str]',
                              'k': 'typing.Tuple[typing.Tuple[int, int], str]'},
                             self.extractor_out.to_dict()['classes'][0]['funcs'][0]['variables'])
        self.assertDictEqual({'x': "typing.Tuple[typing_extensions.Literal['Hello'], typing_extensions.Literal['World']]",
                              'f': 'float', 'g': 'int', 'res': 'float'},
                             self.extractor_out.to_dict()['classes'][0]['funcs'][1]['variables'])

    def test_module_seq2seq_repr(self):
        exp_mod_seq2seq = "0 0 0 $float$ 0 0 0 $builtins.int$ 0 0 0 $str$ 0 0 0 $int$ 0 $int$ 0 0 0 0 0 0 0 0 0 0 " \
                          "$int$ 0 0 0 $str$ 0 0 0 $int$ 0 $typing.List[int]$ 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 " \
                          "0 0 0 0 0 0 $typing.List[int]$ 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 " \
                          "$typing.Tuple[typing.Tuple[int,int],str]$ 0 0 0 $typing.Tuple[typing.Tuple[int,int],str]$ 0 " \
                          "0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 " \
                          "$typing.Tuple[typing_extensions.Literal['Hello'],typing_extensions.Literal['World']]$ 0 0 0 " \
                          "0 0 0 0 $float$ 0 $int$ 0 0 0 0 0 $float$ 0 $float$ 0 $float$ 0 0 0 0"

        self.assertEqual(exp_mod_seq2seq, self.extractor_out.to_dict()['typed_seq'])

    def test_no_type_annot(self):
        exp_no_type_annot = {'U': 4, 'D': 1, 'I': 15}
        self.assertEqual(exp_no_type_annot, self.extractor_out.to_dict()['no_types_annot'])
