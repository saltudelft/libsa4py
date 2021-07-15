from libsa4py.cst_extractor import Extractor
import unittest


class TestImports(unittest.TestCase):
    """
    It tests various forms of imports in a file
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls.processed_f = Extractor().extract(open('./examples/imports.py', 'r').read()).to_dict()

    def test_import_single_module(self):
        print(self.processed_f['imports'])
        imp_single_mod_exp = 'math'
        self.assertEqual(imp_single_mod_exp in self.processed_f['imports'], True)

    def test_import_alias(self):
        imp_alias_exp = 'typing'
        self.assertEqual(imp_alias_exp in self.processed_f['imports'], True)

    def test_import_asname(self):
        imp_asname_exp ="t"
        self.assertEqual(imp_asname_exp in self.processed_f['imports'], True)

    def test_inner_imports(self):
        imp_inner_imports = 'collections'
        self.assertEqual(imp_inner_imports in self.processed_f['imports'], True)

    def test_star_import(self):
        imp_star_exp = 'string'
        self.assertEqual(imp_star_exp in self.processed_f['imports'], True)

    def test_module_from_import(self):
        imp_module = ['os', 'path']
        self.assertEqual(all(i for i in imp_module if i in self.processed_f['imports']), True)

    # A case like from . import x
    def test_from_imp_empty_mod(self):
        imp_module = 'assignments'
        self.assertEqual(imp_module in self.processed_f['imports'], True)
