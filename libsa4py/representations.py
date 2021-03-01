from typing import Dict, List, Union, Optional, Pattern, Match
from libsa4py.exceptions import OutputSequenceException
import docstring_parser
import re


# TODO: We might want to remove the node parameter. The reason why it is there is to facilitate for the
#       extract_args_ret_occur. However, combined with LibCST's parsing & matcher capabilities, we could instead
#       perform those steps in the Visitor (or some matcher) itself.
class FunctionInfo:
    """
    Class that holds parsed function information generated via a Visitor.
    Used as a data container for function information.
    """

    def __init__(self, name) -> None:
        self.name = name
        self.parameters: Dict[str, str] = {}
        self.parameters_occur: Dict[str, list] = {}
        self.return_exprs = []
        self.return_type = ""
        self.docstring = ""
        self.variables: Dict[str, str] = {}  # Variable names
        self.node = None

    def to_dict(self):
        return {**{"name": self.name, "params": self.parameters, "ret_exprs": self.return_exprs,
                   "params_occur": self.parameters_occur, "ret_type": self.return_type, "variables": self.variables,
                   **self.__get_params_descr()}}

    def __get_params_descr(self):
        params_descr = self.__extract_docstring_descriptions(self.docstring)
        return {"params_descr": {p: params_descr['params'][p] if p in params_descr['params'] else '' for p in
                                 self.parameters.keys()},
                "docstring": {"func": params_descr["function_descr"], "ret": params_descr["return_descr"],
                              "long_descr": params_descr["long_descr"]}}

    def __extract_docstring_descriptions(self, docstring: str) -> Dict[
        str, Union[Union[Optional[str], Dict[str, str]], Optional[str]]]:
        """Extract the return description from the docstring"""
        try:
            parsed_docstring: docstring_parser.parser.Docstring = docstring_parser.parse(docstring)

            descr_map: Dict[str, Union[Union[str, Dict[str, str]], Optional[str]], Optional[str]] = {
                "function_descr": parsed_docstring.short_description,
                "params": {},
                "return_descr": None,
                "long_descr": None}

            if parsed_docstring.returns is not None:
                descr_map["return_descr"] = parsed_docstring.returns.description

            if parsed_docstring.long_description is not None:
                descr_map['long_descr'] = parsed_docstring.long_description

            for param in parsed_docstring.params:
                descr_map["params"][param.arg_name] = param.description

            return descr_map
        except Exception:
            return {"function_descr": None, "params": {}, "return_descr": None, "long_descr": None}

    def __check_func_docstring(self, docstring: str) -> Optional[str]:
        """Check the docstring if it has a valid structure for parsing and returns a valid docstring."""
        dash_line_matcher: Pattern[str] = re.compile("\s*--+")
        param_keywords: List[str] = ["Parameters", "Params", "Arguments", "Args"]
        return_keywords: List[str] = ["Returns", "Return"]
        break_keywords: List[str] = ["See Also", "Examples"]

        convert_docstring: bool = False
        add_indent: bool = False
        add_double_colon: bool = False
        active_keyword: bool = False
        end_docstring: bool = False

        preparsed_docstring: str = ""
        lines: List[str] = docstring.split("\n")
        for line in lines:
            result: Optional[Match] = re.match(dash_line_matcher, line)
            if result is not None:
                preparsed_docstring = preparsed_docstring[:-1] + ":" + "\n"
                convert_docstring = True
            else:
                for keyword in param_keywords:
                    if keyword in line:
                        add_indent = True
                        active_keyword = True
                        break
                if not active_keyword:
                    for keyword in return_keywords:
                        if keyword in line:
                            add_indent = True
                            add_double_colon = True
                            active_keyword = True
                            break
                if not add_double_colon:
                    for keyword in break_keywords:
                        if keyword in line:
                            end_docstring = True
                            break
                if end_docstring:
                    break
                if active_keyword:
                    preparsed_docstring += line + "\n"
                    active_keyword = False
                elif add_double_colon:
                    preparsed_docstring += "\t" + line + ":\n"
                    add_double_colon = False
                elif add_indent:
                    line_parts = line.split(":")
                    if len(line_parts) > 1:
                        preparsed_docstring += "\t" + line_parts[0] + "(" + line_parts[1].replace(" ", "") + "):\n"
                    else:
                        preparsed_docstring += "\t" + line + "\n"
                else:
                    preparsed_docstring += line + "\n"

        if convert_docstring:
            return preparsed_docstring
        else:
            return

    def get_type_annot_cove(self) -> float:
        try:
            return (sum([1 for k, v in self.variables.items() if v] +
                        [1 for k, v in self.parameters.items() if v]) +
                    (1 if self.return_type else 0)) / (len(self.variables.keys()) +
                        (len(self.parameters.keys()) - 1 if 'self' in self.parameters.keys()
                             else len(self.parameters.keys())) + (1 if len(self.return_exprs) or
                                                                       self.return_type == "None" else 0))
        except ZeroDivisionError:
            # For functions with no parameters, variables and return
            return 0.0


class ClassInfo:
    """
    Holds data related to a class
    """

    def __init__(self):
        self.name: str = ''
        self.variables: Dict[str, str] = {}
        self.funcs: List[FunctionInfo] = []

    def to_dict(self) -> dict:
        return {"name": self.name, "variables": self.variables, "funcs": [f.to_dict() for f in self.funcs]}

    def get_type_annot_cove(self) -> float:
        return ((sum([1 for k, v in self.variables.items() if v]) / len(self.variables.keys()) if len(self.variables.keys()) else 0) +
               (sum([f.get_type_annot_cove() for f in self.funcs]) / len(self.funcs) if len(self.funcs) else 0)) / 2


class ModuleInfo:
    """
    This class holds data that is extracted from a source code file.
    """

    def __init__(self, import_names: list, variables: Dict[str, str], classes: List[ClassInfo],
                 funcs: List[FunctionInfo], untyped_seq: str, typed_seq: str):
        self.import_names = import_names
        self.variables = variables
        self.classes = classes
        self.funcs = funcs
        self.untyped_seq = untyped_seq
        self.typed_seq = typed_seq

    def to_dict(self) -> dict:
        return {"untyped_seq": ModuleInfo.normalize_module_code(self.untyped_seq),
                "typed_seq": create_output_seq(ModuleInfo.normalize_module_code(self.typed_seq)),
                "imports": self.import_names, "variables": self.variables,
                "classes": [c.to_dict() for c in self.classes],
                "funcs": [f.to_dict() for f in self.funcs],
                "set": None,
                "type_annot_cove": round(self.get_type_annot_cove(), 2)}

    @staticmethod
    def normalize_module_code(m_code: str) -> str:
        # New lines
        m_code = re.compile(r"\n").sub(r" [EOL] ", m_code)
        # white spaces
        m_code = re.compile(r"[ \t\n]+").sub(" ", m_code)

        # Replace comments, docstrings, numeric literals and string literals with special tokens
        special_tks = {"#[comment]": "[comment]", "\"\"\"[docstring]\"\"\"": "[docstring]", "\"[string]\"": "[string]",
                       "\"[number]\"": "[number]"}
        regex = re.compile("(%s)" % "|".join(map(re.escape, special_tks.keys())))
        m_code = regex.sub(lambda mo: special_tks[mo.string[mo.start():mo.end()]], m_code)

        return m_code.strip()

    def get_type_annot_cove(self):
        return ((sum([1 for k, v in self.variables.items() if v]) / len(self.variables.keys()) if len(self.variables.keys()) else 0) +
               (sum([c.get_type_annot_cove() for c in self.classes]) / len(self.classes) if len(self.classes) else 0) +
               (sum([f.get_type_annot_cove() for f in self.funcs]) / len(self.funcs) if len(self.funcs) else 0)) / 3


def create_output_seq(typed_seq: str, type_sep_symb="$") -> str:
    """
    It generates an output sequence for seq2seq representation.
    """

    output_seq = ""
    for token in typed_seq.split(" "):
        if token.startswith(type_sep_symb) and token.endswith(type_sep_symb):
            output_seq += token
            output_seq += " "
        else:
            output_seq += "0 "

    output_seq = output_seq.strip()
    validate_output_seq(typed_seq, output_seq)

    return output_seq


def validate_output_seq(typed_seq: str, output_seq: str, type_sep_symb="$"):
    """
    Validates whether the input and output sequence are aligned properly
    """

    typed_seq = typed_seq.split(" ")
    output_seq = output_seq.split(" ")

    for i, token in enumerate(typed_seq):
        if token.startswith(type_sep_symb) and token.endswith(type_sep_symb):
            if token != output_seq[i]:
                raise OutputSequenceException(token, output_seq[i])
        elif not (token.startswith(type_sep_symb) or token.endswith(type_sep_symb)):
            if output_seq[i] != '0':
                raise OutputSequenceException(token, output_seq[i])
        else:
            raise OutputSequenceException(token, output_seq[i])