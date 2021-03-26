from typing import Dict, List, Optional, Pattern, Match
from libsa4py.exceptions import OutputSequenceException

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
        self.params_descr: Dict[str, str] = {}
        self.return_exprs = []
        self.return_type = ""
        self.docstring: Dict[str, str] = {}
        self.variables: Dict[str, str] = {}  # Variable names
        self.variables_occur: Dict[str, list] = {}
        self.node = None

    def to_dict(self):
        return {"name": self.name, "params": self.parameters, "ret_exprs": self.return_exprs,
                "params_occur": self.parameters_occur, "ret_type": self.return_type, "variables": self.variables,
                "fn_var_occur": self.variables_occur, "params_descr": self.params_descr, "docstring": self.docstring}

    def from_dict(self, fn_dict_repr: dict):
        self.name = fn_dict_repr['name']
        self.parameters = fn_dict_repr['params']
        self.parameters_occur = fn_dict_repr['params_occur']
        self.params_descr = fn_dict_repr['params_descr']
        self.return_exprs = fn_dict_repr['ret_exprs']
        self.return_type = fn_dict_repr['ret_type']
        self.variables = fn_dict_repr['variables']
        self.variables_occur = fn_dict_repr['fn_var_occur']
        self.docstring = fn_dict_repr['docstring']

        return self

    def __eq__(self, other_func_info_obj: 'FunctionInfo'):
        return other_func_info_obj.name == self.name and \
               other_func_info_obj.parameters == self.parameters and \
               other_func_info_obj.parameters_occur == self.parameters_occur and \
               other_func_info_obj.params_descr == self.params_descr and \
               other_func_info_obj.return_exprs == self.return_exprs and \
               other_func_info_obj.return_type == self.return_type and \
               other_func_info_obj.variables == self.variables and \
               other_func_info_obj.variables_occur == self.variables_occur and \
               other_func_info_obj.docstring == self.docstring

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
        self.variables_use_occur: Dict[str, list] = {}
        self.funcs: List[FunctionInfo] = []

    def to_dict(self) -> dict:
        return {"name": self.name, "variables": self.variables, "cls_var_occur": self.variables_use_occur,
                "funcs": [f.to_dict() for f in self.funcs]}

    def from_dict(self, cls_repr_dict: dict):
        self.name = cls_repr_dict['name']
        self.variables = cls_repr_dict['variables']
        self.variables_use_occur = cls_repr_dict['cls_var_occur']
        self.funcs = [FunctionInfo(f['name']).from_dict(f) for f in cls_repr_dict['funcs']]

        return self

    def __eq__(self, other_class_info_obj: 'ClassInfo'):
        return other_class_info_obj.name == self.name and \
               other_class_info_obj.variables == self.variables and \
               other_class_info_obj.variables_use_occur == self.variables_use_occur and \
               other_class_info_obj.funcs == self.funcs

    def get_type_annot_cove(self) -> float:
        return ((sum([1 for k, v in self.variables.items() if v]) / len(self.variables.keys()) if len(self.variables.keys()) else 0) +
               (sum([f.get_type_annot_cove() for f in self.funcs]) / len(self.funcs) if len(self.funcs) else 0)) / 2


class ModuleInfo:
    """
    This class holds data that is extracted from a source code file.
    """

    def __init__(self, import_names: list, variables: Dict[str, str], var_occur: Dict[str, List[list]],
                 classes: List[ClassInfo], funcs: List[FunctionInfo], untyped_seq: str, typed_seq: str):
        self.import_names = import_names
        self.variables = variables
        self.var_occur = var_occur
        self.classes = classes
        self.funcs = funcs
        self.untyped_seq = untyped_seq
        self.typed_seq = typed_seq

    def to_dict(self) -> dict:
        return {"untyped_seq": self.untyped_seq,
                "typed_seq": self.typed_seq,
                "imports": self.import_names, "variables": self.variables, "mod_var_occur": self.var_occur,
                "classes": [c.to_dict() for c in self.classes],
                "funcs": [f.to_dict() for f in self.funcs],
                "set": None,
                "type_annot_cove": round(self.get_type_annot_cove(), 2)}

    @classmethod
    def from_dict(cls, mod_dict_repr: dict):
        return cls(mod_dict_repr['imports'], mod_dict_repr['variables'], mod_dict_repr['mod_var_occur'],
                   [ClassInfo().from_dict(c) for c in mod_dict_repr['classes']],
                   [FunctionInfo(f['name']).from_dict(f) for f in mod_dict_repr['funcs']],
                   mod_dict_repr['untyped_seq'], mod_dict_repr['typed_seq'])

    def __eq__(self, other_module_info_obj: 'ModuleInfo'):
        return other_module_info_obj.import_names == self.import_names and \
               other_module_info_obj.variables == self.variables and \
               other_module_info_obj.var_occur == self.var_occur and \
               other_module_info_obj.classes == self.classes and \
               other_module_info_obj.funcs == self.funcs and \
               other_module_info_obj.untyped_seq == self.untyped_seq and \
               other_module_info_obj.typed_seq == self.typed_seq

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