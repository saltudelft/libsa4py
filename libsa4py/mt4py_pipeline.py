from collections import Counter
from datetime import timedelta
from encodings import utf_8
from enum import Enum
import json
import os
from pathlib import Path
from sys import platform
from textwrap import indent
import time
from typing import OrderedDict
from joblib import delayed
from psutil import cpu_count
import regex

import requests
from tqdm import tqdm
from libsa4py.cst_transformers import (
    TypeApplier,
    TypeApplierExtended,
    TypeApplierExtendedBranch,
)
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
from libsa4py.mt4py_filestatistics import predictionElement, fileStatistics

Mode = Enum("Mode", "local internet")
PredictionMethod = Enum("PredictionMethod", "p1_prediction gt_match")


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
                + file.split("repos/")[1].replace("/", "").replace(".py", ".json"),
                "+w",
            ) as f:
                f.write(json.dumps(header))

    def read_existing_predictions(self):
        path = Path("./existing_predictions.txt")
        self.amount_predictions = list_files(self.output_path, file_ext=".json")
        if path.is_file():
            with open("./existing_predictions.txt", "r", encoding="utf-8") as ep:
                lines = ep.readlines()
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
                print(f"Predicting file: {file}")
                self.existing_predictions.add(file)
                prediction = self.predict(file)
                self.format_prediction(prediction, file)
                self.append_existing_predictions(file)
        self.output_errors()


# TODO:
# Sanitize original to work with typings and other common similiar types
# Add start argument to say where to start
class Mt4pyApplyPredictionMethod:
    def __init__(self, method, prediction_path, treshold, output_folder):
        method_exists = False
        self.prediction_path = prediction_path
        self.min_confidence = treshold
        self.output_folder = output_folder
        for name in PredictionMethod.__members__:
            if method == name:
                self.method = PredictionMethod[method]
                method_exists = True
                break
        if not method_exists:
            self.method = PredictionMethod["p1_prediction"]

    # Applies prediction method p1 to variables
    def p1_variables(self, object, file_stat: fileStatistics, key):
        variables = object["variables"]
        p_variables = object["variables_p"]
        line_numbers = object[key]
        if variables and p_variables:
            for variable in variables:
                # Prediction element work for file statistics:
                original = variables[variable]
                # If variable has atleast 1 prediction:
                if len(p_variables[variable]) > 0:
                    p_element = predictionElement(
                        variable,
                        "variable",
                        "empty",
                        original,
                        line_numbers[variable][0][0],
                    )
                    prediction = p_variables[variable][0][0]
                    prediction_confidence = p_variables[variable][0][1]
                    # If confidence of prediction is higher than minimum confidence:

                    if prediction_confidence >= self.min_confidence:
                        if original == prediction:
                            p_element.match_case = "match"
                        elif original:
                            p_element.match_case = "mismatch"
                        variables[variable] = prediction
                        p_element.predicted_type = prediction
                        file_stat.addPredictionElement(p_element)

        object["variables"] = variables
        return object

    # Applies prediction method p1 to functions
    def p1_functions(self, f_object, file_stat: fileStatistics):
        # Return type:
        if "ret_type" in f_object and "ret_type_p" in f_object:
            return_type = f_object["ret_type"]
            p_return_types = f_object["ret_type_p"]
            line_number_return = f_object["fn_lc"][1][0]
            # If return type has atleast 1 prediction:
            if len(p_return_types) > 0:
                p_element = predictionElement(
                    "", "return_type", "empty", return_type, line_number_return
                )
                prediction = p_return_types[0][0]
                prediction_confidence = p_return_types[0][1]
                # If confidence of prediction is higher than minimum confidence:
                if prediction_confidence >= self.min_confidence:
                    if prediction == return_type:
                        p_element.match_case = "match"
                    elif return_type:
                        p_element.match_case = "mismatch"
                    f_object["ret_type"] = prediction
                    p_element.predicted_type = prediction
                    file_stat.addPredictionElement(p_element)
        # Parameters:
        if "params_p" in f_object and "params" in f_object:
            params = f_object["params"]
            p_params = f_object["params_p"]
            line_number_parameters = f_object["fn_lc"][0][0]
            if params and p_params:
                for param in params:
                    original = params[param]
                    # If param has atleast 1 prediction:
                    if len(p_params[param]) > 0:
                        p_element = predictionElement(
                            param,
                            "parameter",
                            "empty",
                            original,
                            line_number_parameters,
                        )
                        prediction = p_params[param][0][0]
                        prediction_confidence = p_params[param][0][1]
                        # If confidence of prediction is higher than minimum confidence:
                        if prediction_confidence >= self.min_confidence:
                            if prediction == original:
                                p_element.match_case = "match"
                            elif original:
                                p_element.match_case = "mismatch"
                            params[param] = prediction
                            p_element.predicted_type = prediction
                            file_stat.addPredictionElement(p_element)
        f_object["params"] = params

        # Variables:
        f_object = self.p1_variables(f_object, file_stat, "fn_var_ln")

        return f_object

    # Applies prediction method p1 to classes
    def p1_classes(self, c_object, file_stat):
        # Variables
        c_object = self.p1_variables(c_object, file_stat, "cls_var_ln")
        # Functions:
        functions = c_object["funcs"]
        if len(functions) > 0:
            for index, f_object in enumerate(functions):
                functions[index] = self.p1_functions(f_object, file_stat)
        c_object["funcs"] = functions
        return c_object

    # Applies p1 prediction method
    def apply_p1_prediction_method(self, file):
        file_stat = fileStatistics(file)
        data = ""
        with open(file, "+r") as f:
            data = json.load(f)

        first_key = list(data.keys())[0]
        second_key = "src_files"
        third_key = list(data[first_key][second_key].keys())[0]

        # Global variables
        g_object = data[first_key][second_key][third_key]
        data[first_key][second_key][third_key] = self.p1_variables(
            g_object, file_stat, "mod_var_ln"
        )

        # Functions:
        functions = data[first_key][second_key][third_key]["funcs"]
        if len(functions) > 0:
            for index, f_object in enumerate(functions):
                functions[index] = self.p1_functions(f_object, file_stat)
        data[first_key][second_key][third_key]["funcs"] = functions

        # # Classes:
        classes = data[first_key][second_key][third_key]["classes"]
        if len(classes) > 0:
            for index, c_object in enumerate(classes):
                classes[index] = self.p1_classes(c_object, file_stat)
        data[first_key][second_key][third_key]["classes"] = classes

        return data, file_stat.toJSON()
        # Rewrite filename and save to appropiate folder

    def write_predictions(self, file, predictions):
        split_file_name = file.split("/", 2)
        parsed_file_name = split_file_name[len(split_file_name) - 1]
        path = f"./prediction_methods/{self.output_folder}"
        Path(path).mkdir(parents=True, exist_ok=True)
        with open(path + "/" + parsed_file_name, "+w") as f:
            f.write(json.dumps(predictions))

    def write_filestats(self, file, filestat):
        split_file_name = file.split("/", 2)
        parsed_file_name = split_file_name[len(split_file_name) - 1]
        path = f"./filestats/{self.output_folder}"
        Path(path).mkdir(parents=True, exist_ok=True)
        with open(path + "/" + parsed_file_name, "+w") as f:
            f.write(filestat)

    # Case match for different prediction methods
    def apply_prediction_method(self, file):
        if self.method.value == 1:
            predictions, file_stat = self.apply_p1_prediction_method(file)
            self.write_predictions(file, predictions)
            self.write_filestats(file, file_stat)

    def run(self):
        files = list_files(self.prediction_path, file_ext=".json")
        if platform == "win32":
            # print("currently running on a windows machine")
            files = [file.replace("\\", "/") for file in files]

        limit = len(files)
        start_t = time.time()
        jobs = cpu_count()
        start = 0
        ParallelExecutor(n_jobs=jobs)(total=limit)(
            delayed(self.apply_prediction_method)(file)
            for i, file in enumerate(files[start:limit], start=start)
        )
        print(
            "Finished processing %d files in %s "
            % (limit, str(timedelta(seconds=time.time() - start_t)))
        )

        # for i in tqdm(range(len(files))):
        #     file = files[i]
        #     self.apply_prediction_method(file)


class Mt4PyApplyTypesSourcecode:
    def __init__(
        self, prediction_path, sourcecode_path, output_path, limit=-1, cores=-1
    ):
        self.prediction_path = prediction_path
        self.sourcecode_path = sourcecode_path
        self.output_path = output_path
        if cores is None:
            self.cores = -1
        else:
            self.cores = cores
        if limit is None:
            self.limit = -1
        else:
            self.limit = limit

    def apply_file(self, json_file):
        with open(json_file, "+r", encoding="utf-8") as f:
            data = json.load(f)
            path = list(data)[0]
            file = list(data[path]["src_files"])[0]
            src_file_path = path + file.split(".", 1)[1]
            clean_src_path = src_file_path.split("/", 2)[2]
            src_file_path = self.sourcecode_path + clean_src_path
            out_file_path = self.output_path + clean_src_path
            data = data[path]["src_files"][file]
        try:
            f_read = read_file_strong(src_file_path)
        except:
            return
        if len(f_read) != 0:
            try:
                f_parsed = cst.parse_module(f_read)
                try:
                    tae = TypeApplierExtendedBranch(data, False)
                    f_parsed = cst.metadata.MetadataWrapper(f_parsed).visit(tae)
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
            files = [file.replace("\\", "/") for file in files]

        if self.limit == -1 or self.limit > len(files):
            limit = len(files)
        else:
            limit = self.limit
        start_t = time.time()
        jobs = cpu_count()
        if self.cores != -1:
            jobs = self.cores
        start = 0
        ParallelExecutor(n_jobs=jobs)(total=limit - start)(
            delayed(self.apply_file)(file)
            for i, file in enumerate(files[start:limit], start=start)
        )
        # for i in tqdm(range(limit)):
        #     file = files[i]
        #     self.apply_file(file)
        print(
            "Finished processing %d files in %s "
            % (limit, str(timedelta(seconds=time.time() - start_t)))
        )
        # for i in tqdm(range(limit)):
        #     file = files[i]
        #     self.apply_file(file)
        # print("run")


class Mt4pyApplyTypecheck:
    """
    Apply typechecking and report results
    """

    def __init__(self, sourcecodepath, resultsfolder, limit, cores=-1):
        if limit is None:
            self.limit = -1
        else:
            self.limit = limit
        if cores is None:
            self.cores = -1
        else: 
            self.cores = cores
        self.tc_manager = MypyManager("mypy", 1000)
        self.sourcecode_path = sourcecodepath
        self.resultsfolder = resultsfolder

    def typecheck_file(self, file):
        result = type_check_single_file(file, self.tc_manager)
        return result

    def write_to_file(self, parsed_file, type_check):
        path = f"tc_results/{self.resultsfolder}/"
        if not os.path.isdir(path):
            Path(path).mkdir(parents=True, exist_ok=True)
        with open(path + parsed_file, "+w") as f:
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
        start_t = time.time()
        jobs = cpu_count()
        if self.cores != -1:
            jobs = self.cores
        start = 0
        ParallelExecutor(n_jobs=jobs)(total=limit - start)(
            delayed(self.type_check_files)(file)
            for i, file in enumerate(files[start:limit], start=start)
        )
        print(
            "Finished processing %d files in %s "
            % (limit, str(timedelta(seconds=time.time() - start_t)))
        )

        # Single run
        # type_check = {"tc_results": []}
        # for i in tqdm(range(limit)):
        #     file = files[i]
        #     type_check["tc_results"].append(self.typecheck_file(file))
        # self.write_to_file(type_check)

    def type_check_files(self, file):
        split_file = file.split("repos/", 2)
        parsed_file = split_file[len(split_file) - 1]
        parsed_file = parsed_file.replace("/", "")
        parsed_file = parsed_file.replace(".py", ".json")
        checked_file = self.typecheck_file(file)
        self.write_to_file(parsed_file, checked_file)


class Mt4pyEvaluate:
    def __init__(self, filestat_folder, tc_results_folder, name, limit):
        self.filestat_folder = filestat_folder
        self.tc_results_folder = tc_results_folder
        self.name = name
        self.limit = limit
        if limit is None:
            self.limit = -1
        else:
            self.limit = limit

        self.type_info = {
            "type_info": {
                "variable": {
                    "match_types": {
                        "empty": {"original_types": [], "predicted_types": []},
                        "match": {"original_types": [], "predicted_types": []},
                        "mismatch": {"original_types": [], "predicted_types": []},
                    }
                },
                "return_type": {
                    "match_types": {
                        "empty": {"original_types": [], "predicted_types": []},
                        "match": {"original_types": [], "predicted_types": []},
                        "mismatch": {"original_types": [], "predicted_types": []},
                    }
                },
                "parameter": {
                    "match_types": {
                        "empty": {"original_types": [], "predicted_types": []},
                        "match": {"original_types": [], "predicted_types": []},
                        "mismatch": {"original_types": [], "predicted_types": []},
                    }
                },
            }
        }
        self.result = {
            "evaluation": {
                "total": 0,
                "variable": {
                    "match_types": {
                        "empty": {
                            "total": 0,
                            "errors": 0,
                        },
                        "match": {"total": 0, "errors": 0},
                        "mismatch": {"total": 0, "errors": 0},
                    },
                },
                "return_type": {
                    "match_types": {
                        "empty": {
                            "total": 0,
                            "errors": 0,
                        },
                        "match": {"total": 0, "errors": 0},
                        "mismatch": {"total": 0, "errors": 0},
                    },
                },
                "parameter": {
                    "match_types": {
                        "empty": {
                            "total": 0,
                            "errors": 0,
                        },
                        "match": {"total": 0, "errors": 0},
                        "mismatch": {"total": 0, "errors": 0},
                    },
                },
            }
        }

    def resolve_type_alias(self, t: str):
        type_aliases = {
            "(?<=.*)any(?<=.*)|(?<=.*)unknown(?<=.*)": "Any",
            "^{}$|^Dict$|^Dict\[\]$|(?<=.*)Dict\[Any, *?Any\](?=.*)|^Dict\[unknown, *Any\]$": "dict",
            "^Set$|(?<=.*)Set\[\](?<=.*)|^Set\[Any\]$": "set",
            "^Tuple$|(?<=.*)Tuple\[\](?<=.*)|^Tuple\[Any\]$|(?<=.*)Tuple\[Any, *?\.\.\.\](?=.*)|^Tuple\[unknown, *?unknown\]$|^Tuple\[unknown, *?Any\]$|(?<=.*)tuple\[\](?<=.*)": "tuple",
            "^Tuple\[(.+), *?\.\.\.\]$": r"Tuple[\1]",
            "\\bText\\b": "str",
            "^\[\]$|(?<=.*)List\[\](?<=.*)|^List\[Any\]$|^List$": "list",
            "^\[{}\]$": "List[dict]",
            "(?<=.*)Literal\['.*?'\](?=.*)": "Literal",
            "(?<=.*)Literal\[\d+\](?=.*)": "Literal",  # Maybe int?!
            "^Callable\[\.\.\., *?Any\]$|^Callable\[\[Any\], *?Any\]$|^Callable[[Named(x, Any)], Any]$": "Callable",
            "^Iterator[Any]$": "Iterator",
            "^OrderedDict[Any, *?Any]$": "OrderedDict",
            "^Counter[Any]$": "Counter",
            "(?<=.*)Match[Any](?<=.*)": "Match",
        }

        for t_alias in type_aliases:
            if regex.search(regex.compile(t_alias), t):
                t = regex.sub(regex.compile(t_alias), type_aliases[t_alias], t)
        return t

    def run(self):
        files_stats = list_files(self.filestat_folder, ".json")
        files_a = list(map(lambda file: file.split("/")[3], files_stats))
        files_predictions = list_files(self.tc_results_folder, ".json")
        files_b = list(map(lambda file: file.split("/")[3], files_predictions))

        files = []
        # print(files_stats)
        for file in files_a:
            # if file in files_predictions:
            if file in files_b:
                files.append(file)
        # print(files)
        if platform == "win32":
            # print("currently running on a windows machine")
            files = [file.replace("\\", "/") for file in files]
        if self.limit == -1 or self.limit > len(files):
            limit = len(files)
        else:
            limit = self.limit
        # start_t = time.time()
        # jobs = cpu_count()
        # start = 0
        # ParallelExecutor(n_jobs=jobs)(total=limit)(
        #     delayed(self.evaluate_predictions)(file)
        #     for i, file in enumerate(files[start:limit], start=start)
        # )
        # print(
        #     "Finished processing %d files in %s "
        #     % (limit, str(timedelta(seconds=time.time() - start_t)))
        # )
        # Single run

        for i in tqdm(range(limit)):
            file = files[i]
            self.evaluate_predictions(file)

        self.write_type_info()
        self.write_result()

    def write_result(self):
        path = "evaluations/" + self.name
        if not os.path.isdir(path):
            os.mkdir(path)
        results = json.dumps(self.result, indent=4)
        write_file_strong(path + "/results.json", results)

    def write_type_info(self):
        path = "evaluations/" + self.name
        if not os.path.isdir(path):
            os.mkdir(path)
        type_info = json.dumps(self.type_info, indent=4)
        write_file_strong(path + "/type_info.json", type_info)

    def evaluate_predictions(self, file):

        with open(f"{self.filestat_folder}{file}", "r") as f:
            predictions = json.loads(f.read())
        try:
            with open(f"{self.tc_results_folder}{file}", "r") as f:
                errors = json.loads(f.read())
        except:
            return
        predictionElements = predictions["predictionElements"]
        line_numbers = []
        if errors and errors[0] and errors[0][0]:
            for error in errors[0]:
                line_numbers.append(error[1])

        for element in predictionElements:
            self.result["evaluation"]["total"] = self.result["evaluation"]["total"] + 1
            sanitized_type = self.resolve_type_alias(element["original_type"])
            if "builtins." in sanitized_type:
                sanitized_type = sanitized_type.split("builtins.")[1]
                if sanitized_type == element["predicted_type"]:
                    element["original_type"] = sanitized_type
                    element["match_case"] = "match"

            # add to total
            self.result["evaluation"][element["type"]]["match_types"][
                element["match_case"]
            ]["total"] = (
                self.result["evaluation"][element["type"]]["match_types"][
                    element["match_case"]
                ]["total"]
                + 1
            )
            # add to errors
            if line_numbers:
                if str(element["line_number"]) in line_numbers:
                    self.result["evaluation"][element["type"]]["match_types"][
                        element["match_case"]
                    ]["errors"] = (
                        self.result["evaluation"][element["type"]]["match_types"][
                            element["match_case"]
                        ]["errors"]
                        + 1
                    )

            # add count of original and prediction types
            original = element["original_type"]
            prediction = element["predicted_type"]
            originals = self.type_info["type_info"][element["type"]]["match_types"][
                element["match_case"]
            ]["original_types"]
            predictions = self.type_info["type_info"][element["type"]]["match_types"][
                element["match_case"]
            ]["predicted_types"]
            found_original = False
            found_prediction = False
            if originals:
                for i, el in enumerate(originals):
                    # print(el)
                    if el[0] == original:
                        self.type_info["type_info"][element["type"]]["match_types"][
                            element["match_case"]
                        ]["original_types"][i] = (el[0], el[1] + 1)
                        found_original = True
                        break
            if original and (not originals or not found_original):
                newType = (original, 1)
                self.type_info["type_info"][element["type"]]["match_types"][
                    element["match_case"]
                ]["original_types"].append(newType)
            if predictions:
                for i, el in enumerate(predictions):
                    if el[0] == prediction:
                        self.type_info["type_info"][element["type"]]["match_types"][
                            element["match_case"]
                        ]["predicted_types"][i] = (el[0], el[1] + 1)
                        found_prediction = True
                        break
            if not predictions or not found_prediction:
                newType = (prediction, 1)
                self.type_info["type_info"][element["type"]]["match_types"][
                    element["match_case"]
                ]["predicted_types"].append(newType)
