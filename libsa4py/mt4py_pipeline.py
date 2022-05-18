from enum import Enum
import json
from sys import platform
from textwrap import indent
from joblib import delayed

import requests
from tqdm import tqdm

from libsa4py.utils import ParallelExecutor, find_repos_list, list_files

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
        self.error_files = []
        if mode is None:
            self.mode = Mode["local"]
        else:
            self.mode = Mode[mode]
            self.url = "https://type4py.com/api/predict?tc=0"
        if mode == Mode.internet:
            self.url = "https://type4py.com/api/predict?tc=0"
        else:
            self.url = "http://localhost:5001/api/predict?tc=0"

    def predict(self, file: str):
        print("predicting types for file...")
        # print(file)
        # file = "./mytype4py/input_files/quake.py"
        # file = "./source_files_test/repos/007MrNiko/Stepper/manage.py"
        # print(self.url)
        # print(file)
        with open(file) as f:
            data = f.read()
            data = data.encode()
            r = requests.post(self.url, data)
            response = r.json()

            if response["error"]:
                self.error_files.append(file.split("./source_files_test")[1])

            prediction = r.json()
            return prediction

    def output_errors(self):
        with open("./errors/error_files.txt", "w+") as f:
            for error in self.error_files:
                f.write("%s\n" % error)

    def format_prediction(self, prediction, file):
        folderpath = file.rsplit("/", 1)[0]
        filename = "./" + file.rsplit("/", 1)[1]
        # Only save predictions that didn't receive error
        if prediction["response"]:
            header = {folderpath: {"src_files": {filename: prediction}}}
            with open(
                "./predicted_projects/"
                + file.split("repos/")[1].replace("/", "").replace(".py", "")
                + ".json",
                "+w",
            ) as f:
                f.write(json.dumps(header))

    def run(self):
        print("mode is:", self.mode)
        print("sourcecode path is: ", self.sourcecode_path)
        print("output path is:", self.output_path)
        files = list_files(self.sourcecode_path)
        if platform == "win32":
            print("currently running on a windows machine")
            files = [file.replace("\\", "/") for file in files]

        for i in tqdm(range(100)):
            file = files[i]
            prediction = self.predict(file)
            self.format_prediction(prediction, file)

        self.output_errors()
