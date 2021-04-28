from libsa4py.cst_extractor import Extractor
import unittest


class TestVarsArgsOccur(unittest.TestCase):
    """
    It tests various forms of contextual use for module-level, class-level, and local variables plus arguments.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls.processed_f = Extractor().extract(open('./examples/vars_args_occur.py', 'r').read()).to_dict()

    def test_module_vars_use(self):
        mod_vars_use_expected = {'PI': [['PI', 'add_something'], ['range', 'int', 'PI'], ['PI', 'MOD_CONSTANT'],
                                        ['PI', 'add_something'], ['MOD_CONSTANT', 'PI', 'add_something', 'n']],
                                 'MOD_CONSTANT': [['cls_constant', 'MOD_CONSTANT'], ['PI', 'MOD_CONSTANT'],
                                                  ['MOD_CONSTANT', 'PI', 'add_something', 'n']]}
        self.assertDictEqual(mod_vars_use_expected, self.processed_f['mod_var_occur'])


    def test_fn_params_occur(self):
        print(self.processed_f['classes'][0]['funcs'][1]['params_occur'])
        fn_params_occur_exp = {'self': [],
                               'param1': [['z', 'param1', 'param2'], ['add_x_y', 'add', 'param1', 'param2'],
                                          ['list_comp', 'i', 'i', 'range', 'param1', 'param2', 'z'],
                                          ['param1', 'add_x_y'], ['param1', 'param2'], ['param2', 'param1', 'z'],
                                          ['range', 'param1', 'z'], ['param1', 'add_x_y', 'z'], ['param1', 'param2']],
                               'param2': [['z', 'param1', 'param2'], ['add_x_y', 'add', 'param1', 'param2'],
                                          ['list_comp', 'i', 'i', 'range', 'param1', 'param2', 'z'],
                                          ['param1', 'param2'], ['param2', 'param1', 'z'], ['z', 'param2', 'f'],
                                          ['print', 'z', 'param2', 'f'], ['z', 'param2'], ['param1', 'param2']]}
        self.assertDictEqual(fn_params_occur_exp, self.processed_f['classes'][0]['funcs'][1]['params_occur'])


    def test_cls_vars_use(self):
        cls_vars_use = {'greeting': [['TestVarArgOccur', 'greeting', 'f']],
                        'num': [['c', 'self', 'x', 'TestVarArgOccur', 'num'], ['TestVarArgOccur', 'num', 'c'],
                                ['range', 'TestVarArgOccur', 'num'], ['TestVarArgOccur', 'num', 'i'],
                                ['TestVarArgOccur', 'num'], ['TestVarArgOccur', 'num']],
                        'cls_constant': [['c', 'TestVarArgOccur', 'cls_constant'],
                                         ['TestVarArgOccur', 'cls_constant', 'c']]}

        self.assertDictEqual(cls_vars_use, self.processed_f['classes'][0]['cls_var_occur'])

    def test_local_vars_use(self):
        local_vars_use = {'v': [['v', 'builtins', 'int', 'sum'], ['v_1', 'v', 'p'], ['range', 'v', 'v_1'], ['i', 'v'],
                                ['v', 'v_1', 'v'], ['print', 'v'], ['v', 'v_1'], ['print', 'v', 'v_1'],
                                ['v', 'v_1', 'p'], ['v', 'v_1'], ['v', 'n'], ['v', 'p', 'p']],
                          'v_1': [['v_1', 'v', 'p'], ['range', 'v', 'v_1'], ['i', 'v_1'], ['v', 'v_1', 'v'],
                                  ['v', 'v_1'], ['print', 'v', 'v_1'], ['print', 'v_1'], ['v', 'v_1', 'p'],
                                  ['v', 'v_1'], ['v_1', 'p', 'n']]}

        self.assertDictEqual(local_vars_use, self.processed_f['classes'][0]['funcs'][2]['fn_var_occur'])

