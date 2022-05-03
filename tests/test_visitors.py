"""
Testing CST Visitors
"""
from libsa4py.utils import read_file
from libsa4py.cst_visitor import TypeAnnotationCounter, CountParametricTypeDepth
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


class TestParametricTypeDepthReducer(unittest.TestCase):
    """
    It tests counting the depth of parametric types.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __count_depth_param_type(self, param_type: str) -> int:
        t = cst.parse_module(param_type)
        cptd_visitor = CountParametricTypeDepth()
        t.visit(cptd_visitor)
        return cptd_visitor.type_annot_depth

    def test_count_param_type_depth(self):
        param_types_expected_depth = [("List[Tuple[str, int]]", 2),
                                      ("Dict[str, str]", 1),
                                      ("List[List[Dict[str, Tuple[int]]]]", 4),
                                      ("List[Dict[str, Tuple[int]]]", 3)]
        for t, e in param_types_expected_depth:
            self.assertEqual(self.__count_depth_param_type(t), e)
