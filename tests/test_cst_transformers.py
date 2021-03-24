from libsa4py.cst_visitor import Visitor
from libsa4py.cst_transformers import SpaceAdder, TypeAdder
from libsa4py.utils import read_file
import unittest
import filecmp
import libcst as cst


class TestSpaceAdder(unittest.TestCase):
    """
    It tests the SpaceAdder transformer.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls.out_p = cst.parse_module(read_file('examples/space_tokens.py'))

        v = Visitor()
        cls.out_p.visit(v)

        cls.out_untyped_s = cls.out_p.visit(SpaceAdder())
        cls.out_typed_s = cls.out_p.visit(TypeAdder(v.module_all_annotations)).visit(SpaceAdder())

        print(cls.out_typed_s.code)

        cls.exp_p = read_file('exp_outputs/added_space.py')

    def test_added_space_file(self):
        self.assertMultiLineEqual(self.exp_p, self.out_untyped_s.code)

    def test_removed_space_from_types(self):
        self.assertFalse("$List[ int ]$" in self.out_typed_s.code)
