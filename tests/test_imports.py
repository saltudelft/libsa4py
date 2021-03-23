from libsa4py.cst_extractor import Extractor
import unittest


class TestImports(unittest.TestCase):
    """
    It tests various forms of imports in a file
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def setUp(cls):
        cls.processed_f = Extractor().extract(open('./examples/imports.py', 'r').read())

    def test_import_single_module(self):
        print(self.processed_f['imports'])
        imp_single_mod_exp = 'math'
        self.assertEqual(imp_single_mod_exp in self.processed_f['imports'], True)

    def test_import_alias(self):
        imp_alias_exp = 'typing'
        self.assertEqual(imp_alias_exp in self.processed_f['imports'], True)

    def test_inner_imports(self):
        imp_inner_imports = 'collections'
        self.assertEqual(imp_inner_imports in self.processed_f['imports'], True)

    def test_star_import(self):
        pass  # TODO: extracting star imports?
