from libsa4py.cst_extractor import Extractor
import unittest


class TestQualifiedTypes(unittest.TestCase):
    """
    It tests resolving qualified type names, e.g. t.List -> typing.List
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls.processed_f = Extractor().extract(open('examples/qualified_types.py', 'r').read()).to_dict()

    def test_qualified_type_assign(self):
        exp_q_type = {'d': 'typing.Dict', 'l': 'typing.List[builtins.str]'}
        self.assertDictEqual(exp_q_type, self.processed_f['variables'])

    def test_qualified_type_cls_var(self):
        exp_q_type = {'foo_seq': 'collections.abc.Sequence'}
        self.assertDictEqual(exp_q_type, self.processed_f['classes'][0]['variables'])

    def test_qualified_type_fn_params(self):
        exp_q_type = {'self': '', 'x': 'typing.Tuple', 'y': 'typing.Pattern'}
        self.assertDictEqual(exp_q_type, self.processed_f['classes'][0]['funcs'][0]['params'])

    def test_qualified_type_fn_vars(self):
        exp_q_type = {'x': 'typing.Tuple', 'n': 'numpy.int'}
        self.assertDictEqual(exp_q_type, self.processed_f['classes'][0]['funcs'][0]['variables'])

    def test_qualified_type_fn_ret(self):
        exp_q_ret_type = 'numpy.array'
        self.assertEqual(exp_q_ret_type, self.processed_f['classes'][0]['funcs'][1]['ret_type'])
