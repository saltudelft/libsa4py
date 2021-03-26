from libsa4py.cst_extractor import Extractor
from libsa4py.representations import ModuleInfo
from libsa4py.utils import read_file, load_json
import unittest


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
