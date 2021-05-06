from libsa4py.cst_lenient_parser import lenient_parse_module
from libsa4py.cst_visitor import Visitor
from libsa4py.cst_transformers import SpaceAdder, TypeAdder,\
    CommentAndDocStringRemover, StringRemover, NumberRemover, \
    TypeAnnotationRemover, ParametricTypeDepthReducer
from libsa4py.utils import read_file
import unittest
import libcst as cst


class TestSpaceAdder(unittest.TestCase):
    """
    It tests the SpaceAdder transformer.
    """

    maxDiff = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls.out_p = cst.parse_module(read_file('examples/space_tokens.py'))

        v = Visitor()
        mw = cst.metadata.MetadataWrapper(cls.out_p, cache={cst.metadata.TypeInferenceProvider: {'types': []}})
        mw.visit(v)

        cls.out_untyped_s = cls.out_p.visit(SpaceAdder())
        cls.out_typed_s = cls.out_p.visit(TypeAdder(v.module_all_annotations)).visit(SpaceAdder())

        cls.exp_p = read_file('exp_outputs/added_space.py')

    def test_added_space_file(self):
        self.assertMultiLineEqual(self.exp_p, self.out_untyped_s.code)

    def test_removed_space_from_types(self):
        self.assertFalse("$List[ int ]$" in self.out_typed_s.code)


class TestCommentAndDocStringRemover(unittest.TestCase):
    """
     It tests the removal of comments and docstring from a source code file.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls.out_p = cst.parse_module(read_file('examples/comment_removal.py')).visit(CommentAndDocStringRemover())

    def test_removed_comments_docs_file(self):
        self.assertMultiLineEqual(read_file('exp_outputs/removed_com_docs.py'), self.out_p.code)


class TestStringRemover(unittest.TestCase):
    """
     It tests the removal of string literals from a source code file.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls.out_p = cst.parse_module(read_file('examples/string_removal.py')).visit(StringRemover())

    def test_removed_strings_file(self):
        self.assertMultiLineEqual(read_file('exp_outputs/removed_str.py'), self.out_p.code)


class TestNumberRemover(unittest.TestCase):
    """
     It tests the removal of numeric literals from a source code file.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls.out_p = cst.parse_module(read_file('examples/num_removal.py')).visit(NumberRemover())

    def test_removed_strings_file(self):
        self.assertMultiLineEqual(read_file('exp_outputs/removed_num.py'), self.out_p.code)


class TestTypeAnnotationRemover(unittest.TestCase):
    """
     It tests the removal of type annotations from a source code file.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls.out_p = cst.parse_module(read_file('examples/type_annot_removal.py')).visit(TypeAnnotationRemover())

    def test_removed_strings_file(self):
        self.assertMultiLineEqual(read_file('exp_outputs/removed_type_annot.py'), self.out_p.code)


class TestTypeAdder(unittest.TestCase):
    """
     It tests the type propagation throughout a source code file.
     That is, replacing the typed identifiers with their type.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls.out_p = cst.parse_module(read_file('examples/types_prop.py'))
        v = Visitor()
        mw = cst.metadata.MetadataWrapper(cls.out_p, cache={cst.metadata.TypeInferenceProvider: {'types': []}})
        mw.visit(v)
        cls.out_p = cls.out_p.visit(TypeAdder(v.module_all_annotations))

    def test_propagated_types_file(self):
        # TODO: TypeAdder needs improvements to propagate all the types across the file
        self.assertMultiLineEqual(read_file('exp_outputs/propagated_types.py'), self.out_p.code)


class TestParametricTypeDepthReducer(unittest.TestCase):
    """
    It tests reducing the depth of parametric types.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __reduce_depth_param_type(self, param_type: str, max_depth: int) -> str:
        t = cst.parse_module(param_type)
        t = t.visit(ParametricTypeDepthReducer(max_annot_depth=max_depth))
        return t.code

    def test_param_type_depth(self):
        exp_t = "List[Tuple[str, int]]"
        self.assertEqual(exp_t,
                         self.__reduce_depth_param_type("List[Tuple[str, int]]", 2))

    def test_param_type_depth_reduce_three(self):
        exp_t = "List[List[Any]]"
        self.assertEqual(exp_t,
                         self.__reduce_depth_param_type("List[List[Tuple[str]]]", 2))

    def test_param_type_depth_reduce_four(self):
        exp_t = "List[List[Dict[str, Any]]]"
        self.assertEqual(exp_t,
                         self.__reduce_depth_param_type("List[List[Dict[str, Tuple[int]]]]", 3))

    def test_param_type_reduce_lenient_parse(self):
        param_type = "Dict[str, Type[Union[.vendor.pip._vendor.requests.packages.urllib3.contrib.socks.SOCKSHTTPConnectionPool," \
                     " .vendor.pip._vendor.requests.packages.urllib3.contrib.socks.SOCKSHTTPSConnectionPool]]]"
        exp_out = "Dict[str, Type[Any]]"

        t = lenient_parse_module(param_type)
        t = t.visit(ParametricTypeDepthReducer(2))

        self.assertEqual(t.code, exp_out)


