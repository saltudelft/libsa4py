from typing import Union, Dict, Tuple, List, Optional
from collections import Counter
from itertools import chain
from libsa4py.nl_preprocessing import NLPreprocessor
from libsa4py import PY_TYPING_MOD, PY_COLLECTION_MOD
import libcst as cst
import libcst.matchers as match
import re
import regex


class CommentAndDocStringRemover(cst.CSTTransformer):
    """
    It removes comments and docstrings and replaces them with [comment] and [docstring] special tokens
    """

    def leave_Expr(self, original_node: cst.Expr, updated_node: cst.Expr) -> Union[cst.BaseSmallStatement,
                                                                                   cst.RemovalSentinel]:
        if match.matches(original_node, match.Expr(value=match.SimpleString())):
            return updated_node.with_changes(value=cst.SimpleString(value='"""[docstring]"""'))
        else:
            return updated_node

    def leave_Comment(self, original_node: cst.Comment, updated_node: cst.Comment):
        return updated_node.with_changes(value="#[comment]")


class StringRemover(cst.CSTTransformer):
    """
    It removes string literals and replaces them with [string] special token
    """

    def leave_SimpleString(self, original_node: cst.SimpleString, updated_node: cst.SimpleString):
        return updated_node.with_changes(
            value="\"[string]\"") if updated_node.value != '"""[docstring]"""' else updated_node

    def leave_FormattedStringText(self, original_node: cst.FormattedString, updated_node: cst.FormattedString):
        return updated_node.with_changes(value=" [string] ")


class NumberRemover(cst.CSTTransformer):
    """
    It removes numeric literals and replaces them with [number] special token
    """

    def leave_Float(self, original_node: cst.Float, updated_node: cst.Float):
        return cst.SimpleString(value="\"[number]\"")

    def leave_Integer(self, original_node: cst.Integer, updated_node: cst.Integer):
        return cst.SimpleString(value="\"[number]\"")

    def leave_Imaginary(self, original_node: cst.Imaginary, updated_node: cst.Imaginary):
        return cst.SimpleString(value="\"[number]\"")


class TypeAnnotationRemover(cst.CSTTransformer):
    """
    It removes type annotations from a source code
    """

    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef) -> Union[
        cst.BaseStatement,
        cst.RemovalSentinel]:
        return updated_node.with_changes(returns=None) if original_node.returns is not None else updated_node

    def leave_Param(self, original_node: cst.Param, updated_node: cst.Param) -> Union[cst.Param,
                                                                                      cst.MaybeSentinel,
                                                                                      cst.RemovalSentinel]:
        return updated_node.with_changes(annotation=None) if original_node.annotation is not None else updated_node

    def leave_AnnAssign(self, original_node: cst.AnnAssign, updated_node: cst.AnnAssign) -> Union[
        cst.BaseSmallStatement,
        cst.RemovalSentinel]:
        # It handles a special case where a type-annotated variable has not initialized, e.g. foo: str
        # This case will be converted to foo = ... so that nodes traversal won't encounter exceptions later on
        if match.matches(original_node,
                         match.AnnAssign(target=match.Name(value=match.DoNotCare()),
                         annotation=match.Annotation(annotation=match.DoNotCare()), value=None)):
            updated_node = cst.Assign(targets=[cst.AssignTarget(target=original_node.target)], value=cst.Ellipsis())
        # Handles type-annotated class attributes that has not been initialized, e.g. self.foo: str
        elif match.matches(original_node, match.AnnAssign(target=match.Attribute(value=match.DoNotCare()),
                                                          annotation=match.Annotation(annotation=match.DoNotCare()),
                                                          value=None)):
            updated_node = cst.Assign(targets=[cst.AssignTarget(target=original_node.target)], value=cst.Ellipsis())
        else:
            updated_node = cst.Assign(targets=[cst.AssignTarget(target=original_node.target)], value=original_node.value)
        return updated_node


class TypeAdder(cst.CSTTransformer):
    """
    It replaces identifiers in a module with their type annotations if any
    Also, it propagates types of a function parameters in the function body and module-level constants
    """

    def __init__(self, module_type_annot: Dict[Tuple, Tuple[str, str]]):
        self.cls_stack: List[str] = []
        self.fn_stack: List[str] = []
        self.module_type_annot = module_type_annot
        self.__no_name_validation()

    def __no_name_validation(self):
        """
        It turns off validation of identifier names in LibCST
        """
        from libcst._nodes.expression import Name
        Name._validate = lambda x: "No validation for Name node"

    def visit_ClassDef(self, node: cst.ClassDef):
        self.cls_stack.append(node.name.value)

    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef):
        self.cls_stack.pop()
        return updated_node

    def visit_FunctionDef(self, node: cst.FunctionDef):
        self.fn_stack.append(node.name.value)

    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef):

        ret_type = self.module_type_annot[(self.cls_stack[-1] if len(self.cls_stack) > 0 else None,
                                           self.fn_stack[-1], None)][0]
        self.fn_stack.pop()
        if ret_type != '':
            return updated_node.with_changes(name=cst.Name(value=f"${ret_type}$"))
        else:
            return updated_node

    def leave_Name(self, original_node: cst.Name, updated_node: cst.Name):

        def extract_module_var_type(module_type_annot: Dict[Tuple, Tuple[str, str]]):
            if (None, None, original_node.value) in module_type_annot:  # Skips imported module names
                if module_type_annot[(None, None, original_node.value)][0] != '':
                    return module_type_annot[(None, None, original_node.value)][0]

        name_type = None

        # Adds types of class variables, function parameters and function variables
        if len(self.cls_stack) > 0:
            if (self.cls_stack[-1], self.fn_stack[-1] if len(self.fn_stack) > 0 else None, original_node.value) in \
                    self.module_type_annot:  # skips classes' identifiers
                if self.module_type_annot[(self.cls_stack[-1], self.fn_stack[-1] if len(self.fn_stack) > 0 else None,
                                           original_node.value)][0] != '':
                    name_type = self.module_type_annot[(self.cls_stack[-1],
                                                        self.fn_stack[-1] if len(self.fn_stack) > 0 else None,
                                                        original_node.value)][0]
            else:  # module-level variables (constants) in a function
                name_type = extract_module_var_type(self.module_type_annot)
        else:  # module-level variables (constants)
            name_type = extract_module_var_type(self.module_type_annot)

        return updated_node.with_changes(value=f"${name_type}$") if name_type is not None else updated_node


# This class is written by Georgios Gousios (GitHub: @gousiosg)
class SpaceAdder(cst.CSTTransformer):
    """
    Blindly adds spaces around all possible tokens. This is to help tokenization.
    """

    def __init__(self):
        self.visited_name = False
        self.last_visited_name = ''

    def leave_Annotation(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_before_indicator=cst.SimpleWhitespace(' '),
            whitespace_after_indicator=cst.SimpleWhitespace(' ')
        )

    def leave_Arg(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after_arg=cst.SimpleWhitespace(' '),
            whitespace_after_star=cst.SimpleWhitespace(' ')
        )

    def leave_Asynchronous(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' ')
        )

    def leave_Await(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after_await=cst.SimpleWhitespace(' ')
        )

    def leave_Call(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after_func=cst.SimpleWhitespace(' '),
            whitespace_before_args=cst.SimpleWhitespace(' ')
        )

    def leave_CompFor(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_before=cst.SimpleWhitespace(' '),
            whitespace_after_for=cst.SimpleWhitespace(' '),
            whitespace_before_in=cst.SimpleWhitespace(' '),
            whitespace_after_in=cst.SimpleWhitespace(' ')
        )

    def leave_CompIf(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_before=cst.SimpleWhitespace(' '),
            whitespace_before_test=cst.SimpleWhitespace(' ')
        )

    def leave_ConcatenatedString(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_between=cst.SimpleWhitespace(' ')
        )

    def leave_DictComp(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_before_colon=cst.SimpleWhitespace(' '),
            whitespace_after_colon=cst.SimpleWhitespace(' ')
        )

    def leave_DictElement(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_before_colon=cst.SimpleWhitespace(' '),
            whitespace_after_colon=cst.SimpleWhitespace(' ')
        )

    def leave_FormattedStringExpression(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_before_expression=cst.SimpleWhitespace(' '),
            whitespace_after_expression=cst.SimpleWhitespace(' ')
        )

    def leave_LeftCurlyBrace(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' ')
        )

    def leave_LeftParen(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' ')
        )

    def leave_LeftSquareBracket(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' ')
        )

    def leave_Param(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after_param=cst.SimpleWhitespace(' '),
            whitespace_after_star=cst.SimpleWhitespace(' ')
        )

    def leave_RightCurlyBrace(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_RightParen(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_RightSquareBracket(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_StarredDictElement(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_before_value=cst.SimpleWhitespace(' ')
        )

    def leave_StarredElement(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_before_value=cst.SimpleWhitespace(' ')
        )

    def leave_Subscript(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after_value=cst.SimpleWhitespace(' ')
        )

    def leave_Add(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_AddAssign(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_AssignEqual(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_before=cst.SimpleWhitespace(' '),
            whitespace_after=cst.SimpleWhitespace(' ')
        )

    def leave_BaseAugOp(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' '),
        )

    def leave_BaseBinaryOp(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' '),
        )

    def leave_BaseBooleanOp(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' '),
        )

    def leave_BaseCompOp(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' '),
        )

    def leave_BaseUnaryOp(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' '),
        )

    def leave_BitAnd(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' '),
        )

    def leave_BitAndAssign(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' '),
        )

    def leave_BitInvert(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' ')
        )

    def leave_BitOr(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' '),
        )

    def leave_BitOrAssign(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_BitXor(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_BitXorAssign(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_Colon(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_Comma(self, node: cst.Comma, updated_node: cst.Comma):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_Divide(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_DivideAssign(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_Dot(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' '),
        )

    def leave_Equal(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before = cst.SimpleWhitespace(' '),
        )

    def leave_FloorDivide(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_FloorDivideAssign(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_GreaterThan(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_GreaterThanEqual(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_In(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_Is(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_IsNot(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_LeftShift(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_LeftShiftAssign(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_LessThan(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_LessThanEqual(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_MatrixMultiply(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_MatrixMultiplyAssign(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_Minus(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' ')
        )

    def leave_Modulo(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_ModuloAssign(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_Multiply(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_MultiplyAssign(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_Not(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' ')
        )

    def leave_NotEqual(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_NotIn(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_between=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_Or(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_And(self, original_node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' ')
        )

    def leave_Plus(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' ')
        )

    def leave_Power(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_PowerAssign(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_RightShift(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_RightShiftAssign(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_Semicolon(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_Subtract(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_SubtractAssign(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after=cst.SimpleWhitespace(' '),
            whitespace_before=cst.SimpleWhitespace(' ')
        )

    def leave_AsName(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_before_as=cst.SimpleWhitespace(' '),
            whitespace_after_as=cst.SimpleWhitespace(' ')
        )

    def leave_Assert(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after_assert=cst.SimpleWhitespace(' ')
        )

    def leave_AssignTarget(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_before_equal=cst.SimpleWhitespace(' '),
            whitespace_after_equal=cst.SimpleWhitespace(' ')
        )

    def leave_ClassDef(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after_class=cst.SimpleWhitespace(' '),
            whitespace_after_name=cst.SimpleWhitespace(' '),
            whitespace_before_colon=cst.SimpleWhitespace(' ')
        )

    def leave_Decorator(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after_at=cst.SimpleWhitespace(' '),
            trailing_whitespace=cst.SimpleWhitespace(' ')
        )

    def leave_Del(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after_del=cst.SimpleWhitespace(' ')
        )

    def leave_Else(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_before_colon=cst.SimpleWhitespace(' ')
        )

    def leave_ExceptHandler(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after_except=cst.SimpleWhitespace(' '),
            whitespace_before_colon=cst.SimpleWhitespace(' ')
        )

    def leave_Finally(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_before_colon=cst.SimpleWhitespace(' ')
        )

    def leave_For(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after_for=cst.SimpleWhitespace(' '),
            whitespace_before_in=cst.SimpleWhitespace(' '),
            whitespace_after_in=cst.SimpleWhitespace(' '),
            whitespace_before_colon=cst.SimpleWhitespace(' ')
        )

    def leave_FunctionDef(self, original_node, updated_node):
        return updated_node.with_changes(
            whitespace_after_def=cst.SimpleWhitespace(' '),
            whitespace_after_name=cst.SimpleWhitespace(' '),
            whitespace_before_params=cst.SimpleWhitespace(' '),
            whitespace_before_colon=cst.SimpleWhitespace(' ')
        )

    def leave_Global(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after_global=cst.SimpleWhitespace(' ')
        )

    def leave_If(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_before_test=cst.SimpleWhitespace(' '),
            whitespace_after_test=cst.SimpleWhitespace(' ')
        )

    def leave_Import(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after_import=cst.SimpleWhitespace(' ')
        )

    def leave_ImportAlias(self, node, updated_node):
        return updated_node.with_changes(

        )

    def leave_ImportFrom(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after_from=cst.SimpleWhitespace(' '),
            whitespace_before_import=cst.SimpleWhitespace(' '),
            whitespace_after_import=cst.SimpleWhitespace(' ')
        )

    def leave_Nonlocal(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after_nonlocal=cst.SimpleWhitespace(' ')
        )

    def leave_Raise(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after_raise=cst.SimpleWhitespace(' ')
        )

    def leave_Return(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after_return=cst.SimpleWhitespace(' ')
        )

    def leave_Try(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_before_colon=cst.SimpleWhitespace(' ')
        )

    def leave_While(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after_while=cst.SimpleWhitespace(' '),
            whitespace_before_colon=cst.SimpleWhitespace(' ')
        )

    def leave_With(self, node, updated_node):
        return updated_node.with_changes(
            whitespace_after_with=cst.SimpleWhitespace(' '),
            whitespace_before_colon=cst.SimpleWhitespace(' ')
        )

    # This method is added to remove space from type annotations as it becomes problematic
    # when tokenizing and creating an aligned output sequence
    def leave_Name(self, original_node: cst.Name, updated_node: cst.Name):
        if re.match(r"^\$.+\$$", original_node.value):
            return updated_node.with_changes(value=original_node.value.replace(" ", ""))
        else:
            return original_node


class TypeQualifierResolver(cst.CSTTransformer):
    """
    It resolves qualified names for types, e.g. t.List -> typing.List
    """

    METADATA_DEPENDENCIES = (cst.metadata.QualifiedNameProvider,)

    def __init__(self):
        self.type_annot_visited: bool = False
        self.parametric_type_annot_visited: bool = False
        self.last_visited_name: cst.Name = None
        self.q_names_cache: Dict[Tuple[str, cst.metadata.QualifiedNameSource]] = {}

    def visit_Annotation(self, node: cst.Annotation):
        if not match.matches(node, match.Annotation(annotation=match.OneOf(
                match.Name(value='None'), match.List(elements=[])))):
            self.type_annot_visited = True

    def leave_Annotation(self, original_node: cst.Annotation, updated_node: cst.Annotation):
        if self.type_annot_visited:
            self.type_annot_visited = False
            if self.parametric_type_annot_visited:
                self.parametric_type_annot_visited = False
                q_name, _ = self.__get_qualified_name(original_node.annotation.value)
                if q_name is not None:
                    return updated_node.with_changes(annotation=cst.Subscript(value=self.__name2annotation(q_name).annotation,
                                             slice=updated_node.annotation.slice))
            else:
                q_name, _ = self.__get_qualified_name(original_node.annotation)
                if q_name is not None:
                    return updated_node.with_changes(annotation=self.__name2annotation(q_name).annotation)

        return original_node

    def visit_Subscript(self, node: cst.Subscript):
        if self.type_annot_visited:
            self.parametric_type_annot_visited = True

    def leave_SubscriptElement(self, original_node: cst.SubscriptElement,
                               updated_node: cst.SubscriptElement):
        if self.type_annot_visited and self.parametric_type_annot_visited:
            if match.matches(original_node, match.SubscriptElement(slice=match.Index(value=match.Subscript()))):
                q_name, _ = self.__get_qualified_name(original_node.slice.value.value)
                if q_name is not None:
                    return updated_node.with_changes(slice=cst.Index(value=cst.Subscript(value=self.__name2annotation(q_name).annotation,
                                                                 slice=updated_node.slice.value.slice)))
            elif match.matches(original_node, match.SubscriptElement(slice=match.Index(value=match.Ellipsis()))):
                # TODO: Should the original node be returned?!
                return updated_node.with_changes(slice=cst.Index(value=cst.Ellipsis()))
            elif match.matches(original_node, match.SubscriptElement(slice=match.Index(value=match.SimpleString(value=match.DoNotCare())))):
                return updated_node.with_changes(slice=cst.Index(value=updated_node.slice.value))
            elif match.matches(original_node, match.SubscriptElement(slice=match.Index(value=match.Name(value='None')))):
                return original_node
            elif match.matches(original_node, match.SubscriptElement(slice=match.Index(value=match.List()))):
                return updated_node.with_changes(slice=cst.Index(value=updated_node.slice.value))
            else:
                q_name, _ = self.__get_qualified_name(original_node.slice.value)
                if q_name is not None:
                    return updated_node.with_changes(slice=cst.Index(value=self.__name2annotation(q_name).annotation))

        return original_node

    def leave_Element(self, original_node: cst.Element, updated_node: cst.Element):
        if self.type_annot_visited:
            q_name, _ = self.__get_qualified_name(original_node.value)
            return updated_node.with_changes(value=self.__name2annotation(q_name).annotation)
        else:
            return original_node

    def visit_Name(self, node: cst.Name):
        if self.type_annot_visited:
            self.last_visited_name = node

    def __get_qualified_name(self, node):
        q = list(self.get_metadata(cst.metadata.QualifiedNameProvider, node))
        if len(q) != 0:
            q_name, q_src = q[0].name, q[0].source
            if re.match(r'^\.+.+', q_name):
                q_name = re.sub(re.compile(r'^\.+(.+)'), r'\1', q_name)

            if (self.last_visited_name.value, q_src) not in self.q_names_cache:
                self.q_names_cache[(self.last_visited_name.value, q_src)] = q_name

            return q_name, q_src
        else:
            return None, None

    def __name2annotation(self, type_name: str):
        """
        Converts Name nodes to valid annotation nodes
        """
        try:
            return match.extract(cst.parse_module("x: %s=None" % type_name).body[0].body[0],
                         match.AnnAssign(target=match.Name(value=match.DoNotCare()),
                                         annotation=match.SaveMatchedNode(match.DoNotCare(), "type")))['type']
        except cst._exceptions.ParserSyntaxError:
            # To handle a bug in LibCST's scope provider where a local name shadows a type annotation with the same name
            if (self.last_visited_name.value, cst.metadata.QualifiedNameSource.IMPORT) in self.q_names_cache:
                return match.extract(cst.parse_module("x: %s=None" % self.q_names_cache[(self.last_visited_name.value,
                                cst.metadata.QualifiedNameSource.IMPORT)]).body[0].body[0],
                                 match.AnnAssign(target=match.Name(value=match.DoNotCare()),
                                             annotation=match.SaveMatchedNode(match.DoNotCare(), "type")))['type']
            else:
                return match.extract(cst.parse_module("x: %s=None" % self.last_visited_name.value).body[0].body[0],
                                 match.AnnAssign(target=match.Name(value=match.DoNotCare()),
                                                 annotation=match.SaveMatchedNode(match.DoNotCare(), "type")))['type']


class ParametricTypeDepthReducer(cst.CSTTransformer):
    def __init__(self, max_annot_depth=2):
        self.max_annot_depth = max_annot_depth
        self.max_annot = 0
        self.current_annot_depth = 0

    def visit_Subscript(self, node):
        self.current_annot_depth += 1
        if self.max_annot < self.current_annot_depth:
            self.max_annot += 1

    def leave_Subscript(self, original_node, updated_node):
        self.current_annot_depth -= 1
        return updated_node

    def leave_SubscriptElement(self, original_node, updated_node):
        if self.max_annot > self.max_annot_depth and self.current_annot_depth == self.max_annot_depth:
            self.max_annot -= 1
            return updated_node.with_changes(slice=cst.Index(value=cst.Name(value='Any')))
        else:
            return updated_node


class TypeApplier(cst.CSTTransformer):
    """
    It applies (inferred) type annotations to a source code file.
    Specifically, it applies the type of arguments, return types, and variables' type.
    """

    METADATA_DEPENDENCIES = (cst.metadata.ScopeProvider, cst.metadata.QualifiedNameProvider)

    def __init__(self, f_processeed_dict: dict, apply_nlp: bool=True):
        self.f_processed_dict = f_processeed_dict
        self.cls_visited: List[Tuple[dict, Counter]] = []
        self.fn_visited: List[Tuple[dict, Counter]] = []

        self.last_visited_assign_t_name = None
        self.last_visited_assign_t_count = 0
        self.lambda_d = 0

        self.all_applied_types = set()

        if apply_nlp:
            self.nlp_p = NLPreprocessor().process_identifier
        else:
            self.nlp_p = lambda x: x

    def __get_fn(self, f_node: cst.FunctionDef) -> dict:
        if len(self.cls_visited) != 0:
            fns = self.cls_visited[-1][0]['funcs']
        else:
            fns = self.f_processed_dict['funcs']

        for fn in fns:
            if fn['q_name'] == self.__get_qualified_name(f_node.name) and \
                    set(list(fn['params'].keys())) == set(self.__get_fn_params(f_node.params)):
                return fn

    def __get_fn_param_type(self, param_name: str):
        fn_param_type = self.fn_visited[-1][0]['params'][self.nlp_p(param_name)]
        if fn_param_type != "":
            fn_param_type_resolved = self.resolve_type_alias(fn_param_type)
            fn_param_type = self.__name2annotation(fn_param_type_resolved)
            if fn_param_type is not None:
                self.all_applied_types.add((fn_param_type_resolved, fn_param_type))
                return fn_param_type

    def __get_cls(self, cls: cst.ClassDef) -> dict:
        for c in self.f_processed_dict['classes']:
            if c['q_name'] == self.__get_qualified_name(cls.name):
                return c

    def __get_fn_vars(self, var_name: str) -> dict:
        if var_name in self.fn_visited[-1][0]['variables']:
            if self.fn_visited[-1][0]['variables'][var_name] != "":
                return self.fn_visited[-1][0]['variables'][var_name]

    def __get_fn_params(self, fn_params: cst.Parameters):
        p_names: List[str] = []
        kwarg = [fn_params.star_kwarg] if fn_params.star_kwarg is not None else []
        stararg = [fn_params.star_arg] if match.matches(fn_params.star_arg, match.Param(
            name=match.Name(value=match.DoNotCare()))) else []
        for p in list(fn_params.params) + list(fn_params.kwonly_params) + list(fn_params.posonly_params) + stararg + kwarg:
            p_names.append(self.nlp_p(p.name.value))
        return p_names

    def __get_cls_vars(self, var_name: str) -> dict:
        if var_name in self.cls_visited[-1][0]['variables']:
            return self.cls_visited[-1][0]['variables'][var_name]

    def __get_mod_vars(self):
        return self.f_processed_dict['variables']

    def __get_var_type_assign_t(self, var_name: str):
        t: str = None
        if len(self.cls_visited) != 0:
            if len(self.fn_visited) != 0:
                # A class method's variable
                if self.fn_visited[-1][1][var_name] == self.last_visited_assign_t_count:
                    t = self.__get_fn_vars(self.nlp_p(var_name))
            else:
                # A class variable
                if self.cls_visited[-1][1][var_name] == self.last_visited_assign_t_count:
                    t = self.__get_cls_vars(self.nlp_p(var_name))
        elif len(self.fn_visited) != 0:
            # A module function's variable
            if self.fn_visited[-1][1][var_name] == self.last_visited_assign_t_count:
                t = self.__get_fn_vars(self.nlp_p(var_name))
        else:
            # A module's variables
            t = self.__get_mod_vars()[self.nlp_p(var_name)]
        return t

    def __get_var_type_an_assign(self, var_name: str):
        if len(self.cls_visited) != 0:
            if len(self.fn_visited) != 0:
                # A class method's variable
                t = self.__get_fn_vars(self.nlp_p(var_name))
            else:
                # A class variable
                t = self.__get_cls_vars(self.nlp_p(var_name))
        elif len(self.fn_visited) != 0:
            # A module function's variable
            t = self.__get_fn_vars(self.nlp_p(var_name))
        else:
            # A module's variables
            t = self.__get_mod_vars()[self.nlp_p(var_name)]
        return t

    def __get_var_names_counter(self, node, scope):
        vars_name = match.extractall(node, match.OneOf(match.AssignTarget(target=match.SaveMatchedNode(
            match.Name(value=match.DoNotCare()), "name")), match.AnnAssign(target=match.SaveMatchedNode(
            match.Name(value=match.DoNotCare()), "name"))))
        return Counter([n['name'].value for n in vars_name if isinstance(self.get_metadata(cst.metadata.ScopeProvider,
                                                                                           n['name']), scope)])

    def visit_ClassDef(self, node: cst.ClassDef):
        self.cls_visited.append((self.__get_cls(node),
                                 self.__get_var_names_counter(node, cst.metadata.ClassScope)))

    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef):
        self.cls_visited.pop()
        return updated_node

    def visit_FunctionDef(self, node: cst.FunctionDef):
        self.fn_visited.append((self.__get_fn(node),
                                self.__get_var_names_counter(node, cst.metadata.FunctionScope)))

    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef):
        fn_ret_type = self.fn_visited[-1][0]['ret_type']
        self.fn_visited.pop()
        if fn_ret_type != "":
            fn_ret_type_resolved = self.resolve_type_alias(fn_ret_type)
            fn_ret_type = self.__name2annotation(fn_ret_type_resolved)
            if fn_ret_type is not None:
                self.all_applied_types.add((fn_ret_type_resolved, fn_ret_type))
                return updated_node.with_changes(returns=fn_ret_type)

        return updated_node

    def visit_Lambda(self, node: cst.Lambda):
        self.lambda_d += 1

    def leave_Lambda(self, original_node: cst.Lambda, updated_node: cst.Lambda):
        self.lambda_d -= 1
        return original_node

    def leave_SimpleStatementLine(self, original_node: cst.SimpleStatementLine,
                                  updated_node: cst.SimpleStatementLine):
        if match.matches(original_node, match.SimpleStatementLine(body=[match.Assign(targets=[match.AssignTarget(
                target=match.Name(value=match.DoNotCare()))])])):
            t = self.__get_var_type_assign_t(original_node.body[0].targets[0].target.value)

            if t is not None:
                t_annot_node_resolved = self.resolve_type_alias(t)
                t_annot_node = self.__name2annotation(t_annot_node_resolved)
                if t_annot_node is not None:
                    self.all_applied_types.add((t_annot_node_resolved, t_annot_node))
                    return updated_node.with_changes(body=[cst.AnnAssign(
                        target=original_node.body[0].targets[0].target,
                        value=original_node.body[0].value,
                        annotation=t_annot_node,
                        equal=cst.AssignEqual(whitespace_after=original_node.body[0].targets[0].whitespace_after_equal,
                                            whitespace_before=original_node.body[0].targets[0].whitespace_before_equal))]
                    )
        elif match.matches(original_node, match.SimpleStatementLine(body=[match.AnnAssign(target=match.Name(value=match.DoNotCare()))])):
            t = self.__get_var_type_an_assign(original_node.body[0].target.value)
            if t is not None:
                t_annot_node_resolved = self.resolve_type_alias(t)
                t_annot_node = self.__name2annotation(t_annot_node_resolved)
                if t_annot_node is not None:
                    self.all_applied_types.add((t_annot_node_resolved, t_annot_node))
                    return updated_node.with_changes(body=[cst.AnnAssign(
                        target=original_node.body[0].target,
                        value=original_node.body[0].value,
                        annotation=t_annot_node,
                        equal=original_node.body[0].equal)])

        return original_node

    def leave_Param(self, original_node: cst.Param, updated_node: cst.Param):
        if self.lambda_d == 0:
            fn_param_type = self.__get_fn_param_type(original_node.name.value)
            if fn_param_type is not None:
                return updated_node.with_changes(annotation=fn_param_type)

        return original_node

    def visit_AssignTarget(self, node: cst.AssignTarget):
        if match.matches(node, match.AssignTarget(target=match.Name(value=match.DoNotCare()))):
            if self.last_visited_assign_t_name == self.__get_qualified_name(node.target):
                self.last_visited_assign_t_count += 1
            elif self.last_visited_assign_t_count == 0:
                self.last_visited_assign_t_count = 1
            else:
                self.last_visited_assign_t_count = 1
            self.last_visited_assign_t_name = self.__get_qualified_name(node.target)

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module):
        return updated_node.with_changes(body=self.__get_required_imports() + list(updated_node.body))

    # TODO: Check the imported modules before adding new ones
    def __get_required_imports(self):
        def find_required_modules(all_types):
            req_mod = set()
            for _, a_node in all_types:
                m = match.findall(a_node.annotation, match.Attribute(value=match.DoNotCare(), attr=match.DoNotCare()))
                if len(m) != 0:
                    for i in m:
                        req_mod.add([n.value for n in match.findall(i, match.Name(value=match.DoNotCare()))][0])
            return req_mod

        req_imports = []
        all_req_mods = find_required_modules(self.all_applied_types)
        all_type_names = set(chain.from_iterable(map(lambda t: regex.findall(r"\w+", t[0]), self.all_applied_types)))

        typing_imports = PY_TYPING_MOD & all_type_names
        collection_imports = PY_COLLECTION_MOD & all_type_names

        if len(typing_imports) > 0:
            req_imports.append(cst.SimpleStatementLine(body=[cst.ImportFrom(module=cst.Name(value="typing"),
                                                                 names=[cst.ImportAlias(name=cst.Name(value=t),
                                                                                        asname=None) for t in
                                                                        typing_imports]),]))
        if len(collection_imports) > 0:
            req_imports.append(cst.SimpleStatementLine(body=[cst.ImportFrom(module=cst.Name(value="collections"),
                                                       names=[cst.ImportAlias(name=cst.Name(value=t), asname=None) \
                                                              for t in collection_imports]),]))
        if len(all_req_mods) > 0:
            for mod_name in all_req_mods:
                req_imports.append(cst.SimpleStatementLine(body=[cst.Import(names=[cst.ImportAlias(name=cst.Name(value=mod_name),
                                                                                    asname=None)])]))

        return req_imports

    def __name2annotation(self, type_name: str):
        ext_annot = lambda t: match.extract(cst.parse_module("x: %s=None" % t).body[0].body[0],
                                            match.AnnAssign(target=match.Name(value=match.DoNotCare()),
                                                            annotation=match.SaveMatchedNode(match.DoNotCare(), "type")))['type']
        try:
            return ext_annot(type_name)
        except cst._exceptions.ParserSyntaxError:
            return None

    def __get_qualified_name(self, node) -> Optional[str]:
        q_name = list(self.get_metadata(cst.metadata.QualifiedNameProvider, node))
        return q_name[0].name if len(q_name) != 0 else None

    def resolve_type_alias(self, t: str):
        type_aliases = {'^{}$|^Dict$|(?<=.*)Dict\[\](?<=.*)|(?<=.*)Dict\[Any, *?Any\](?=.*)|^Dict\[unknown, *Any\]$': 'dict',
                        '^Set$|(?<=.*)Set\[\](?<=.*)|^Set\[Any\]$': 'set',
                        '^Tuple$|(?<=.*)Tuple\[\](?<=.*)|^Tuple\[Any\]$|(?<=.*)Tuple\[Any, *?\.\.\.\](?=.*)|^Tuple\[unknown, *?unknown\]$|^Tuple\[unknown, *?Any\]$|(?<=.*)tuple\[\](?<=.*)': 'tuple',
                        '^Tuple\[(.+), *?\.\.\.\]$': r'Tuple[\1]',
                        '\\bText\\b': 'str',
                        '^\[\]$|(?<=.*)List\[\](?<=.*)|^List\[Any\]$|^List$': 'list',
                        '^\[{}\]$': 'List[dict]',
                        '(?<=.*)Literal\[\'.*?\'\](?=.*)': 'Literal',
                        '(?<=.*)Literal\[\d+\](?=.*)': 'Literal',  # Maybe int?!
                        '^Callable\[\.\.\., *?Any\]$|^Callable\[\[Any\], *?Any\]$|^Callable[[Named(x, Any)], Any]$': 'Callable',
                        '^Iterator[Any]$': 'Iterator',
                        '^OrderedDict[Any, *?Any]$': 'OrderedDict',
                        '^Counter[Any]$': 'Counter',
                        '(?<=.*)Match[Any](?<=.*)': 'Match',
                        '^\.(.+)': r'\1',
                        '(?<=.*)Optional\[\](?<=.*)': 'Optional'}
        for t_alias in type_aliases:
            if regex.search(regex.compile(t_alias), t):
                t = regex.sub(regex.compile(t_alias), type_aliases[t_alias], t)
        return t
