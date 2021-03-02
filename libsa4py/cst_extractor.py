from libsa4py.cst_visitor import Visitor
from libsa4py.representations import ModuleInfo
from libsa4py.cst_transformers import TypeAdder, SpaceAdder, StringRemover, CommentAndDocStringRemover, NumberRemover,\
    TypeAnnotationRemover
from libsa4py.exceptions import ParseError

import libcst as cst


class Extractor:
    """
    Extracts data from a Python source code
    """

    @staticmethod
    def extract(program: str) -> dict:

        try:
            parsed_program = cst.parse_module(program)
        except Exception as e:
            raise ParseError(str(e))

        v: Visitor = Visitor()
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

        print(v_untyped)

        return ModuleInfo(v.imports, v.module_variables, v.cls_list, v.fns, v_untyped.code, v_typed.code).to_dict()
