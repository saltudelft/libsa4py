"""
Helper functions to use pyre in the pipeline
"""

from typing import Optional
from pathlib import Path
from subprocess import TimeoutExpired
from os.path import join, exists, isdir
from libcst.metadata.type_inference_provider import run_command, PyreData
import os
import shutil
import signal
import json
from libsa4py.utils import run
import subprocess
import re


def clean_watchman_config(project_path: str):
    # update the watchman config to the project
    dict = {"root": "."}
    if exists(join(project_path, '.watchmanconfig')):
        os.remove(join(project_path, '.watchmanconfig'))
        print(f"[WATCHMAN_CLEAN] config of {project_path} ")

    with open(join(project_path, '.watchmanconfig'), "w") as f:
        json.dump(dict, f)
        print(f"[WATCHMAN_WRITE] config of {project_path} ")



def start_watchman(project_path: str):
    # start watchman for the project
    stdout, stderr, r_code = run(
        "cd %s; watchman watch-project ." % project_path)


def pyre_server_init(project_path: str) -> int:
   # start pyre server
    stdout, stderr, r_code = run(
        "cd %s; pyre start" % project_path)
    print(f"[PYRE_SERVER] initialized at {project_path} ", stdout, stderr)
    # TODO: Raise an exception if the pyre server has not been started


def check_pyre_server(project_path: str):
    exist = False
    stdout, stderr, r_code = run("pyre servers")
    folder = r"%s" % project_path
    m = re.search(folder, stdout)
    if m is not None:
        exist = True
    return exist


def find_pyre_server(project_path: str) -> Optional[int]:
    try:
        with open(join(project_path, '.pyre', "server", "server.pid")) as pid_file:
            return int(pid_file.read())
    except (OSError, ValueError):
        print("Didn't find the pyre server in ", project_path)
        return None


def clean_pyre_config(project_path: str):
    # add pyre initiation file for the path
    dict = {
        "site_package_search_strategy": "pep561",
        "source_directories": [
            "."
        ],
        "typeshed": "/pyre-check/stubs/typeshed/typeshed",
        "workers": 64
    }

    if exists(join(project_path, '.pyre_configuration')):
        os.remove(join(project_path, '.pyre_configuration'))
        print(f"cleaned pyre config in {project_path} ")

    with open(join(project_path, '.pyre_configuration'), "w") as f:
        json.dump(dict, f)


def pyre_server_shutdown(project_path: str):
    # stop pyre server in the project path
    run("cd %s ; pyre stop" % project_path)
    print("Stopped pyre server in ", project_path)

def watchman_server_shutdown(project_path: str):
    # stop pyre server in the project path
    run("cd %s ;watchman watch-del ." % project_path)
    print("Stopped watchman server in ", project_path)


def pyre_kill_all_servers():
    run("pyre kill")
    print("Killed all instances of pyre's servers")

def watchman_kill_all_servers():
    run("watchman watch-del-all")
    print("Removed all watches and associated triggers.")


def pyre_query_types(project_path: str, file_path: str, timeout: int = 600) -> Optional[PyreData]:
    # pyre query for each file
    try:
        file_types = None
        stdout, stderr, r_code = run('''cd %s; pyre query "types(path='%s')"''' % (project_path,
                                                                                   str(Path(file_path).relative_to(
                                                                                       Path(project_path)))),
                                     timeout=timeout)
        if r_code == 0:
            file_types = json.loads(stdout)["response"][0]
        else:
            print(f"[PYRE_ERROR] p: {project_path}", stderr)
    except KeyError:
        print(f"[PYRE_ERROR] p: {project_path}", json.loads(stdout)['error'])
    except TimeoutExpired as te:
        print(f"[PYRE_TIMEOUT] p: {project_path}", te)
    finally:
        return file_types

def pyre_infer(project_path: str):
    # pyre infer for parameters and return types
    stdout, stderr, r_code = run(
        "cd %s; pyre infer -i" % project_path)
    print(f"[PYRE_INFER] started at {project_path} ", stdout, stderr)

def clean_config(project_path: str):
    # clean watchman and pyre configuration files
    # clean watchman
    if exists(join(project_path, '.watchmanconfig')):
        os.remove(join(project_path, '.watchmanconfig'))
        print(f"[WATCHMAN_CLEAN] config of {project_path} ")

    # clean pyre
    if exists(join(project_path, '.pyre_configuration')):
        os.remove(join(project_path, '.pyre_configuration'))
        print(f"[PYRE_CLEAN] config of {project_path} ")

    # clean pyre folder
    pyre_dir = join(project_path, '.pyre')
    if exists(pyre_dir) and isdir(pyre_dir):
        shutil.rmtree(pyre_dir)