from libsa4py.cst_pipeline import Pipeline
from pathlib import Path
from os.path import join
import unittest
import json
import shutil


class TestPipeline(unittest.TestCase):
    """
    It tests the pipeline of LibSA4Py
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        p_nlp = Pipeline(Path(__file__).parent.absolute().parent,
                         join(Path(__file__).parent.absolute(), 'tmp'), nlp_transf=True, use_pyre=False)
        p_nlp.run([{'author': 'tests', 'repo': 'examples'}], 1)

        p_no_nlp = Pipeline(Path(__file__).parent.absolute().parent,
                            join(Path(__file__).parent.absolute(), 'tmp_nonlp'), nlp_transf=False, use_pyre=False)
        p_no_nlp.run([{'author': 'tests', 'repo': 'examples'}], 1)

    def test_pipeline_output(self):
        pipeline_out_exp = json.loads(open("exp_outputs/testsexamples.json", 'r').read())
        pipeline_out = json.loads(open("tmp/processed_projects/testsexamples.json", 'r').read())

        self.assertDictEqual(pipeline_out_exp, pipeline_out)

    def test_pipeline_output_nonlp(self):
        pipeline_out_nonlp_exp = json.loads(open("exp_outputs/testsexamples_nonlp.json", 'r').read())
        pipeline_out_nonlp = json.loads(open("tmp_nonlp/processed_projects/testsexamples.json", 'r').read())

        self.assertDictEqual(pipeline_out_nonlp_exp, pipeline_out_nonlp)

    # TODO: Test the pipeline when using mypy
    # def test_pipeline_output_mypy(self):
    #     pass

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree("./tmp/")
        shutil.rmtree("./tmp_nonlp/")
