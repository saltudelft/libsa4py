from libsa4py.cst_extractor import Extractor
import unittest


class TestExtractor(unittest.TestCase):
    """
    It tests extracted attributes and type hints from a Python source code file.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setUp(self):
        self.processed_src_f = Extractor().extract(open('example.py', 'r').read())

    def test_output_dict_fields(self):
        self.assertEqual(list(self.processed_src_f.keys()), ['untyped_seq', 'typed_seq', 'imports', 'variables',
                                                             'classes', 'funcs'])

    def test_extracted_import_names(self):
        self.assertEqual(self.processed_src_f['imports'], ['Optional', 'List'])

    def test_extracted_module_variables(self):
        self.assertEqual(self.processed_src_f['variables'], {"PI": "", "x": "",  "y": "", "z": "",
                                                             "TEST_CONSTANT": "int", "LONG_STRING": ""})

    def test_extracted_class_names(self):
        self.assertEqual([c['name'] for c in self.processed_src_f['classes']], ['Test', 'Test2'])

    def test_extracted_class_variables(self):
        self.assertEqual([c['variables'] for c in self.processed_src_f['classes']], [{"out_x": "", "out_u": "",
                                                                                      "out_f": "", "out_y": "str",
                                                                                      "scientific_num": ""},
                                                                                     {"x": "", "y": "float"}])
