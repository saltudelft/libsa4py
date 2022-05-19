from enum import Enum
import json
from pathlib import Path
from sys import platform
from textwrap import indent
from joblib import delayed

import requests
from tqdm import tqdm

from libsa4py.utils import ParallelExecutor, find_repos_list, list_files

Mode = Enum("Mode", "local internet")
class PredictionMethod(enum.Enum):
    p1_prediction = 1


class Mt4pyPredictProjects:

    """
    Uses Type4Py server requests to make type predictions
    for project files
    """

    def __init__(self, sourcecode_path: str, output_path: str, mode=None, limit=-1):
        self.sourcecode_path = sourcecode_path
        self.output_path = output_path
        self.error_files = []
        self.existing_predictions = set()
        if limit is None:
            self.limit = -1
        else:
            self.limit = limit
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
        with open(file, "r", encoding="utf8") as f:
            data = f.read()
            data = data.encode()
            r = requests.post(self.url, data)
            response = r.json()
            if response["error"]:
                self.error_files.append(file.split(self.sourcecode_path)[1])
            prediction = r.json()
            return prediction

    def output_errors(self):
        with open("./errors/error_files.txt", "w+") as f:
            for error in self.error_files:
                f.write("%s\n" % error)

    def format_prediction(self, prediction, file):
        folderpath = file.rsplit("/", 1)[0]
        filename = "./" + file.rsplit("/", 1)[1]
        if prediction["response"]:
            header = {folderpath: {"src_files": {filename: prediction}}}
            with open(
                self.output_path
                + file.split("repos/")[1].replace("/", "").replace(".py", "")
                + ".json",
                "+w",
            ) as f:
                f.write(json.dumps(header))

    def read_existing_predictions(self):
        path = Path("./existing_predictions.txt")
        if path.is_file():
            with open("./existing_predictions.txt", "r") as ep:
                lines = ep.readlines()
                if len(lines) > 0:
                    for line in lines:
                        self.existing_predictions.add(line.strip())

    def append_existing_predictions(self, file):
        with open("./existing_predictions.txt", "a") as f:
            if not file == "":
                f.write(file + "\n")

    def is_existing_prediction(self, file):
        if file in self.existing_predictions:
            return True
        return False

    def run(self):
        # print("mode is:", self.mode)
        # print("sourcecode path is: ", self.sourcecode_path)
        # print("output path is:", self.output_path)
        limit = 1
        files = list_files(self.sourcecode_path)
        if platform == "win32":
            # print("currently running on a windows machine")
            files = [file.replace("\\", "/") for file in files]

        self.read_existing_predictions()
        if self.limit == -1 or self.limit > len(files):
            limit = len(files)
        else:
            limit = self.limit

        for i in tqdm(range(limit)):
            file = files[i]
            if not self.is_existing_prediction(file):
                self.existing_predictions.add(file)
                prediction = self.predict(file)
                self.format_prediction(prediction, file)
                self.append_existing_predictions(file)
        self.output_errors()


class Mt4pyApplyPredictionMethod:
    def __init__(self, method):
        if()

    def run(self):
        print(f"Applying prediction")
