from typing import List, Dict, Tuple, Union, Optional
from libsa4py.representations import FunctionInfo, ClassInfo
from libsa4py.nl_preprocessing import extract_docstring_descriptions
from libsa4py import DEV_TYPE_ANNOT, INF_TYPE_ANNOT, UNK_TYPE_ANNOT
import libcst as cst
import libcst.matchers as match
import re


class Visitor(cst.CSTVisitor):
    """
    This class performs light-weight static analysis on a source code file
    """

    METADATA_DEPENDENCIES = (cst.metadata.PositionProvider, cst.metadata.TypeInferenceProvider,
                             cst.metadata.QualifiedNameProvider)

    def __init__(self):
        super().__init__()

        # Note: This visitor visits children as well.
        # Stack for storing functions currently being explored
        self.stack: List[FunctionInfo] = []

        self.fns = []  # List of functions in a module
        # Statements in which a function's arguments may occur
        self.fn_may_args_var_use: List[list] = []

        # self.visited_class = False
        self.cls_stack: List[ClassInfo] = []
        self.cls_list: List[ClassInfo] = []
        self.cls_may_vars_use: List[list] = []

        self.module_variables: Dict[str, str] = {}
        self.module_variables_use: Dict[str, List[list]] = {}
        self.module_vars_ln: Dict[str, Tuple[Tuple[int, int], Tuple[int, int]]] = {}
        self.module_all_annotations: Dict[Tuple, Tuple[str, str]] = {}
        #self.module_pyre_inferred_types: List[str] = []
        self.module_type_annot_cove: float = 0.0
        self.module_no_types: Dict[str, int] = {'U': 0, 'D': 0, 'I': 0}

        # Visible types in a source code file
        self.class_defs = []
        self.imports = []  # Names of imports

        # Current stack depth specific variables for a function
        self.last_annotation = None  # Annotation for the previous parameter
        # Keep track of lambda depth in order not to assign parameters from lambda to outer function
        self.lambda_depth = 0

    def visit_ClassDef(self, node: cst.ClassDef):
        """
        Extracts locally user-defined classes.
        """

        cls = ClassInfo()
        cls.name = node.name.value

        self.cls_stack.append(cls)

    def leave_ClassDef(self, node: cst.ClassDef):

        cls = self.cls_stack.pop()
        cls.variables_use_occur = self.__find_args_vars_use(list(cls.variables.keys()), self.cls_may_vars_use)
        cls.q_name = self.__get_qualified_name(node.name)
        cls.ln_col = self.__get_line_column_no(node)
        self.cls_may_vars_use = []
        self.cls_list.append(cls)

    def visit_FunctionDef(self, node: cst.FunctionDef):
        """
        Visits a function and updates the current function stack to track parameters.
        """

        # Create function info representation for newly visited function
        func = FunctionInfo(node.name.value)  # Pass in function name
        func.node = node  # Update node
        func.q_name = self.__get_qualified_name(node.name)
        # Push function info on top of the stack, thus increasing stack
        # depth to account for the current function.
        self.stack.append(func)

    def leave_FunctionDef(self, node: cst.FunctionDef):
        """
        Leaves a function definition, and takes care of adding the function
        to the list of functions parameter.

        The function also takes care of resetting the necessary variables.
        """
        # Un-set last seen annotation
        self.last_annotation = None

        # Decrease stack depth of the current function
        fn = self.stack.pop()

        fn.ln_col = self.__get_line_column_no(fn.node)
        fn.docstring, params_descr = extract_docstring_descriptions(self.__extract_docstring(node))
        fn.params_descr = {p: params_descr[p] if p in params_descr else '' for p in fn.parameters.keys()}

        fn.parameters_occur = self.__find_args_vars_use(list(fn.parameters.keys()), self.fn_may_args_var_use, True)
        fn.variables_occur = self.__find_args_vars_use(list(fn.variables.keys()), self.fn_may_args_var_use)

        self.fn_may_args_var_use = []

        # Retrieve & update return type from returns annotation (if it exists)
        # If return annotation does not exist, it will resolve to 'None' and then an empty
        # string via the conversion method.
        fn.return_type = self.__convert_annotation(node.returns)

        if len(self.cls_stack) > 0:
            # Adds a class method
            self.cls_stack[-1].funcs.append(fn)
            self.module_all_annotations[(self.cls_stack[-1].name, fn.name, None)] = (fn.return_type, DEV_TYPE_ANNOT \
                if fn.return_type else UNK_TYPE_ANNOT)
        else:
            # Add a local function info to functions list
            self.fns.append(fn)
            self.module_all_annotations[(None, fn.name, None)] = (fn.return_type, DEV_TYPE_ANNOT \
                if fn.return_type else UNK_TYPE_ANNOT)

    def visit_Return(self, node):
        """
        Visits a return expression, and saves this return expression.
        """
        if self.lambda_depth == 0:
            # Parse return expression directly to the code representation.
            # TODO: Possibly alter this to further analyze the return statement.
            # TODO: This was simply done to conform to DLTPy's older implementation.
            parsed_return = self.__clean_string_whitespace(self.__convert_node_to_code(node))

            # Append return expression to last function in the stack (the one currently being explored)
            self.stack[-1].return_exprs.append(parsed_return)

    def visit_Param(self, node: cst.Param):
        """
        Visits a function parameter, and appends the parameter
        to the current function's parameter list.
        """
        if self.lambda_depth == 0:
            # Add parameter name & set last seen parameter to None
            self.stack[-1].parameters[node.name.value] = ''

        self.last_annotation = None

    def leave_Param(self, node: cst.Param):
        """
        Leaves a parameter definition. This essentially means that the
        parameter's annotation will have been processed.
        """
        if self.lambda_depth == 0:
            # Convert last annotation (which corresponds to this parameter)
            # to relevant format and append it to the parameter annotation list
            annotation_value = self.__convert_annotation(self.last_annotation)
            self.stack[-1].parameters[node.name.value] = annotation_value

            if len(self.cls_stack) > 0:
                self.module_all_annotations[(self.cls_stack[-1].name, self.stack[-1].name,
                                             node.name.value)] = (annotation_value, DEV_TYPE_ANNOT \
                    if annotation_value else UNK_TYPE_ANNOT)
            else:
                self.module_all_annotations[(None, self.stack[-1].name,
                                             node.name.value)] = (annotation_value, DEV_TYPE_ANNOT \
                    if annotation_value else UNK_TYPE_ANNOT)

        # Un-set last annotation
        self.last_annotation = None

    def visit_Annotation(self, node: cst.Annotation):
        """
        Visits an annotation; Updates the last seen annotation value.
        """
        # Update last annotation
        self.last_annotation = node

    def visit_ImportAlias(self, node: cst.ImportAlias):
        """
        Extracts imports.

        Even if an Import has no alias, the Import node will still have an ImportAlias
        with it's real name.
        """
        # Extract information from the Import Alias node.
        # Both the (real) import name and the alias are extracted.
        # Result is returned as a dictionary with a name:node KV pair,
        # and an alias:name KV pair if an alias is present.
        import_info = match.extract(node, match.ImportAlias(
            asname=match.AsName(  # Attempt to match alias
                name=match.Name(  # Check for alias name
                    value=match.SaveMatchedNode(  # Save the alias name
                        match.MatchRegex(r'(.)+'),  # Match any string literal
                        "alias"
                    )
                )
            ) | ~match.AsName(),
            # If there is no AsName, we should still match. We negate AsName to and OR to form a tautology.
            name=match.SaveMatchedNode(  # Match & save name of import
                match.DoNotCare(),
                "name"
            )
        ))

        # Add import if a name could be extracted.
        if "name" in import_info:
            # Append import name to imports list.
            # We convert the ImportAlias node to the code representation for simplified conversion
            # of multi-level imports (e.g. import.x.y.z)
            # TODO: This might be un-needed after implementing import type extraction change.
            # TODO: So far, no differentiation between import and from imports.
            import_name = self.__convert_node_to_code(import_info["name"])
            import_name = self.__clean_string_whitespace(import_name)
            self.imports.append(import_name)

        if "alias" in import_info:
            import_name = self.__clean_string_whitespace(import_info["alias"])
            self.imports.append(import_name)

        # No need to traverse children, as we already performed the matching.
        return False

    def visit_ImportFrom(self, node: cst.ImportFrom):
        if node.module is not None:
            self.imports.extend([n.value for n in match.findall(node.module, match.Name(value=match.DoNotCare()))])

    def visit_Assign(self, node: cst.Assign):
        """
        Extracts data from the assignment operator, depending on the current function depth.

        If the Visitor is not currently in a function, NewType definitions will be attempted
        to be extracted from the provided node. Otherwise, variable names will be attempted
        to be extracted from the node inside a function.
        """
        if len(self.stack) == 0:
            # We only look for NewType defs outside of functions, since they will be properly
            # scoped for usage across more than just inside the function
            self.__extract_assign_newtype(node)
        # else:
        #     # If we are inside a function, then we extract variables from assignment operators
        #     self.extract_assign_variable(node)

    def visit_AssignTarget(self, node: cst.AssignTarget):
        extracted_names = self.__extract_variable_name(node)
        if extracted_names is not None:
            # Only extract if in function
            if len(self.stack) > 0:
                # Extract names of the target.
                self.__process_extracted_assign_names(extracted_names, node.target)

            elif len(self.cls_stack) > 0:
                # Add class variables
                if 'name' in extracted_names:
                    self.cls_stack[-1].variables[extracted_names['name']] = extracted_names['type'][0]
                    self.cls_stack[-1].variables_ln[extracted_names['name']] = self.__get_line_column_no(node.target)
                    self.module_all_annotations[(self.cls_stack[-1].name, None, extracted_names['name'])] = extracted_names['type']
                else:
                    ext_names_type = self.__get_type_for_names(extracted_names['names'])
                    self.cls_stack[-1].variables = {**self.cls_stack[-1].variables,
                                                    **{n.value: t for n, t, i in ext_names_type}}
                    self.cls_stack[-1].variables_ln = {**self.cls_stack[-1].variables_ln,
                                                       **{n.value: self.__get_line_column_no(n) for n, t, i in ext_names_type}}
                    self.module_all_annotations = {**self.module_all_annotations,
                                                   **{(self.cls_stack[-1].name, None, n.value): \
                                                          (t, i) for n, t, i in ext_names_type}}
            else:
                # Adds module-level variables
                if 'name' in extracted_names:
                    self.module_variables[extracted_names['name']] = extracted_names['type'][0]
                    self.module_variables_use[extracted_names['name']] = []
                    self.module_vars_ln[extracted_names['name']] = self.__get_line_column_no(node.target)
                    self.module_all_annotations[(None, None, extracted_names['name'])] = extracted_names['type']
                else:
                    ext_names_type = self.__get_type_for_names(extracted_names['names'])
                    self.module_variables = {**self.module_variables,
                                             **{n.value: t for n, t, i in ext_names_type}}
                    self.module_variables_use = {**self.module_variables_use,
                                                 **{n.value: [] for n, t, i in ext_names_type}}
                    self.module_vars_ln = {**self.module_vars_ln,
                                           **{n.value: self.__get_line_column_no(n) for n, t, i in ext_names_type}}
                    self.module_all_annotations = {**self.module_all_annotations,
                                                   **{(None, None, n.value): (t, i) for n, t, i in ext_names_type}}

    def visit_AnnAssign(self, node: cst.AnnAssign):
        extracted_assign = self.__extract_variable_name_type(node)

        if extracted_assign is not None:
            extracted_assign['type'] = self.__convert_annotation(extracted_assign['type'])
            if len(self.stack) > 0:
                # Both name & type must be present if we have an Annotated Assign
                self.__add_variable_to_function(extracted_assign["name"], extracted_assign["type"], node.target)
                self.module_all_annotations[(self.cls_stack[-1].name if len(self.cls_stack) > 0 else None,
                                             self.stack[-1].name, extracted_assign["name"])] = \
                    (extracted_assign["type"], DEV_TYPE_ANNOT if extracted_assign["type"] else UNK_TYPE_ANNOT)
            elif len(self.cls_stack) > 0:
                # TODO: Support types in tuple format, e.g. x:int, y:int = 12, 12
                self.cls_stack[-1].variables[extracted_assign['name']] = extracted_assign['type']
                self.cls_stack[-1].variables_ln[extracted_assign['name']] = self.__get_line_column_no(node.target)
                self.module_all_annotations[(self.cls_stack[-1].name, None,
                                             extracted_assign['name'])] = \
                    (extracted_assign['type'], DEV_TYPE_ANNOT if extracted_assign["type"] else UNK_TYPE_ANNOT)
            else:
                self.module_variables[extracted_assign['name']] = extracted_assign['type']
                self.module_variables_use[extracted_assign['name']] = []
                self.module_vars_ln[extracted_assign['name']] = self.__get_line_column_no(node.target)
                self.module_all_annotations[(None, None, extracted_assign['name'])] = \
                    (extracted_assign['type'], DEV_TYPE_ANNOT if extracted_assign["type"] else UNK_TYPE_ANNOT)

    def visit_Lambda(self, node: cst.Lambda):
        self.lambda_depth += 1

    def leave_Lambda(self, node: cst.Lambda):
        self.lambda_depth -= 1

    def visit_SimpleStatementLine(self, node: cst.SimpleStatementLine):
        smt_names = [n.value for n in match.findall(node, match.Name(
                value=match.SaveMatchedNode(
                    match.DoNotCare(),
                    'name'
                )
            ))]

        if len(self.stack) > 0:
            self.fn_may_args_var_use.append(smt_names)

        if len(self.cls_stack) > 0:
            if self.cls_stack[0].name in smt_names:
                self.cls_may_vars_use.append(smt_names)

        self.__find_module_vars_use(smt_names)

    def visit_If(self, node: cst.If):
        if_names = [n.value for n in match.findall(node.test, match.Name(
                value=match.SaveMatchedNode(
                    match.DoNotCare(),
                    'name'
                )
            ))]

        if len(self.cls_stack) > 0:
            if self.cls_stack[0].name in if_names:
                self.cls_may_vars_use.append(if_names)

        if len(self.stack) > 0:
            self.fn_may_args_var_use.append(if_names)

        self.__find_module_vars_use(if_names)

    def visit_While(self, node: cst.While):

        while_names = [n.value for n in match.findall(node.test, match.Name(
                value=match.SaveMatchedNode(
                    match.DoNotCare(),
                    'name'
                )
            ))]

        if len(self.stack) > 0:
            self.fn_may_args_var_use.append(while_names)

        if len(self.cls_stack) > 0:
            if self.cls_stack[0].name in while_names:
                self.cls_may_vars_use.append(while_names)

        self.__find_module_vars_use(while_names)

    def visit_For(self, node: cst.For):

        for_names = [n.value for n in match.findall(node.iter, match.Name(
                value=match.SaveMatchedNode(
                    match.DoNotCare(),
                    'name'
                )
            ))]

        if len(self.cls_stack) > 0:
            if self.cls_stack[0].name in for_names:
                self.cls_may_vars_use.append(for_names)

        if len(self.stack) > 0:
            self.fn_may_args_var_use.append(for_names)

        self.__find_module_vars_use(for_names)

    def visit_With(self, node: cst.With):
        with_names = [n.value for n in match.findall(match.extract(node, match.With( items=match.SaveMatchedNode(
                                                                                              match.DoNotCare(),
                                                                                              'with_items'
                                                                                          )))['with_items'][0],
                                                                        match.Name(
                                                                            value=match.SaveMatchedNode(
                                                                                match.DoNotCare(),
                                                                                'name'
                                                                            )
                                                                        ))]
        if len(self.stack) > 0:
            self.fn_may_args_var_use.append(with_names)

        if len(self.cls_stack) > 0:
            if self.cls_stack[0].name in with_names:
                self.cls_may_vars_use.append(with_names)

        self.__find_module_vars_use(with_names)

    def leave_Module(self, node):
        try:
            # Calculating the type annotation coverage of the module.
            all_annot_filtered = {k: v for k, v in self.module_all_annotations.items() if k[2] != 'self'}
            no_dev_type_annot = sum([1 for k, v in all_annot_filtered.items() if v[0] and v[1] == DEV_TYPE_ANNOT])
            no_pyre_inf_annot = sum([1 for k, v in all_annot_filtered.items() if v[0] and v[1] == INF_TYPE_ANNOT])
            self.module_no_types['D'], self.module_no_types['I'] = no_dev_type_annot, no_pyre_inf_annot
            self.module_no_types['U'] = len(all_annot_filtered.keys()) - (self.module_no_types['D'] + \
                                                                          self.module_no_types['I'])  # UNK_TYPE_ANNOT
            self.module_type_annot_cove = round(sum([1 for k, v in all_annot_filtered.items() if v[0]]) \
                                                / len(all_annot_filtered.keys()), 2)
        except ZeroDivisionError:
            self.module_type_annot_cove = 1.0

    def __convert_annotation(self, node: cst.Annotation):
        """
        Converts an annotation to a string format.
        """
        if node is not None:
            # Convert annotation directly to code representation
            # TODO: Adapt this to support subtokens/subtypes for generics
            converted = self.__convert_node_to_code(node.annotation)
            #converted = self.__get_qualified_name(node.annotation)

            # Strip away newlines, spaces and tabs from the type
            converted = self.__clean_string_whitespace(converted)

            # Strip away all quotes
            # converted = converted.replace("\"", "").replace("'", "")

            return converted
        else:
            # Return blank String (no annotation)
            return ""

    def __extract_variable_name(self, node: cst.AssignTarget):
        extracted_var_names = match.extract(node, match.AssignTarget(  # Assignment operator
            target=match.OneOf(  # Two cases exist
                match.Name(  # Single target
                    value=match.SaveMatchedNode(  # Save result
                        match.MatchRegex(r'(.)+'),  # Match any string literal
                        "name"
                    )
                ),
                match.Tuple(  # Multi-target
                    elements=match.SaveMatchedNode(  # Save result
                        match.DoNotCare(),  # Type of list
                        "names"
                    )
                ),
                # This extracts variables inside __init__ without type annotation (e.g. self.x=2)
                match.Attribute(
                    value=match.Name(value=match.SaveMatchedNode(
                        match.MatchRegex(r'(.)+'),
                        "obj_name"  # Object name
                        )
                    ),
                    attr=match.Name(match.SaveMatchedNode(
                        match.MatchRegex(r'(.)+'),
                        "name"
                        )
                    ),
                )
            )
            )
        )

        if extracted_var_names is not None:
            if "name" in extracted_var_names:
                t = self.__get_type_from_metadata(node.target)
                extracted_var_names['type'] = (t, INF_TYPE_ANNOT if t else UNK_TYPE_ANNOT)
                return extracted_var_names
            elif "names" in extracted_var_names:
                return {'names': self.__extract_names_multi_assign(list(extracted_var_names['names']))}
        else:
            return extracted_var_names

    def __extract_variable_name_type(self, node: cst.AnnAssign):
        """
        Extracts a variable's identifier name and its type annotation
        """
        return match.extract(node, match.AnnAssign(  # Annotated Assignment
            target=match.OneOf(
                match.Name(  # Variable name of assignment (only one)
                    value=match.SaveMatchedNode(  # Save result
                        match.MatchRegex(r'(.)+'),  # Match any string literal
                        "name"
                    )
                ),
                # This extracts variables inside __init__ which typically starts with self (e.g. self.x:int=2)
                match.Attribute(
                    value=match.Name(value=match.SaveMatchedNode(
                        match.MatchRegex(r'(.)+'),
                        "obj_name"  # Object name
                    )
                    ),
                    attr=match.Name(match.SaveMatchedNode(
                        match.MatchRegex(r'(.)+'),
                        "name"
                    )
                    ),
                )
            ),
            annotation=match.SaveMatchedNode(  # Save result
                match.DoNotCare(),  # Match any string literal
                "type"
            )
        )
            )

    def __extract_assign_newtype(self, node: cst.Assign):
        """
        Attempts extracting a NewType declaration from the provided Assign node.

        If the Assign node corresponds to a NewType assignment, the NewType name is
        added to the class definitions of the Visitor.
        """
        # Define matcher to extract NewType assignment
        matcher_newtype = match.Assign(
            targets=[  # Check the assign targets
                match.AssignTarget(  # There should only be one target
                    target=match.Name(  # Check target name
                        value=match.SaveMatchedNode(  # Save target name
                            match.MatchRegex(r'(.)+'),  # Match any string literal
                            "type"
                        )
                    )
                )
            ],
            value=match.Call(  # We are examining a function call
                func=match.Name(  # Function must have a name
                    value="NewType"  # Name must be 'NewType'
                ),
                args=[
                    match.Arg(  # Check first argument
                        value=match.SimpleString()  # First argument must be the name for the type
                    ),
                    match.ZeroOrMore()  # We allow any number of arguments after by def. of NewType
                ]
            )
        )

        extracted_type = match.extract(node, matcher_newtype)

        if extracted_type is not None:
            # Append the additional type to the list
            # TODO: Either rename class defs, or create new list for additional types
            self.class_defs.append(extracted_type["type"].strip("\'"))

    def __extract_names_multi_assign(self, elements):
        # Add self vars. in tuple assignments, e.g. self.x, self.y = 1, 2
        # Adds variables in tuple(s) in multiple assignments, e.g. a, (b, c) = 1, (2, 3)
        names: List[cst.Name] = []
        i = 0
        while i < len(elements):
            if match.matches(elements[i], match.Element(value=match.Name(value=match.DoNotCare()))):
                names.append(elements[i].value)
            elif match.matches(elements[i], match.Element(value=match.Attribute(attr=match.Name(value=match.DoNotCare())))):
                names.append(elements[i].value)
            elif match.matches(elements[i], match.Element(value=match.Tuple(elements=match.DoNotCare()))):
                elements.extend(match.findall(elements[i].value, match.Element(value=match.OneOf(
                    match.Attribute(attr=match.Name(value=match.DoNotCare())),
                    match.Name(value=match.DoNotCare())
                ))))
            i += 1

        return names
    def __add_variable_to_function(self, name, annotation, name_node: cst.Name):
        """
        Adds a variable definition/assignment to the current function,
        provided the visitor is in a function currently.
        """
        # Check if we're in a function
        if len(self.stack) > 0:
            # Get current function (top of stack)
            func = self.stack[-1]

            # Convert None to '' if needed
            annotation = annotation if annotation is not None else ''

            # Add name & annotation to function local variable data
            func.variables[name] = annotation
            func.variables_ln[name] = self.__get_line_column_no(name_node)
            # func.variables_types.append(annotation)

            # Add entry to dictionary as (name -> annotation), provided
            # that this variable is not in the dictionary already
            # if (name not in func.variables):
            #     func.variables[name] = annotation

    def __process_extracted_assign_names(self, extracted_names, name_node: cst.Name):
        """
        Auxiliary function to process the output of a matcher extraction
        for extracting assign targets.

        The given extracted names variable is expected to be a dictionary
        with either 'name' holding a single string corresponding to
        the variable name, or 'names' which is expected to be a list of
        match.Element entries, corresponding to tuple assignment.

        The function processes the extracted names for both cases, and
        adds these definitions to the function.
        """

        if "name" in extracted_names:
            # Single name extracted
            extracted_name = extracted_names["name"]

            # Add the variable to function
            self.__add_variable_to_function(extracted_name, extracted_names['type'][0], name_node)

            self.module_all_annotations[(self.cls_stack[-1].name if len(self.cls_stack) > 0 else None,
                                         self.stack[-1].name, extracted_name)] = extracted_names['type']

        elif "names" in extracted_names:
            # Iterate through all target names
            for name in extracted_names["names"]:
                name_type = self.__get_type_from_metadata(name)
                if match.matches(name, match.Name(value=match.DoNotCare())):
                    self.__add_variable_to_function(name.value, name_type, name)
                    name = name.value
                elif match.matches(name, match.Attribute(attr=match.Name(value=match.DoNotCare()))):
                    self.__add_variable_to_function(name.attr.value, name_type, name.attr)
                    name = name.attr.value

                self.module_all_annotations[(self.cls_stack[-1].name if len(self.cls_stack) > 0 else None,
                                             self.stack[-1].name, name)] = \
                    (name_type, INF_TYPE_ANNOT if name_type else UNK_TYPE_ANNOT)

    def __find_args_vars_use(self, vars_name: list, may_vars_use: List[list], is_var_arg: bool=False) -> dict:
        """
        Finds usage of variables or functions' arguments in a context
        """

        # def is_var_def(a: str, mu: list):
        #     if is_var_arg:
        #         return False
        #     else:
        #         # TODO: Do not exclude non-assign statements like x+= smt
        #         return a in mu[0] or ('self' in mu[0] and a in mu[1])

        fn_args_use = {}
        for arg in vars_name:
            arg_use = []
            for may_use in may_vars_use:
                if arg in may_use and len(may_use) > 1:
                    # Excludes variable definition itself from the context hints
                    arg_use.append(may_use)
            fn_args_use[arg] = arg_use

        return fn_args_use

    def __find_module_vars_use(self, may_vars_use: list):
        """
        Finds usage of module variables in a context
        """

        for v in self.module_variables.keys():
            # TODO: To be more exact, the variable can be checked whether it's in functions' vars or class vars
            if v in may_vars_use:
                self.module_variables_use[v].append(may_vars_use)

    def __convert_node_to_code(self, node) -> str:
        """
        Converts a node to a code string.
        """
        # Construct artificial module from single node
        node_module = cst.Module([node])

        # Return the code representation of that module
        return node_module.code

    def __clean_string_whitespace(self, string: str) -> str:
        """
        Removes tabs, newlines and implicit newlines (\\ in Python), and converts
        all multiple spaces to a single space from a string.
        """
        return re.sub(' +', ' ', re.sub('\n|\t|\\\\', '', string))

    def __extract_docstring(self, node: cst.FunctionDef) -> str:
        """
        Extracts & post-processes the docstring from the provided function node.
        If a docstring is not present, an empty string is returned.

        :node: Function node
        :return: Docstring as string
        """
        # Get docstring from Function node
        docstring = node.get_docstring()

        # Return empty string if docstring undefined
        return docstring if docstring is not None else ""

    def __get_qualified_name(self, node) -> Optional[str]:
        q_name = list(self.get_metadata(cst.metadata.QualifiedNameProvider, node))
        return q_name[0].name if len(q_name) != 0 else None

    def __get_type_for_names(self, names: List[cst.Name]):
        n_types: List[Tuple[cst.Name, str, Union[UNK_TYPE_ANNOT, INF_TYPE_ANNOT]]] = []
        for n in names:
            t = self.__get_type_from_metadata(n)
            n_types.append((n, t, INF_TYPE_ANNOT if t else UNK_TYPE_ANNOT))
        return n_types

    def __get_type_from_metadata(self, node: cst.Name) -> str:
        """
        Extracts type of a `Name` node if `TypeInferenceProvider` given.
        """
        try:
            ext_type = self.__clean_string_whitespace(self.get_metadata(cst.metadata.TypeInferenceProvider, node))
            # A workaround for pyre's weird inferred integers
            if bool(re.match("^typing_extensions.Literal\[[0-9]+\]$", ext_type)):
                ext_type = 'int'
            elif bool(re.match("^typing_extensions.Literal\[.+\]$", ext_type)):
                ext_type = "str"

            # q_name = self.__get_qualified_name(node)
            # if q_name is not None and q_name not in self.module_pyre_inferred_types:
            #     self.module_pyre_inferred_types.append(q_name)

            return ext_type

        except KeyError:
            return ''

    def __get_line_column_no(self, node) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        lc = self.get_metadata(cst.metadata.PositionProvider, node)
        return (lc.start.line, lc.start.column), (lc.end.line, lc.end.column)


class TypeAnnotationCounter(cst.CSTVisitor):
    """
    It counts the number of type annotations in a Python source code file
    """

    def __init__(self):
        super().__init__()
        self.total_no_type_annot = 0

    def visit_FunctionDef(self, node: cst.FunctionDef):
        if node.returns is not None:
            self.total_no_type_annot += 1

    def visit_Param(self, node: cst.Param):
        if node.annotation is not None:
            self.total_no_type_annot += 1
        return False

    def visit_AnnAssign(self, node: cst.AnnAssign):
        self.total_no_type_annot += 1
        return False


class CountParametricTypeDepth(cst.CSTVisitor):
    """
    Counts the depth of parametric types. E.g., List[List[int]] has a depth of 2.
    """
    def __init__(self):
        self.type_annot_depth = 0

    def visit_Subscript(self, node):
        self.type_annot_depth += 1
