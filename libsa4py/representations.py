from typing import Dict, List, Tuple
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
        self.q_name = None
        # Line, Column no. for the start and end of the function
        self.ln_col: Tuple[Tuple[int, int], Tuple[int, int]] = None
        self.parameters: Dict[str, str] = {}
        self.parameters_occur: Dict[str, list] = {}
        self.params_descr: Dict[str, str] = {}
        self.return_exprs = []
        self.return_type = ""
        self.docstring: Dict[str, str] = {}
        self.variables: Dict[str, str] = {}  # Variable names
        self.variables_occur: Dict[str, list] = {}
        self.variables_ln: Dict[str, Tuple[Tuple[int, int], Tuple[int, int]]]= {}
        self.node = None

    def to_dict(self):
        return {"name": self.name, "q_name": self.q_name, "fn_lc": self.ln_col, "params": self.parameters,
                "ret_exprs": self.return_exprs, "params_occur": self.parameters_occur, "ret_type": self.return_type,
                "variables": self.variables, "fn_var_occur": self.variables_occur, "fn_var_ln": self.variables_ln,
                "params_descr": self.params_descr, "docstring": self.docstring}

    def from_dict(self, fn_dict_repr: dict):
        self.name = fn_dict_repr['name']
        self.q_name = fn_dict_repr['q_name']
        self.ln_col = (tuple(fn_dict_repr['fn_lc'][0]), tuple(fn_dict_repr['fn_lc'][1]))
        self.parameters = fn_dict_repr['params']
        self.parameters_occur = fn_dict_repr['params_occur']
        self.params_descr = fn_dict_repr['params_descr']
        self.return_exprs = fn_dict_repr['ret_exprs']
        self.return_type = fn_dict_repr['ret_type']
        self.variables = fn_dict_repr['variables']
        self.variables_occur = fn_dict_repr['fn_var_occur']
        self.variables_ln = {v: (tuple(l[0]), tuple(l[1])) for v, l in fn_dict_repr['fn_var_ln'].items()}
        self.docstring = fn_dict_repr['docstring']

        return self

    def __eq__(self, other_func_info_obj: 'FunctionInfo'):
        return other_func_info_obj.name == self.name and \
               other_func_info_obj.q_name == self.q_name and \
               other_func_info_obj.ln_col == self.ln_col and \
               other_func_info_obj.parameters == self.parameters and \
               other_func_info_obj.parameters_occur == self.parameters_occur and \
               other_func_info_obj.params_descr == self.params_descr and \
               other_func_info_obj.return_exprs == self.return_exprs and \
               other_func_info_obj.return_type == self.return_type and \
               other_func_info_obj.variables == self.variables and \
               other_func_info_obj.variables_occur == self.variables_occur and \
               other_func_info_obj.variables_ln == self.variables_ln and \
               other_func_info_obj.docstring == self.docstring


class ClassInfo:
    """
    Holds data related to a class
    """

    def __init__(self):
        self.name: str = ''
        self.q_name: str = ''
        # Line, Column no. for the start and end of the class
        self.ln_col: Tuple[Tuple[int, int], Tuple[int, int]] = None
        self.variables: Dict[str, str] = {}
        self.variables_use_occur: Dict[str, list] = {}
        self.variables_ln: Dict[str, Tuple[Tuple[int, int], Tuple[int, int]]] = {}
        self.funcs: List[FunctionInfo] = []

    def to_dict(self) -> dict:
        return {"name": self.name, "q_name": self.q_name, "cls_lc": self.ln_col, "variables": self.variables,
                "cls_var_occur": self.variables_use_occur, "cls_var_ln": self.variables_ln,
                "funcs": [f.to_dict() for f in self.funcs]}

    def from_dict(self, cls_repr_dict: dict):
        self.name = cls_repr_dict['name']
        self.q_name = cls_repr_dict['q_name']
        self.ln_col = (tuple(cls_repr_dict['cls_lc'][0]), tuple(cls_repr_dict['cls_lc'][1]))
        self.variables = cls_repr_dict['variables']
        self.variables_use_occur = cls_repr_dict['cls_var_occur']
        self.variables_ln = {v: (tuple(l[0]), tuple(l[1])) for v, l in cls_repr_dict['cls_var_ln'].items()}
        self.funcs = [FunctionInfo(f['name']).from_dict(f) for f in cls_repr_dict['funcs']]

        return self

    def __eq__(self, other_class_info_obj: 'ClassInfo'):
        return other_class_info_obj.name == self.name and \
               other_class_info_obj.q_name == self.q_name and \
               other_class_info_obj.ln_col == self.ln_col and \
               other_class_info_obj.variables == self.variables and \
               other_class_info_obj.variables_use_occur == self.variables_use_occur and \
               other_class_info_obj.variables_ln == self.variables_ln and \
               other_class_info_obj.funcs == self.funcs


class ModuleInfo:
    """
    This class holds data that is extracted from a source code file.
    """

    def __init__(self, import_names: list, variables: Dict[str, str], var_occur: Dict[str, List[list]], var_ln,
                 classes: List[ClassInfo], funcs: List[FunctionInfo], untyped_seq: str, typed_seq: str,
                 no_types_annot: Dict[str, int], type_annot_cove: float):
        self.import_names = import_names
        self.variables = variables
        self.var_occur = var_occur
        self.var_ln = var_ln
        self.classes = classes
        self.funcs = funcs
        self.untyped_seq = untyped_seq
        self.typed_seq = typed_seq
        self.no_types_annot = no_types_annot
        self.type_annot_cove = type_annot_cove

    def to_dict(self) -> dict:
        return {"untyped_seq": self.untyped_seq,
                "typed_seq": self.typed_seq,
                "imports": self.import_names,
                "variables": self.variables,
                "mod_var_occur": self.var_occur,
                "mod_var_ln": self.var_ln,
                "classes": [c.to_dict() for c in self.classes],
                "funcs": [f.to_dict() for f in self.funcs],
                "set": None,
                "tc": (False, None),
                "no_types_annot": self.no_types_annot,
                "type_annot_cove": self.type_annot_cove}

    @classmethod
    def from_dict(cls, mod_dict_repr: dict):
        return cls(mod_dict_repr['imports'], mod_dict_repr['variables'], mod_dict_repr['mod_var_occur'],
                   {v: (tuple(l[0]), tuple(l[1])) for v, l in mod_dict_repr['mod_var_ln'].items()},
                   [ClassInfo().from_dict(c) for c in mod_dict_repr['classes']],
                   [FunctionInfo(f['name']).from_dict(f) for f in mod_dict_repr['funcs']],
                   mod_dict_repr['untyped_seq'], mod_dict_repr['typed_seq'], mod_dict_repr['no_types_annot'],
                   mod_dict_repr['type_annot_cove'])

    def __eq__(self, other_module_info_obj: 'ModuleInfo'):
        return other_module_info_obj.import_names == self.import_names and \
               other_module_info_obj.variables == self.variables and \
               other_module_info_obj.var_occur == self.var_occur and \
               other_module_info_obj.var_ln == self.var_ln and \
               other_module_info_obj.classes == self.classes and \
               other_module_info_obj.funcs == self.funcs and \
               other_module_info_obj.untyped_seq == self.untyped_seq and \
               other_module_info_obj.typed_seq == self.typed_seq and \
               other_module_info_obj.no_types_annot == self.no_types_annot and \
               other_module_info_obj.type_annot_cove == self.type_annot_cove


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