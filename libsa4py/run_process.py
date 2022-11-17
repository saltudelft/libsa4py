import subprocess


def run(
        cmd_args: List[str], timeout: Optional[int] = None
) -> Tuple[str, str, int]:
    process = subprocess.run(cmd_args, shell=False, capture_output=True, timeout=timeout)
    return process.stdout.decode(), process.stderr.decode(), process.returncode
