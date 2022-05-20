from libsa4py.cst_extractor import Extractor
import unittest


class TestQualifiedTypes(unittest.TestCase):
    """
    It tests resolving qualified type names, e.g. t.List -> typing.List
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maxDiff = None

    @classmethod
    def setUpClass(cls):
        cls.processed_f = Extractor().extract(open('examples/qualified_types.py', 'r').read()).to_dict()

    def test_qualified_type_assign(self):
        exp_q_type = {'d': 'typing.Dict', 'l': 'typing.List[builtins.str]',
                      'l_n': 'typing.List[typing.Tuple[builtins.int, builtins.int]]',
                      'q_v': 'typing.List[builtins.int]', 't_e': 'typing.Tuple[typing.Any, ...]',
                      'u_d': 'typing.Union[typing.List[typing.Tuple[builtins.str, builtins.int]], '
                             'typing.Tuple[typing.Any], typing.Tuple[typing.List[typing.Tuple[typing.Set[builtins.int]]]]]',
                      'c': 'typing.Callable[..., typing.List]',
                      't_a': 'typing.Type[typing.List]',
                      'tqr': 'libsa4py.cst_transformers.TypeQualifierResolver',
                      'lt': 'typing.Literal["123"]',
                      'c_h': 'typing.Callable[[typing.List, typing.Dict], builtins.int]',
                      's': '[]', 'u': 'Foo', 'foo': 'Foo', 'b': 'True',
                      'foo_t': 'typing.Tuple[Foo, libsa4py.cst_transformers.TypeQualifierResolver]',
                      'N': 'typing.Union[typing.List, None]',
                      'rl': 'representations.Bar',
                      'relative_i': 'test_imports.TestImports'}

        self.assertDictEqual(exp_q_type, self.processed_f['variables'])

    def test_qualified_type_cls_var(self):
        exp_q_type = {'foo_seq': 'collections.abc.Sequence'}
        self.assertDictEqual(exp_q_type, self.processed_f['classes'][1]['variables'])

    def test_qualified_type_fn_params(self):
        exp_q_type = {'self': '', 'x': 'typing.Tuple', 'y': 'typing.Pattern'}
        self.assertDictEqual(exp_q_type, self.processed_f['classes'][1]['funcs'][0]['params'])

    def test_qualified_type_fn_vars(self):
        exp_q_type = {'x': 'typing.Tuple', 'n': 'numpy.int', 'd': 'Delta'}
        self.assertDictEqual(exp_q_type, self.processed_f['classes'][1]['funcs'][0]['variables'])

    def test_qualified_type_fn_ret(self):
        exp_q_ret_type = 'numpy.array'
        self.assertEqual(exp_q_ret_type, self.processed_f['classes'][1]['funcs'][1]['ret_type'])

    def test_shadowed_qualified_name(self):
        exp_q_type = {'sq': 'builtins.str'}
        self.assertDictEqual(exp_q_type, self.processed_f['classes'][1]['funcs'][2]['variables'])
