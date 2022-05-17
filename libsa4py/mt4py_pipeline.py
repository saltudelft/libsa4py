from enum import Enum

import requests

from libsa4py.utils import find_repos_list, list_files

Mode = Enum("Mode", "local internet")


class Mt4pyPredictProjects:

    """
    Uses Type4Py server requests to make type predictions
    for project files
    """

    def __init__(self, sourcecode_path: str, output_path: str, mode=None):
        print(mode)
        self.sourcecode_path = sourcecode_path
        self.output_path = output_path
        if mode is None:
            self.mode = Mode["local"]
            self.url = "http://localhost:5001/"
        else:
            self.mode = Mode[mode]
            self.url = "https://type4py.com/api/predict?tc=0"

    def predict(self, file: str):
        print("predicting types for file...")
        with open(file) as f:
            r = requests.post(self.url)
            data = r.json()

    def run(self):
        print("mode is:", self.mode)
        print("sourcecode path is: ", self.sourcecode_path)
        print("output path is:", self.output_path)
        print(
            "repos in: ",
            self.sourcecode_path,
            "are: ",
            list_files(self.sourcecode_path),
        )
