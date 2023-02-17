import shutil
from typing import List, Tuple
from tqdm import tqdm
from joblib import Parallel
from os.path import join, isdir
from tempfile import NamedTemporaryFile
from pathlib import Path
import time
import os
import signal
import json


def text_progessbar(seq, total=None):
    step = 1
    tick = time.time()
    while True:
        time_diff = time.time() - tick
        avg_speed = time_diff / step
        total_str = 'of %n' % total if total else ''
        print('step', step, '%.2f' % time_diff, 'avg: %.2f iter/sec' % avg_speed, total_str)
        step += 1
        yield next(seq)


all_bar_funcs = {
    'tqdm': lambda args: lambda x: tqdm(x, **args),
    'txt': lambda args: lambda x: text_progessbar(x, **args),
    'False': lambda args: iter,
    'None': lambda args: iter,
}


def ParallelExecutor(use_bar='tqdm', **joblib_args):
    def aprun(bar=use_bar, **tq_args):
        def tmp(op_iter):
            if str(bar) in all_bar_funcs.keys():
                bar_func = all_bar_funcs[str(bar)](tq_args)
            else:
                raise ValueError("Value %s not supported as bar type" % bar)
            return Parallel(**joblib_args)(bar_func(op_iter))

        return tmp

    return aprun


# This is a legacy DESTRUCTIVE function that should be removed
# def filter_directory(directory: str, extension: str = '.py') -> str:
#     """
#     Delete all files within the given directory with filenames not ending in the given extension
#     """
#     for root, dirs, files in os.walk(directory):
#         [os.remove(os.path.join(root, fi)) for fi in files if not fi.endswith(extension)]
#
#     return directory


def list_files(directory: str, file_ext: str = ".py") -> Tuple[list, int]:
    """
    List all files in the given directory (recursively)
    """
    filenames = []
    dir_size = 0

    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.endswith(file_ext):
                filenames.append(os.path.join(root, filename))
                dir_size += Path(os.path.join(root, filename)).stat().st_size

    return filenames, dir_size


def read_file(filename: str) -> str:
    """
    Open a file and return its contents as a string
    """
    with open(filename) as file:
        return file.read()

def write_file(filename: str, content: str):
    with open(filename, 'w') as file:
        file.write(content)

def mk_dir_cp_file(src_path: str, dest_path: str):
    """
    Creates directories in the destination if not exists and copy the given file
    """
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    shutil.copy(src_path, dest_path)

def save_json(filename: str, dict_obj: dict):
    """
    Dumps a dict object into a JSON file
    """
    with open(filename, 'w') as json_f:
        json.dump(dict_obj, json_f, indent=4)


def load_json(filename: str) -> dict:
    """
    Loads a json file into a dictionary
    """
    with open(filename, 'r') as json_f:
        return json.load(json_f)


def find_repos_list(projects_path: str) -> List[dict]:
    """
    Finds a list of author/repo from a Python dataset.
    """

    repos_list: List[dict] = []

    for author in os.listdir(projects_path):
        if not author.startswith(".") and isdir(join(projects_path, author)):
            for repo in os.listdir(join(projects_path, author)):
                if isdir(join(projects_path, author, repo)):
                    repos_list.append({"author": author, "repo": repo})

    return repos_list



def mk_dir_not_exist(path: str):
    if not isdir(path):
        os.mkdir(path)


def create_tmp_file(suffix: str):
    """
    It creates a temporary file.
    NOTE: the temp file should be deleted manually after creation.
    """
    return NamedTemporaryFile(mode="w", delete=False, suffix=suffix)


def delete_tmp_file(tmp_f: NamedTemporaryFile):
    try:
        os.unlink(tmp_f.name)
    except TypeError:
        print("Couldn't delete ", tmp_f.name)


def write_to_tmp_file(tmp_f: NamedTemporaryFile, text: str):
    tmp_f.write(text)
    #tmp_f.close()
    return tmp_f
