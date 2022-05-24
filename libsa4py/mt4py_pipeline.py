from encodings import utf_8
from enum import Enum
import json
from pathlib import Path
from sys import platform
from textwrap import indent
from joblib import delayed

import requests
from tqdm import tqdm
from libsa4py.cst_transformers import TypeApplier
from libsa4py.type_check import MypyManager, TCManager, type_check_single_file

from libsa4py.utils import (
    ParallelExecutor,
    find_repos_list,
    list_files,
    read_file,
    read_file_strong,
    write_file,
    write_file_strong,
)
import libcst as cst

Mode = Enum("Mode", "local internet")
PredictionMethod = Enum("PredictionMethod", "p1_prediction combinatoral")
# class PredictionMethod(enum.Enum):
#     p1_prediction = 1


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
        self.amount_predictions = 0
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
            header = {folderpath: {"src_files": {filename: prediction["response"]}}}
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
            with open("./existing_predictions.txt", "r", encoding="utf-8") as ep:
                lines = ep.readlines()
                self.amount_predictions = len(lines)
                if len(lines) > 0:
                    for line in lines:
                        self.existing_predictions.add(line.strip())

    def append_existing_predictions(self, file):
        with open("./existing_predictions.txt", "a", encoding="utf-8") as f:
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
        files = list_files(self.sourcecode_path)
        if platform == "win32":
            # print("currently running on a windows machine")
            files = [file.replace("\\", "/") for file in files]

        self.read_existing_predictions()
        if self.limit == -1 or self.limit > len(files):
            limit = len(files)
        else:
            limit = self.limit

        for i in tqdm(range(limit), initial=self.amount_predictions):
            file = files[i]
            if not self.is_existing_prediction(file):
                print(f"Predicting file: {file}")
                self.existing_predictions.add(file)
                prediction = self.predict(file)
                self.format_prediction(prediction, file)
                self.append_existing_predictions(file)
        self.output_errors()


class Mt4PyApplyTypesSourcecode:
    def __init__(self, prediction_path, sourcecode_path, output_path, limit=-1):
        self.prediction_path = prediction_path
        self.sourcecode_path = sourcecode_path
        self.output_path = output_path
        if limit is None:
            self.limit = -1
        else:
            self.limit = limit
        print("init")

    def apply_file(self, json_file):
        with open(json_file, "+r", encoding="utf-8") as f:
            data = json.load(f)
            path = list(data)[0]
            file = list(data[path]["src_files"])[0]
            src_file_path = path + file.split(".", 1)[1]
            clean_src_path = src_file_path.split("/", 2)[2]
            src_file_path = "./" + self.sourcecode_path + clean_src_path
            out_file_path = self.output_path + "/" + clean_src_path
            data = data[path]["src_files"][file]
        # print(src_file_path)
        # print(data)
        f_read = read_file_strong(src_file_path)
        if len(f_read) != 0:
            try:
                f_parsed = cst.parse_module(f_read)
                try:
                    f_parsed = cst.metadata.MetadataWrapper(f_parsed).visit(
                        TypeApplier(data, True)
                    )
                    print(out_file_path)
                    write_file_strong(out_file_path, f_parsed.code)
                except KeyError as ke:
                    print(
                        f"A variable not found | project {self.sourcecode_path} | file {src_file_path}",
                        ke,
                    )
                except TypeError as te:
                    print(f"Project {self.sourcecode_path} | file {src_file_path}", te)

            except cst._exceptions.ParserSyntaxError as pse:
                print(f"Can't parsed file {f} in project {src_file_path}", pse)

    def run(self):
        files = list_files(self.prediction_path, file_ext=".json")
        if platform == "win32":
            # print("currently running on a windows machine")
            files = [file.replace("\\", "/") for file in files]

        if self.limit == -1 or self.limit > len(files):
            limit = len(files)
        else:
            limit = self.limit
        print(limit)
        for i in tqdm(range(limit)):
            file = files[i]
            self.apply_file(file)
        print("run")


class TypeAnnotatingProjects:
    """
    It applies the inferred type annotations to the input dataset
    """

    def __init__(self, projects_path: str, output_path: str, apply_nlp: bool = True):
        self.projects_path = projects_path
        self.output_path = output_path
        self.apply_nlp = apply_nlp

    def process_project(self, proj_json_path: str):
        proj_json = load_json(proj_json_path)
        for p in proj_json.keys():
            for i, (f, f_d) in enumerate(proj_json[p]["src_files"].items()):
                f_read = read_file(join(self.projects_path, f))
                if len(f_read) != 0:
                    try:
                        f_parsed = cst.parse_module(f_read)
                        try:
                            f_parsed = cst.metadata.MetadataWrapper(f_parsed).visit(
                                TypeApplier(f_d, self.apply_nlp)
                            )
                            write_file(join(self.projects_path, f), f_parsed.code)
                        except KeyError as ke:
                            print(
                                f"A variable not found | project {proj_json_path} | file {f}",
                                ke,
                            )
                            traceback.print_exc()
                        except TypeError as te:
                            print(f"Project {proj_json_path} | file {f}", te)
                            traceback.print_exc()
                    except cst._exceptions.ParserSyntaxError as pse:
                        print(f"Can't parsed file {f} in project {proj_json_path}", pse)

    def run(self, jobs: int):
        proj_jsons = list_files(join(self.output_path, "processed_projects"), ".json")
        proj_jsons.sort(key=lambda f: os.stat(f).st_size, reverse=True)
        ParallelExecutor(n_jobs=jobs)(total=len(proj_jsons))(
            delayed(self.process_project)(p_j) for p_j in proj_jsons
        )


class Mt4pyApplyPredictionMethod:
    def __init__(self, method, prediction_path):
        method_exists = False
        self.prediction_path = prediction_path
        self.min_confidence = 0.1
        for name in PredictionMethod.__members__:
            if method == name:
                self.method = PredictionMethod[method]
                method_exists = True
                break
        if not method_exists:
            self.method = PredictionMethod["p1_prediction"]

    # Applies prediction method p1 to variables
    def p1_variables(self, object):
        variables = object["variables"]
        p_variables = object["variables_p"]
        if variables and p_variables:
            for variable in variables:
                # If variable has atleast 1 prediction:
                if len(p_variables[variable]) > 0:
                    # If confidence of prediction is higher than minimum confidence:
                    if p_variables[variable][0][1] > self.min_confidence:
                        variables[variable] = p_variables[variable][0][0]
        object["variables"] = variables
        return object

    # Applies prediction method p1 to functions
    def p1_functions(self, f_object):
        # Return type:
        if "ret_type" in f_object and "ret_type_p" in f_object:
            return_type = f_object["ret_type"]
            p_return_types = f_object["ret_type_p"]
            # If return type has atleast 1 prediction:
            if len(p_return_types) > 0:
                # If confidence of prediction is higher than minimum confidence:
                if p_return_types[0][1] > self.min_confidence:
                    f_object["ret_type"] = p_return_types[0][0]
        # Parameters:
        if "params_p" in f_object and "params" in f_object:
            params = f_object["params"]
            p_params = f_object["params_p"]
            if params and p_params:
                for param in params:
                    # If param has atleast 1 prediction:
                    if len(p_params[param]) > 0:
                        # If confidence of prediction is higher than minimum confidence:
                        if p_params[param][0][1] > self.min_confidence:
                            params[param] = p_params[param][0][0]
        f_object["params"] = params

        # Variables:
        f_object = self.p1_variables(f_object)

        return f_object

    # Applies prediction method p1 to classes
    def p1_classes(self, c_object):
        # Variables
        c_object = self.p1_variables(c_object)
        # Functions:
        functions = c_object["funcs"]
        if len(functions) > 0:
            for index, f_object in enumerate(functions):
                functions[index] = self.p1_functions(f_object)
        c_object["funcs"] = functions
        return c_object

    # Applies p1 prediction method
    def apply_p1_prediction_method(self, file):
        data = ""
        with open(file, "+r") as f:
            data = json.load(f)

        first_key = list(data.keys())[0]
        second_key = "src_files"
        third_key = list(data[first_key][second_key].keys())[0]

        # Global variables
        g_object = data[first_key][second_key][third_key]
        data[first_key][second_key][third_key] = self.p1_variables(g_object)

        # Functions:
        functions = data[first_key][second_key][third_key]["funcs"]
        if len(functions) > 0:
            for index, f_object in enumerate(functions):
                functions[index] = self.p1_functions(f_object)
        data[first_key][second_key][third_key]["funcs"] = functions

        # Classes:
        classes = data[first_key][second_key][third_key]["classes"]
        if len(classes) > 0:
            for index, c_object in enumerate(classes):
                classes[index] = self.p1_classes(c_object)
        data[first_key][second_key][third_key]["classes"] = classes

        # Rewrite filename and save to appropiate folder
        split_file_name = file.split("/", 2)
        parsed_file_name = split_file_name[len(split_file_name) - 1]
        with open("./prediction_methods/p1_predictions/" + parsed_file_name, "+w") as f:
            f.write(json.dumps(data))
        # print("find matching ground truths in prediction file")
        # print("save matching ground truths")
        # print("apply #1 predictions to prediction json and make new files")
        # print("save #1 predictions")

    # Case match for different prediction methods
    def apply_prediction_method(self, file):
        if self.method.value == 1:
            self.apply_p1_prediction_method(file)

    def run(self):
        files = list_files(self.prediction_path, file_ext=".json")
        if platform == "win32":
            # print("currently running on a windows machine")
            files = [file.replace("\\", "/") for file in files]
        for i in tqdm(range(len(files))):
            file = files[i]
            self.apply_prediction_method(file)


class Mt4pyApplyTypecheck:
    """
    Apply typechecking and report results
    TODO:
    give output better names: linenumbers : error
    """

    def __init__(self, sourcecodepath, limit):
        if limit is None:
            self.limit = -1
        else:
            self.limit = limit
        self.tc_manager = MypyManager("mypy", 1000)
        self.sourcecode_path = sourcecodepath

    def typecheck_file(self, file):
        split_file = file.split("/", 2)
        parsed_file = split_file[len(split_file) - 1]
        result = {parsed_file: type_check_single_file(file, self.tc_manager)}
        return result

    def write_to_file(self, type_check):
        path = "./tc_results.json"
        with open(path, "+w") as f:
            json.dump(type_check, f, indent=4)

    def run(self):
        files = list_files(self.sourcecode_path)
        if platform == "win32":
            # print("currently running on a windows machine")
            files = [file.replace("\\", "/") for file in files]
        if self.limit == -1 or self.limit > len(files):
            limit = len(files)
        else:
            limit = self.limit

        type_check = {"tc_results": []}
        for i in tqdm(range(limit)):
            file = files[i]
            type_check["tc_results"].append(self.typecheck_file(file))
        self.write_to_file(type_check)
