from typing import Union, Dict, Tuple, List
import libcst as cst
import libcst.matchers as match
import re


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

    def __init__(self, module_type_annot: Dict[Tuple, str]):
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
                                           self.fn_stack[-1], None)]
        self.fn_stack.pop()
        if ret_type != '':
            return updated_node.with_changes(name=cst.Name(value=f"${ret_type}$"))
        else:
            return updated_node

    def leave_Name(self, original_node: cst.Name, updated_node: cst.Name):

        def extract_module_var_type(module_type_annot: Dict[Tuple, str]):
            if (None, None, original_node.value) in module_type_annot:  # Skips imported module names
                if module_type_annot[(None, None, original_node.value)] != '':
                    return module_type_annot[(None, None, original_node.value)]

        name_type = None

        # Adds types of class variables, function parameters and function variables
        if len(self.cls_stack) > 0:
            if (self.cls_stack[-1], self.fn_stack[-1] if len(self.fn_stack) > 0 else None, original_node.value) in \
                    self.module_type_annot:  # skips classes' identifiers
                if self.module_type_annot[(self.cls_stack[-1], self.fn_stack[-1] if len(self.fn_stack) > 0 else None,
                                           original_node.value)] != '':
                    name_type = self.module_type_annot[(self.cls_stack[-1],
                                                        self.fn_stack[-1] if len(self.fn_stack) > 0 else None,
                                                        original_node.value)]
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
        return updated_node.with_changes()

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
