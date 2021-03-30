"""
Helper functions to use pyre in the pipeline
"""

from typing import Optional
from pathlib import Path
from subprocess import TimeoutExpired
from os.path import join, exists
from libcst.metadata.type_inference_provider import run_command, PyreData
import os
import shutil
import signal
import json


def pyre_server_init(project_path: str):
    stdout, stderr, r_code = run_command("cd %s; echo -ne '.\n' | pyre init; pyre start" % project_path)
    print(f"[PYRE_SERVER] initialized at {project_path} ", stdout, stderr)
    #TODO: Raise an exception if the pyre server has not been started


def find_pyre_server(project_path: str) -> Optional[int]:
    try:
        with open(join(project_path, '.pyre', "server", "server.pid")) as pid_file:
            return int(pid_file.read())
    except (OSError, ValueError):
        print("Didn't find the pyre server in ", project_path)
        return None


def clean_pyre_config(project_path: str):
    if exists(join(project_path, '.pyre_configuration')):
        os.remove(join(project_path, '.pyre_configuration'))
        print(f"[PYRE_CLEAN] config of {project_path} ")

    if exists(join(project_path, '.pyre')):
        shutil.rmtree(join(project_path, '.pyre'))
        print(f"[PYRE_CLEAN] pyre folder of {project_path} ")


def pyre_server_shutdown(project_path: str):
    server_pid = find_pyre_server(project_path)
    if server_pid is not None:
        os.kill(server_pid, signal.SIGKILL)
        print("Stopped pyre server with pid ", server_pid)


def pyre_kill_all_servers():
    run_command("pyre kill")
    print("Killed all instances of pyre's servers")


def pyre_query_types(project_path: str, file_path: str, timeout: int = 600) -> Optional[PyreData]:
    try:
        file_types = None
        stdout, stderr, r_code = run_command('''cd %s; pyre query "types(path='%s')"''' % (project_path,
                                             str(Path(file_path).relative_to(Path(project_path)))),
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
