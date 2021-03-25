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
        p = Pipeline(Path(__file__).parent.absolute().parent,
                     join(Path(__file__).parent.absolute(), 'tmp'))
        p.run([{'author': 'tests', 'repo': 'examples'}], 1)

    def test_pipeline_output(self):
        pipeline_out_exp = json.loads(open("exp_outputs/testsexamples.json", 'r').read())
        pipeline_out = json.loads(open("tmp/processed_projects/testsexamples.json", 'r').read())

        self.assertDictEqual(pipeline_out_exp, pipeline_out)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree("./tmp/")
