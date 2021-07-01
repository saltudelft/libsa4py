"""
This module contains helper classes to statically type-check source files using mypy.
It is written and inspired by:
https://github.com/typilus/typilus/blob/e2aec24d94f10e58b3542c04be7fcf5640a1762b/exp/type_check/tcmanager.py
MIT License
"""

from abc import ABC, abstractmethod
from os.path import dirname, basename
from typing import Tuple, Union
from collections import Counter, namedtuple
import toml
import os
import subprocess
import pkg_resources


fields = ("no_type_errs", "no_files", "no_ignored_errs", "no_warnings", "err_breakdown")
ParsedResult = namedtuple("ParsedResult", fields, defaults=(None,) * len(fields))


class CustomError(Exception):
    pass


class TypeCheckingTooLong(CustomError):
    def __init__(self):
        super().__init__("Type checking file taking too long!")


class CustomWarning(Exception):
    pass


class FailToTypeCheck(CustomWarning):
    def __init__(self):
        super().__init__("File containing type errors!")


class OutputParseError(CustomError):
    def __init__(self):
        super().__init__("Failed to parse type checking output!")


class TCManager(ABC):
    def __init__(self, tc, timeout):
        self._timeout = timeout
        #self._logger = logging.getLogger(__name__)
        errcodes = toml.load(pkg_resources.resource_filename(__name__, 'tc_errcodes.toml'))[tc]
        self._all_errcodes = errcodes["all"]
        self._inc_errcodes = errcodes["included"]

    # def _check_file_existence(self, fpath):
    #     if not isfile(fpath):
    #         raise FileNonExisting

    # def _check_py3_compatibility(self, fpath):
    #     if subprocess.run(["python3", "-m", "py_compile", fpath]).returncode != 0:
    #         raise Py3Incompatible

    # def _check_basics(self, fpath):
    #     self._check_file_existence(fpath)
    #     self._check_py3_compatibility(fpath)

    @abstractmethod
    def _build_tc_cmd(self, fpath):
        pass

    def _type_check(self, fpath):
        try:
            cwd = os.getcwd()
            os.chdir(dirname(fpath))
            result = subprocess.run(
                self._build_tc_cmd(basename(fpath)),
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )
            retcode = result.returncode
            outlines = result.stdout.splitlines()
            return retcode, outlines
        except subprocess.TimeoutExpired:
            raise TypeCheckingTooLong
        finally:
            os.chdir(cwd)

    @abstractmethod
    def _check_tc_outcome(self, returncode, outlines):
        pass

    def light_assess(self, fpath):
        print(f"Light assessing {fpath}.")
        try:
            #self._check_basics(fpath)
            retcode, outlines = self._type_check(fpath)
            self._check_tc_outcome(retcode, outlines)
            print("Passed the light assessment.")
            return True
        except CustomError as e:
            print(str(e))
            return False
        except CustomWarning as e:
            print(str(e))
            return False

    @abstractmethod
    def _parse_tc_output(self, returncode, outlines):
        pass

    @abstractmethod
    def _report_errors(self, parsed_result):
        pass

    def heavy_assess(self, fpath):
        try:
            retcode, outlines = self._type_check(fpath)
            parsed_result = self._parse_tc_output(retcode, outlines)
            self._report_errors(parsed_result)
            return parsed_result
        except CustomError as e:
            print(str(e))


class MypyManager(TCManager):
    def _build_tc_cmd(self, fpath):
        # Mypy needs a flag to display the error codes
        return ["mypy", "--show-error-codes", "--no-incremental", "--cache-dir=/dev/null", fpath]

    def _check_tc_outcome(self, _, outlines):
        if any(l.endswith(err) for l in outlines for err in self._inc_errcodes):
            raise FailToTypeCheck

    def _parse_tc_output(self, retcode, outlines):
        last_line = outlines[-1]
        err_breakdown = None
        if retcode == 0:
            if not last_line.startswith("Success: "):
                raise OutputParseError
            no_type_errs = 0
            no_files = next(int(w) for w in last_line.split() if w.isdigit())
            no_ignored_errs = 0
        else:
            c = Counter(
                err for l in outlines for err in self._inc_errcodes if l.endswith(err)
            )
            err_breakdown = dict(c)
            no_type_errs = sum(c.values())
            if last_line.startswith("Found ") and last_line.endswith(" source file)"):
                numbers = [int(s) for s in last_line.split() if s.isdigit()]
                no_errs = numbers[0]
                no_files = numbers[1]
                no_ignored_errs = no_errs - no_type_errs
            else:
                raise OutputParseError

        return ParsedResult(
            no_type_errs, no_files, no_ignored_errs, err_breakdown=err_breakdown
        )

    def _report_errors(self, parsed_result):
        print(
            f"Produced {parsed_result.no_type_errs} type error(s) in {parsed_result.no_files} file(s)."
        )
        if parsed_result.err_breakdown:
            print(f"Error breaking down: {parsed_result.err_breakdown}.")


def type_check_single_file(f_path: str, tc: TCManager) -> Tuple[bool, Union[int, None]]:
    try:
        no_t_err = tc.heavy_assess(f_path)
        if no_t_err is not None:
            return (True, 0) if no_t_err.no_type_errs == 0 else (False, no_t_err.no_type_errs)
        else:
            return False, None
    except IndexError:
        print(f"f: {f_path} - No output from Mypy!")
        return False, None
