"""
Testing CST Visitors
"""
from libsa4py.utils import read_file
from libsa4py.cst_visitor import TypeAnnotationCounter
import unittest
import libcst as cst


class TestTypeAnnotationCounter(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls.py_src_f = read_file("./examples/type_annot_count.py")

    def test_no_counted_type_annot(self):
        f_parsed = cst.parse_module(self.py_src_f)
        tac = TypeAnnotationCounter()
        f_parsed.visit(tac)
        expected_no_type_annot = 11

        self.assertEqual(tac.total_no_type_annot, expected_no_type_annot)