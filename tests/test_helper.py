from libsa4py.helper import extract_names_from_type_annot
import unittest


class TestImports(unittest.TestCase):
    """
    It tests helper functions
    """

    def test_extract_names_from_type_annot(self):

        test_input_exp = [("List[str]", ['List', 'str']),
                          ("List[builtins.str]", ['List', 'builtins', 'str']),
                          ("typing.Dict[str, Any]", ['typing', 'Dict', 'str', 'Any']),
                          ("sklearn.svm.SVC", ['sklearn', 'svm', 'SVC']),
                          ("typing.List[numpy.array]", ['typing', 'List', 'numpy', 'array'])]

        for input, expected in test_input_exp:
            self.assertEqual(extract_names_from_type_annot(input), expected)
