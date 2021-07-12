"""
Contains helper functions to facilitate certain minor tasks
"""

import libcst as cst
import libcst.matchers as match


def extract_names_from_type_annot(type_annot: str):
    """
    Extracts all the names/identifiers from a type annotation
    """

    return [n.value for n in match.findall(cst.parse_expression(type_annot), match.Name(value=match.DoNotCare()))]
