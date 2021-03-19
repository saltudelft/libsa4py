"""
Helper functions to use pyre in the pipeline
"""

from typing import Optional
from pathlib import Path
from libcst.metadata.type_inference_provider import run_command, PyreData
import os
import signal
import json


def pyre_server_init(project_path: str):
    stdout, stderr, r_code = run_command("cd %s; echo -ne '.\n' | pyre init; pyre start" % project_path)


def find_pyre_server(project_path: str) -> Optional[int]:
    try:
        with open(os.path.join(project_path, '.pyre', "server", "server.pid")) as pid_file:
            return int(pid_file.read())
    except (OSError, ValueError):
        print("Didn't find the pyre server in ", project_path)
        return None


def pyre_server_shutdown(project_path: str):
    server_pid = find_pyre_server(project_path)
    if server_pid is not None:
        os.kill(server_pid, signal.SIGKILL)
        print("Stopped pyre server with pid ", server_pid)


def pyre_kill_all_servers():
    run_command("pyre kill")
    print("Killed all instances of pyre's servers")


def pyre_query_types(project_path: str, file_path: str) -> Optional[PyreData]:
    stdout, stderr, r_code = run_command('''cd %s; pyre query "types(path='%s')"''' % (project_path,
                                         str(Path(file_path).relative_to(Path(project_path)))))
    if r_code == 0:
        try:
            return json.loads(stdout)["response"][0]
        except KeyError:
            print("PYRE_ERROR", json.loads(stdout)['error'])
            return None
    else:
        print("PYRE_ERROR: ", stderr)
        return None
