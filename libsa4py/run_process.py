import subprocess
from typing import Dict, List, Mapping, Optional, Sequence, Tuple


def run(
        cmd_args: List[str], timeout: Optional[int] = None
) -> Tuple[str, str, int]:
    process = subprocess.run(cmd_args, shell=True, capture_output=True, timeout=timeout)
    return process.stdout.decode(), process.stderr.decode(), process.returncode
