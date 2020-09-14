from typing import Tuple, Union, List, Optional, Dict, Pattern, Match
from io import BytesIO

import libcst as cst
import libcst.matchers as match
import re
import docstring_parser
import json
import numpy as np

from tqdm import tqdm
from libsa4py.cst_visitor import ExtendedVisitorCST, VisitorCST
from libsa4py.representations import ModuleInfo, FunctionInfo
from libsa4py.cst_transformers import TypeAdder, SpaceAdder, StringRemover, CommentAndDocStringRemover, NumberRemover,\
    TypeAnnotationRemover
from libsa4py.nlp_preprocessing import NLPreprocessor
from libsa4py.extractor import Extractor, Function, tokenize
from libsa4py.exceptions import ParseError

NLP_P = NLPreprocessor()


class ExtendedExtractorCST:
    """
    Extracts data from a Python source code
    """

    @staticmethod
    def extract(program: str) -> dict:

        try:
            parsed_program = cst.parse_module(program)
        except Exception:
            raise ParseError()

        v: ExtendedVisitorCST = ExtendedVisitorCST()
        parsed_program.visit(v)

        # Transformers
        v_cm_doc = CommentAndDocStringRemover()
        v_str = StringRemover()
        v_num = NumberRemover()
        v_type = TypeAnnotationRemover()
        v_type_add = TypeAdder(v.module_all_annotations)
        v_space = SpaceAdder()

        v_untyped = parsed_program.visit(v_cm_doc)
        v_untyped = v_untyped.visit(v_str)
        v_untyped = v_untyped.visit(v_num)
        v_untyped = v_untyped.visit(v_type)

        # Replaces identifiers with their type annotations
        v_typed = v_untyped.visit(v_type_add)

        # Adding space for better tokenization
        v_untyped = v_untyped.visit(v_space)
        v_typed = v_typed.visit(v_space)

        return ModuleInfo(v.imports, v.module_variables, v.cls_list, v.fns, v_untyped.code, v_typed.code).to_dict()


class ExtractorCST:
    """
    Extract data from python source code

    Example usage:
    `
        with open("example.py") as file:
            program = file.read()

        fns = Extractor().extract(program)
    `
    """

    def extract_fn(self, func: FunctionInfo) \
            -> Function:
        # TODO: This can be generalized a bit more (to reduce code redundancy with extended superclass)

        function_name: str = self.extract_name(func)
        docstring: str = self.extract_docstring(func)
        (arg_names, arg_types) = self.extract_args(func)
        return_type: str = self.extract_return_type(func)
        exprs: List[str] = func.return_exprs

        docstring_descr: Dict[
            str, Union[Union[Optional[str], Dict[str, str]], Optional[str]]] = self.extract_docstring_descriptions(
            self.check_docstring(docstring))
        arg_descrs: List[str] = list(map(
            lambda arg_name: docstring_descr["params"][arg_name] if arg_name in docstring_descr['params'] else '',
            arg_names
        ))

        # print(arg_descrs)

        # print("arg_names", arg_names)
        args_occur = self.extract_args_ret_occur(func.node.body, arg_names, 5)
        # print("Args occur: ", args_occur)
        # print("###############################################################################")

        f: Function = Function(function_name, docstring, docstring_descr["function_descr"],
                               arg_names, arg_types, arg_descrs, args_occur,
                               return_type, exprs, docstring_descr["return_descr"], list(func.variables.keys()),
                               list(func.variables.values()))

        return f

    def extract_name(self, func: FunctionInfo) -> str:
        """Extract the name of the function"""
        return func.name

    def extract_docstring(self, func: FunctionInfo) -> str:
        """Extract the docstring from a function"""
        return func.docstring

    def pretty_print(self, node: Optional[cst.CSTNode]) -> str:
        """
        Given some AST type expression,
        pretty print the type so that it is readable
        """
        if node is None:
            return ""

        # Create module from single specified node
        module = cst.Module([node])

        # Convert the node to code format via the module's code property
        return module.code

    def extract_args(self, func: FunctionInfo) -> Tuple[List[str], List[str]]:
        """Extract the names and types of the function args"""
        return func.parameter_names, func.parameter_annotations

    def extract_return_type(self, func: FunctionInfo) -> str:
        """Extract the return type of the function"""
        return func.return_type

    def tokenize_func_stats(self, func):
        """
        A helper method to tokenize every statement in a method
        :return:
        """
        # TODO: This can be generalized a bit more from the originating superclass.
        stats_tokens = []
        ignore_toks = ['utf-8', '', ',']

        for c in func:
            line = cst.Module([c]).code.encode("utf-8")
            stats_tokens.append([tokval.rstrip() for _, tokval, _, _, _ in tokenize(BytesIO(line).readline) if
                                 tokval.rstrip() not in ignore_toks])

        return stats_tokens

    def extract_args_ret_occur(self, func_body, arg_names, win_size):
        """
        Extracts code occurrences of the to-be-typed program element.
        """
        # Due to LibCST conventions, we need to call the super method by taking
        # the body attribute of func_body again. This was overriden to preserve
        # generalization of extract function in ExtractorBase.
        return super().extract_args_ret_occur(func_body.body, arg_names, win_size)

    def extract(self, program: str) -> Tuple[List[Function], list]:
        """Extract useful data from python program"""
        try:
            self.asttok = cst.parse_module(program)
        except Exception as err:
            raise ParseError(err)

        v: VisitorCST = VisitorCST()
        self.asttok.visit(v)

        return list(map(lambda fn: self.extract_fn(fn), v.fns)), v.class_defs + v.imports


def merge_jsons_to_dict(json_files: list) -> dict:
    """
    Merges all the JSON files of projects into a dictionary
    """

    all_projects_dict = {'projects': {}}
    for f in tqdm(json_files, total=len(json_files)):
        with open(f, 'r') as json_f:
            try:
                d = json.load(json_f)
                all_projects_dict['projects'][list(d.keys())[0]] = d[list(d.keys())[0]]
            except json.JSONDecodeError as err:
                print("Could not parse file: ", f)

    return all_projects_dict


def extract_fns(projects: dict) -> list:
    """
    Extracts all the functions from the projects' dictionary in a format that can be converted to a dataframe
    """

    fns = []
    for p in tqdm(list(projects['projects'].keys()), total=len(projects['projects'].keys())):
        p_fns = {'author': '', 'repo': '', 'files': {}}
        p_fns['author'], p_fns['repo'] = p.split("/")
        for f in projects['projects'][p]['src_files'].keys():
            p_fns['files'][f] = {}
            p_fns['files'][f]['imports'] = [NLP_P.process_identifier(i) for i in
                                            projects['projects'][p]['src_files'][f]['imports']]
            cls_fns = [f for c in projects['projects'][p]['src_files'][f]['classes'] for f in c['funcs']]
            f_fns = projects['projects'][p]['src_files'][f]['funcs']
            p_fns['files'][f]['fns'] = f_fns + cls_fns
        for f in p_fns['files']:
            for fn in p_fns['files'][f]['fns']:
                fns.append([p_fns['author'], p_fns['repo'], f, fn['name'],
                            any(t for t in list(fn['params'].values())) or fn['ret_type'] != '',
                            fn['docstring']['long_descr'] if fn['docstring']['long_descr'] is not None else np.NaN,
                            fn['docstring']['func'] if fn['docstring']['func'] is not None else np.NaN,
                            str(list(fn['params'].keys())), str(list(fn['params'].values())),
                            str(list(fn['params_descr'].values())),
                            fn['ret_type'] if fn['ret_type'] != '' else np.NaN,
                            str(fn['ret_exprs']), str(list(fn['params_occur'].values())),
                            fn['docstring']['ret'] if fn['docstring']['ret'] is not None else np.NaN,
                            list(fn['variables'].keys()), list(fn['variables'].values()),
                            str(p_fns['files'][f]['imports']), len(list(fn['params'].keys())),
                            len([t for t in list(fn['params'].values()) if t != ''])])

    return fns
