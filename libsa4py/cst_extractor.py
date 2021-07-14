from libsa4py.cst_visitor import Visitor
from libsa4py.representations import ModuleInfo, create_output_seq
from libsa4py.cst_transformers import TypeAdder, SpaceAdder, StringRemover, CommentAndDocStringRemover, NumberRemover,\
    TypeAnnotationRemover, TypeQualifierResolver
from libsa4py.nl_preprocessing import normalize_module_code
from libsa4py.exceptions import ParseError

import libcst as cst


class Extractor:
    """
    Extracts data from a Python source code
    """

    @staticmethod
    def extract(program: str,
                program_types: cst.metadata.type_inference_provider.PyreData = None,
                include_seq2seq: bool = True) -> ModuleInfo:
        try:
            parsed_program = cst.parse_module(program)
        except Exception as e:
            raise ParseError(str(e))

        # Resolves qualified names for a modules' type annotations
        program_tqr = cst.metadata.MetadataWrapper(parsed_program).visit(TypeQualifierResolver())

        v = Visitor()
        if program_types is not None:
            mw = cst.metadata.MetadataWrapper(program_tqr,
                                             cache={cst.metadata.TypeInferenceProvider: program_types})
            mw.visit(v)
        else:
            mw = cst.metadata.MetadataWrapper(program_tqr, cache={cst.metadata.TypeInferenceProvider: {'types':[]}})
            mw.visit(v)

        if include_seq2seq:
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

            return ModuleInfo(v.imports, v.module_variables, v.module_variables_use, v.module_vars_ln, v.cls_list, v.fns,
                              normalize_module_code(v_untyped.code), create_output_seq(normalize_module_code(v_typed.code)),
                              v.module_no_types, v.module_type_annot_cove)
        else:
            return ModuleInfo(v.imports, v.module_variables, v.module_variables_use, v.module_vars_ln, v.cls_list,
                              v.fns, "", "", v.module_no_types, v.module_type_annot_cove)
