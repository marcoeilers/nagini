"""
Copyright (c) 2025 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
import ast
from contextlib import contextmanager
from typing import List, Optional, Union, Tuple, Callable

from nagini_contracts.contracts import (
    CONTRACT_FUNCS, GHOST_BUILTINS, CONTRACT_WRAPPER_FUNCS,
    CONTRACT_DECORATORS, SPECIAL_PREDICATES
    )
from nagini_contracts.io_contracts import (
    BUILTIN_IO_OPERATIONS, GHOST_IO_TYPES, IO_CONTRACT_FUNCS,
    IO_MIXED_RETURN_FUNCS, IO_OPERATION_PROPERTY_FUNCS, IO_FUNCS, IO_DECORATORS
    )
from nagini_contracts.obligations import OBLIGATION_CONTRACT_FUNCS
from nagini_translation.lib.constants import OBJECT_TYPE, THREADING
from nagini_translation.lib.program_nodes import (
    MethodType, PythonModule, PythonType, PythonMethod, PythonIOOperation,
    PythonVarBase, PythonClass, PythonNode, PythonField, UnionType, GenericType
    )
from nagini_translation.lib.context import Context
from collections import OrderedDict
from nagini_translation.lib.resolver import get_target as do_get_target
from nagini_translation.lib.resolver import get_type as do_get_type
from nagini_translation.lib.util import (
    get_func_name,
    construct_lambda_prefix,
    InvalidProgramException,
    UnsupportedException,
)

annotation_t = Union[ast.Name, ast.Constant, ast.Attribute, ast.Subscript]

ALL_CONTRACT_ELEMS = (CONTRACT_FUNCS + CONTRACT_WRAPPER_FUNCS +
                        IO_CONTRACT_FUNCS + IO_OPERATION_PROPERTY_FUNCS +
                        list(BUILTIN_IO_OPERATIONS) + IO_FUNCS +
                        SPECIAL_PREDICATES + OBLIGATION_CONTRACT_FUNCS
                        )

# Names of types which are always ghost, i.e. which only exist during verification.
ALL_GHOST_TYPE_NAMES = GHOST_BUILTINS + GHOST_IO_TYPES

NAGINI_DECORATORS = CONTRACT_DECORATORS + IO_DECORATORS

# Nagini functions which can be used in a regular context, when the given Nth argument is regular
TRANSPARENT_CALLS = {'Unfolding': 1, 'Reveal': 0}

IGNORE_REG_CALLS = ['TypeVar']

# Functions which have no side effects, so that the result is ghost exactly if
# one of the arguments is.
PURE_REG_CALLS = ['len', 'isinstance', 'cast']

# Decorators which mark a function that exists for verification purposes only.
SPEC_ONLY_DECORATORS = ['IOOperation', 'Predicate']

# Decorator which marks a function whose body consists of specifications only.
CONTRACT_ONLY_DECORATOR = 'ContractOnly'

NAGINI_IMPORT = 'nagini_contracts'

# Marker for return type annotations of the form Tuple[<regular type>, <ghost type>],
# i.e. return values which have both a regular and a ghost component.
MIXED_RETURN = 'mixed'

# Ghost information of a return value: None if unknown, MIXED_RETURN if the
# return value has both a regular and a ghost component, and otherwise whether
# the whole return value is ghost.
return_info_t = Optional[Union[bool, str]]

# Marker for return information which has not been computed yet.
_UNCOMPUTED = object()

class GhostChecker(ast.NodeVisitor):
    """
    Walks through the Python AST and checks for ill-formed ghost elements.
    """
    
    def __init__(self, modules: List[PythonModule]) -> None:
        self.modules = modules
        self.ctx = None
        self.in_ghost_ctx = False
        # The module whose contents are currently being checked.
        self.current_module = None
        # True as soon as a ghost statement has been found inside a function body.
        # Ghost statements are translated into terminating sections, which require
        # the obligation encoding to be enabled.
        self.has_ghost_statements = False

    @property
    def global_module(self) -> PythonModule:
        return self.modules[0]

    def check(self, ctx: Context) -> None:
        """
        Checks the defined modules for valid ghost information in the given context.
        It also stores additional ghost information on AST nodes, which is used for
        the Termination analysis and the extraction.
        """
        self.ctx = ctx
        # Modules which correspond to directories do not have contents of their own;
        # they share the AST of the module that imports them, so we must not visit
        # them a second time.
        visited_nodes = set()
        for module in self.modules[1:]:
            if module.node is None or id(module.node) in visited_nodes:
                continue
            if self.is_library_module(module):
                # Nagini's own contract library is trusted and not checked.
                continue
            visited_nodes.add(id(module.node))
            with self.module_scope(module):
                self.in_ghost_ctx = False
                if module is self.modules[1]:
                    self.visit(module.node)
                else:
                    # Errors in imported modules have to name the module they
                    # occur in, since positions are reported relative to the
                    # file that is being verified.
                    try:
                        self.visit(module.node)
                    except (InvalidProgramException, UnsupportedException) as error:
                        raise self.locate_error(error, module) from error

    def locate_error(self, error: Exception, module: PythonModule) -> Exception:
        """
        Returns a copy of the given error whose message names the module and the
        line the error occurred in.
        """
        line = getattr(error.node, 'lineno', None)
        location = f"{module.type_prefix or module.file}"
        if line is not None:
            location += f", line {line}"
        if isinstance(error, InvalidProgramException):
            message = error.message if error.message else error.code
            return InvalidProgramException(error.node, error.code,
                                           f"[in {location}] {message}")
        return UnsupportedException(error.node, f"[in {location}] {error.desc}")

    def is_library_module(self, module: PythonModule) -> bool:
        """
        Returns whether the given module is part of Nagini's contract library,
        whose contents are trusted and therefore not ghost checked.
        """
        prefix = module.type_prefix
        return bool(prefix) and prefix.split('.')[0] == NAGINI_IMPORT

    @contextmanager
    def module_scope(self, module: Optional[PythonModule]):
        """
        Context manager which makes the given module the one whose names are
        used to resolve targets and annotations.
        """
        if module is None:
            module = self.current_module
        old_module = self.current_module
        old_ctx_module = self.ctx.module
        old_function = self.ctx.current_function
        old_class = self.ctx.current_class
        self.current_module = module
        self.ctx.module = module
        if module is not old_module:
            # Names of the other module must not be resolved in the current scope.
            self.ctx.current_function = None
            self.ctx.current_class = None
        try:
            yield
        finally:
            self.current_module = old_module
            self.ctx.module = old_ctx_module
            self.ctx.current_function = old_function
            self.ctx.current_class = old_class

    def visit(self, node: ast.AST) -> None:
        result = super().visit(node)
        if isinstance(node, ast.stmt):
            node.needs_terminating_section = self.needs_terminating_section(node)
            if node.needs_terminating_section:
                # Terminating sections are encoded using obligations.
                self.has_ghost_statements = True
        return result

    def needs_terminating_section(self, node: ast.stmt) -> bool:
        """
        Returns whether the given statement has to be checked to terminate.
        This is the case for ghost code, i.e. statements which are only executed
        during verification. Declarations and specifications are excluded: they
        cannot diverge, and their execution is checked by Nagini itself.
        """
        if not getattr(node, 'is_ghost', False):
            return False
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                             ast.Import, ast.ImportFrom, ast.Pass, ast.Assert)):
            return False
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and \
                get_func_name(node.value) in ALL_CONTRACT_ELEMS:
            # A specification, e.g. Requires(...) or Assert(...).
            return False
        return True

    def generic_visit(self, node: ast.AST) -> None:
        node.is_ghost = self.in_ghost_ctx
        children = []
        for _, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        self.visit(item)
                        children.append(item)
            elif isinstance(value, ast.AST):
                self.visit(value)
                children.append(value)
        self.set_contains_ghost(node, self.in_ghost_ctx, *children)

    def mark_ghost(self, node: ast.AST) -> None:
        """
        Marks the entire subtree rooted in the given node as ghost.
        """
        for sub_node in ast.walk(node):
            sub_node.is_ghost = True
            sub_node.contains_ghost = True

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        current_class: PythonClass = self.current_module.classes[node.name]
        self.ctx.current_class = current_class
        old_ghost_ctx = self.in_ghost_ctx #TODO: Do we need to define classes within ghost context?
        self.in_ghost_ctx = current_class.is_ghost

        # Classes may only have explicit bases of the same ghost type,
        # i.e. ghost classes only have explicit ghost bases (and the implicit object base).
        object_class = self.global_module.classes[OBJECT_TYPE]
        superclass = current_class.superclass
        if not (superclass is object_class or
                self.is_ghost(superclass) == current_class.is_ghost):
            raise InvalidProgramException(node, "invalid.ghost.classDef")

        for stmt in node.body:
            self.visit(stmt)

        self.in_ghost_ctx = old_ghost_ctx
        self.ctx.current_class = None
        node.is_ghost = current_class.is_ghost
        self.set_contains_ghost(node, current_class.is_ghost, *node.body)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        decorators = {d.id for d in node.decorator_list if isinstance(d, ast.Name)}
        if any([dec in SPEC_ONLY_DECORATORS for dec in decorators]):
            # Predicates and IO operations only exist during verification, so
            # everything about them is ghost.
            self.mark_ghost(node)
            return
        # The body of a contract only function consists of specifications only.
        contract_only = CONTRACT_ONLY_DECORATOR in decorators

        # Resolve defined function
        if 'property' in decorators:
            if not isinstance(self.ctx.current_class, PythonClass):
                raise InvalidProgramException(node, 'invalid.property', "Property outside of class.")
            current_function = self.ctx.current_class.get_field(node.name)
        else:
            scope = self.ctx.current_class if self.ctx.current_class else self.current_module
            current_function = scope.get_func_or_method(node.name)
        if current_function is None:
            attr_decorators = [d for d in node.decorator_list if isinstance(d, ast.Attribute)]
            if len(attr_decorators) == 1 and attr_decorators[0].attr == 'setter':
                if not isinstance(self.ctx.current_class, PythonClass):
                    raise InvalidProgramException(node, 'invalid.property', "Property outside of class.")
                property_function = self.ctx.current_class.get_field(attr_decorators[0].value.id)
                current_function = property_function.setter

        if current_function is None:
            raise InvalidProgramException(node, 'invalid.ghost.functionDef', f"Couldn't correctly resolve function {node.name}")
        
        self.ctx.current_function = current_function
        old_ghost_ctx = self.in_ghost_ctx
        self.in_ghost_ctx = current_function.is_ghost
        
        # Check annotations
        if not current_function.is_ghost:
            contains_ghost = any([d in NAGINI_DECORATORS for d in decorators])

            # Each (non-variadic) argument must be clearly regular or ghost
            norm_args = list(node.args.args)
            norm_args.extend(node.args.posonlyargs)
            norm_args.extend(node.args.kwonlyargs)
            for arg in norm_args:
                if arg.annotation is not None:
                    ann_type = self.check_annotation(arg.annotation)
                    arg.is_ghost = ann_type
                    contains_ghost = contains_ghost or ann_type
                else:
                    arg.is_ghost = False
            
            # Each default value must be an allowed assignment
            for param in current_function.args.values():
                if param.default is not None and not self.is_assignable(param.default, param):
                    raise InvalidProgramException(node, 'invalid.ghost.default')

            # Variadic arguments must be regular
            for arg in [node.args.vararg, node.args.kwarg]:
                if arg is not None:
                    if arg.annotation is not None and self.check_annotation(arg.annotation):
                        raise InvalidProgramException(arg, 'invalid.ghost.annotation')
                    arg.is_ghost = False

            # The return must be None, a Tuple[only_reg, only_ghost] or clearly regular or ghost
            return_ann = node.returns
            ret_info = self.get_return_info(current_function)
            if return_ann is not None:
                return_ann.is_ghost = ret_info is True
                return_ann.contains_ghost = ret_info is not False
                contains_ghost = contains_ghost or ret_info is not False
        else:
            # All elements must be ghost, so annotations do not need to be further analyzed.
            # However, the function may not have variadic arguments
            if node.args.vararg is not None or node.args.kwarg is not None:
                raise InvalidProgramException(node, 'invalid.ghost.functionDef')
            self.mark_ghost(node.args)
            if node.returns is not None:
                self.mark_ghost(node.returns)
            contains_ghost = True

        if contract_only:
            # The body consists of specifications only.
            for stmt in node.body:
                self.mark_ghost(stmt)
        else:
            for stmt in node.body:
                self.visit(stmt)

        self.ctx.current_function = None
        self.in_ghost_ctx = old_ghost_ctx
        node.is_ghost = current_function.is_ghost
        node.contains_ghost = contains_ghost or any([stmt.contains_ghost for stmt in node.body])

    def visit_Return(self, node: ast.Return) -> None:
        if self.ctx.actual_function.is_ghost:
            # Ghost returns are only invalid if we call an impure regular function
            self.check_for_call(node)
            node.is_ghost = True
            node.contains_ghost = True
        else:
            if self.in_ghost_ctx:
                raise InvalidProgramException(
                    node, 'invalid.ghost.return',
                    "A regular function cannot return from within ghost code.")
            current_function = self.ctx.current_function
            expect_ret = current_function.node.returns
            ret_info = self.get_return_info(current_function)
            contains_ghost = False
            if node.value is None:
                # Returning nothing cannot be invalid or mypy would throw error
                pass
            elif ret_info == MIXED_RETURN:
                contains_ghost = True
                mixed_parts = self.get_mixed_return_parts(expect_ret)
                if isinstance(node.value, ast.Tuple) and len(node.value.elts) == 2:
                    for ret, expect in zip(node.value.elts, mixed_parts):
                        expect_type = self.check_annotation(expect)
                        if not self.is_assignable(ret, expect_type):
                            raise InvalidProgramException(node, 'invalid.ghost.return')
                    node.value.is_ghost = False
                    self.set_contains_ghost(node.value, True, *node.value.elts)
                elif isinstance(node.value, ast.Call) and \
                        self.check_call(node.value) == (False, MIXED_RETURN):
                    # Directly returning the result of a call with an equivalent
                    # return type is fine as well.
                    pass
                else:
                    raise InvalidProgramException(
                        node, 'invalid.ghost.return',
                        "A return value with a regular and a ghost part must be returned "
                        "as a tuple of two elements or as the result of a single call.")
            else:
                expect_type = ret_info is True
                if not self.is_assignable(node.value, expect_type):
                    raise InvalidProgramException(
                        node, 'invalid.ghost.return',
                        "The returned value does not match the ghost type of the "
                        "declared return type.")
                contains_ghost = expect_type

            node.is_ghost = False
            self.set_contains_ghost(node, contains_ghost, node.value)

    def visit_Delete(self, node: ast.Delete):
        if self.has_mixed_elems(node.targets):
            raise InvalidProgramException(node, 'invalid.ghost.delete')
        if self.in_ghost_ctx:
            for target in node.targets:
                if not self.is_ghost(target):
                    raise InvalidProgramException(node, 'invalid.ghost.delete')
        
        is_node_ghost = self.is_ghost(node.targets[0])
        node.is_ghost = is_node_ghost
        self.set_contains_ghost(node, is_node_ghost, *node.targets)

    def visit_Assign(self, node: ast.Assign) -> None:
        are_targets_ghost = all([self.is_ghost(target) for target in self.get_all_targets(node.targets)])
        is_node_definitively_ghost = are_targets_ghost and not isinstance(node.value, ast.Call)
        if is_node_definitively_ghost:
            old_ctx = self.in_ghost_ctx
            self.in_ghost_ctx = True
        
        for target in node.targets:
            if isinstance(target, (ast.Tuple, ast.List)):
                # Unpacking
                self.check_unpacking(node.value, target)
            else:
                # Normal assignment
                self.check_assign(node.value, target)
        
        if is_node_definitively_ghost:
            self.in_ghost_ctx = old_ctx

        is_node_ghost = is_node_definitively_ghost or (are_targets_ghost and self.is_ghost(node.value))
        node.is_ghost = is_node_ghost
        self.set_contains_ghost(node, is_node_ghost, node.value, *node.targets)

    def get_all_targets(self, targets: List[ast.expr]) -> List[ast.expr]:
        all_targets = []
        for target in targets:
            if isinstance(target, (ast.Tuple, ast.List)):
                all_targets.extend(self.get_all_targets(target.elts))
            else:
                all_targets.append(target)

        return all_targets

    def visit_AugAssign(self, node: ast.AugAssign):
        is_target_ghost = self.is_ghost(node.target)
        is_node_definitively_ghost = is_target_ghost and not isinstance(node.value, ast.Call)
        if is_node_definitively_ghost:
            old_ctx = self.in_ghost_ctx
            self.in_ghost_ctx = True

        is_value_ghost = self.is_ghost(node.value)
        self.check_assign(is_value_ghost, node.target)

        if is_node_definitively_ghost:
            self.in_ghost_ctx = old_ctx

        is_node_ghost = is_node_definitively_ghost or (is_target_ghost and self.is_ghost(node.value))
        node.is_ghost = is_node_ghost
        self.set_contains_ghost(node, is_node_ghost, node.value, node.target)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        is_target_ghost = self.is_ghost(node.target)
        is_node_definitively_ghost = is_target_ghost and not isinstance(node.value, ast.Call)
        if is_node_definitively_ghost:
            old_ctx = self.in_ghost_ctx
            self.in_ghost_ctx = True
        
        self.check_annotation(node.annotation)
        if node.value is None:
            # Annotated declaration without assign. Simply proceed
            is_node_ghost = self.is_ghost(node.target)
            node.is_ghost = is_node_ghost
            self.set_contains_ghost(node, is_node_ghost, node.target)
        else:
            self.check_assign(node.value, node.target)

            is_node_ghost = is_node_definitively_ghost or (is_target_ghost and self.is_ghost(node.value))
            node.is_ghost = is_node_ghost
            self.set_contains_ghost(node, is_node_ghost, node.value, node.target)
        
        if is_node_definitively_ghost:
                self.in_ghost_ctx = old_ctx

    def check_assign(self, value: Union[ast.expr, bool], target: ast.expr, allow_conversion: bool =True) -> None:        
        if isinstance(target, (ast.Name, ast.Attribute)):
            if not self.is_assignable(value, target, allow_conversion):
                raise InvalidProgramException(
                    target, 'invalid.ghost.assign',
                    "Ghost values may only be assigned to ghost targets.")
        else:
            assert isinstance(target, ast.Subscript), f"Unexpected type of {type(target)}"
            # The subscript of a ghost element may only be read
            if self.is_ghost(target) or self.is_ghost(value) or self.in_ghost_ctx:
                raise InvalidProgramException(
                    target, 'invalid.ghost.assign',
                    "The elements of a ghost collection may only be read.")

    def check_unpacking(self, value: Union[ast.expr, bool], target: Union[ast.List, ast.Tuple]) -> None:
        unpacked = target.elts

        # Resolve value to multiple values
        if isinstance(value, ast.Call):
            is_func_ghost, ret_info = self.check_call(value)
            if is_func_ghost:
                values = [True] * len(unpacked)
            elif ret_info == MIXED_RETURN:
                values = [False, True]
            elif isinstance(ret_info, bool):
                values = [ret_info] * len(unpacked)
            else:
                values = [False] * len(unpacked)
        else:
            # The unpacked value is either an expression which is ghost as a
            # whole, or a boolean which already says whether it is ghost.
            values = [self.is_ghost(value)] * len(unpacked)
        
        if any(isinstance(item, ast.Starred) for item in unpacked):
            # For simplicity, we only allow starred unpacking in regular code
            items = unpacked + values
            for item in items:
                if self.is_ghost(item):
                    raise InvalidProgramException(item, 'invalid.ghost.assign')
            target.is_ghost = False
            self.set_contains_ghost(target, False, *items)
        else:
            # For simplicity during extraction, we allow no conversion (assign
            # reg element to ghost element) during unpacking of mixed targets
            allow_conversion = not self.has_mixed_elems(unpacked)
            
            for sub_target, sub_value in zip(unpacked, values):
                if isinstance(sub_target, (ast.List, ast.Tuple)):
                    self.check_unpacking(sub_value, sub_target)
                else:
                    self.check_assign(sub_value, sub_target, allow_conversion)
                    
            is_target_ghost = all([self.is_ghost(sub_target) for sub_target in unpacked])
            target.is_ghost = is_target_ghost
            self.set_contains_ghost(target, is_target_ghost, *unpacked)
            self.is_ghost(value) # Set flags on value

    def visit_For(self, node: ast.For):
        is_iter_ghost = self.is_ghost(node.iter)
        if is_iter_ghost:
            # Set is_ghost flag of all vars
            def set_var_ghost(var: PythonVarBase) -> None:
                var.is_ghost = True
            if not self.call_on_vars(node.target, set_var_ghost):
                # Iterating over a ghost collection into a target that cannot be
                # made ghost (e.g. a field or a subscript) is not allowed.
                raise InvalidProgramException(node, 'invalid.ghost.For')
        else:
            # We do not allow loop vars to be defined ghost elsewhere
            def check_var(var: PythonVarBase) -> None:
                if var.is_ghost:
                    raise InvalidProgramException(node, 'invalid.ghost.For')
            self.call_on_vars(node.target, check_var)
        self.check_control_flow(is_iter_ghost, node.iter, node.body, node.orelse)

        node.is_ghost = is_iter_ghost
        self.set_contains_ghost(node, is_iter_ghost, node.iter, *node.body, *node.orelse)

    def call_on_vars(self, expr: ast.expr, f: Callable[[PythonVarBase], None]) -> bool:
        """
        Applies the given function to all variables the given target expression
        assigns to. Returns whether all assigned targets were in fact variables.
        """
        if isinstance(expr, ast.Starred):
            return self.call_on_vars(expr.value, f)
        elif isinstance(expr, (ast.Tuple, ast.List)):
            return all([self.call_on_vars(e, f) for e in expr.elts])
        elif isinstance(expr, ast.Name):
            var = self.get_target(expr, self.ctx)
            if not isinstance(var, PythonVarBase):
                return False
            f(var)
            return True
        # Targets which are not variables (e.g. attributes or subscripts) cannot
        # be marked as ghost.
        return False

    def visit_While(self, node: ast.While):
        is_test_ghost = self.is_ghost(node.test)
        self.check_control_flow(is_test_ghost, node.test, node.body, node.orelse)

        node.is_ghost = is_test_ghost
        self.set_contains_ghost(node, is_test_ghost, node.test, *node.body, *node.orelse)

    def visit_If(self, node: ast.If):
        is_test_ghost = self.is_ghost(node.test)
        self.check_control_flow(is_test_ghost, node.test, node.body, node.orelse)

        node.is_ghost = is_test_ghost
        self.set_contains_ghost(node, is_test_ghost, node.test, *node.body, *node.orelse)

    def check_control_flow(self, is_test_ghost: bool, test: ast.expr, body: List[ast.stmt], orelse: List[ast.stmt]):
        if is_test_ghost:
            old_ctx = self.in_ghost_ctx
            self.in_ghost_ctx = True
            self.check_for_call(test)

        for stmt in body:
            self.visit(stmt)
        for stmt in orelse:
            self.visit(stmt)

        if is_test_ghost:
            self.in_ghost_ctx = old_ctx

    def visit_With(self, node: ast.With):
        # With may only be used in and with regular code
        if self.in_ghost_ctx:
            raise InvalidProgramException(node, 'invalid.ghost.with')

        for withitem in node.items:
            if self.is_ghost(withitem.context_expr) or (withitem.optional_vars is not None and
                                                        self.is_ghost(withitem.optional_vars)):
                raise InvalidProgramException(node, 'invalid.ghost.with')

        for stmt in node.body:
            self.visit(stmt)

        node.is_ghost = False
        self.set_contains_ghost(node, False, *node.body)

    def visit_Try(self, node: ast.Try):
        # Exception handling may only be used in regular code, since exceptions
        # cannot be raised from ghost code.
        if self.in_ghost_ctx:
            raise InvalidProgramException(node, 'invalid.ghost.try')

        blocks = [node.body, node.orelse, node.finalbody]
        for handler in node.handlers:
            for stmt in handler.body:
                self.visit(stmt)
            handler.is_ghost = False
            self.set_contains_ghost(handler, False, *handler.body)
        for block in blocks:
            for stmt in block:
                self.visit(stmt)

        node.is_ghost = False
        self.set_contains_ghost(node, False, *node.handlers,
                                *[stmt for block in blocks for stmt in block])

    def visit_Raise(self, node: ast.Raise):
        if self.in_ghost_ctx:
            raise InvalidProgramException(node, 'invalid.ghost.raise')
        if node.exc is not None and self.is_ghost(node.exc):
            raise InvalidProgramException(
                node, 'invalid.ghost.raise',
                "Ghost code cannot raise exceptions.")

        node.is_ghost = False
        self.set_contains_ghost(node, False, node.exc)

    def visit_Assert(self, node: ast.Assert):
        # A plain assert statement is executed at runtime, so it may not talk
        # about ghost state. Use the Assert contract function for that.
        is_test_ghost = self.is_ghost(node.test)
        is_msg_ghost = self.is_ghost(node.msg) if node.msg is not None else False
        if self.in_ghost_ctx or is_test_ghost or is_msg_ghost:
            raise InvalidProgramException(node, 'invalid.ghost.assert',
                                          "Use the Assert contract function when "
                                          "working with ghost elements.")

        node.is_ghost = False
        self.set_contains_ghost(node, False, node.test, node.msg)

    def visit_Expr(self, node: ast.Expr):
        is_node_ghost = self.is_ghost(node.value)

        if is_node_ghost:
            old_ctx = self.in_ghost_ctx
            self.in_ghost_ctx = True
            self.check_for_call(node.value)
            self.in_ghost_ctx = old_ctx

        node.is_ghost = is_node_ghost
        node.contains_ghost = node.value.contains_ghost

    def check_for_call(self, node: ast.AST):
        # Scan expression for function calls
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.Call):
                        self.check_call(item)
                    elif isinstance(item, ast.AST):
                        self.check_for_call(item)
            elif isinstance(value, ast.Call):
                self.check_call(value)
            elif isinstance(value, ast.AST):
                self.check_for_call(value)

    def visit_Break(self, node: ast.Break):
        if self.in_ghost_ctx:
            raise InvalidProgramException(
                node, 'invalid.ghost.break',
                "Ghost code cannot break out of a regular loop.")
        node.is_ghost = False
        node.contains_ghost = False
    
    def visit_Continue(self, node: ast.Continue):
        if self.in_ghost_ctx:
            raise InvalidProgramException(
                node, 'invalid.ghost.continue',
                "Ghost code cannot continue a regular loop.")
        node.is_ghost = False
        node.contains_ghost = False

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module is not None and NAGINI_IMPORT in node.module.split('.'):
            node.is_ghost = True
            node.contains_ghost = True
            super().generic_visit(node)
        else:
            self.generic_visit(node)

    def check_annotation(self, ann: annotation_t) -> bool:
        """
        Checks whether the annotation is valid in regards to ghost information.
        For example, we do not allow Union[Set, PSet], as it is unclear whether the corresponding value will be ghost.
        When the annotation is valid, we return whether it denotes a ghost value.
        """
        if isinstance(ann, ast.Name):
            # Must be valid or mypy would throw error
            return (self.is_ghost_name(ann.id) or
                    self.is_ghost_type(self.get_target(ann, self.ctx)))
        elif isinstance(ann, ast.Constant):
            if ann.value is None:
                return False
            # A forward reference. Must be valid or mypy would throw error.
            return (self.is_ghost_name(ann.value) or
                    self.is_ghost_type(self.find_type(ann.value)))
        elif isinstance(ann, ast.Attribute):
            # Must be valid or mypy would throw error. Find module and check for ghost name
            mod: Optional[PythonNode] = self.get_target(ann.value, self.ctx)
            if not isinstance(mod, PythonModule):
                raise InvalidProgramException(ann, 'invalid.ghost.annotation',
                                              "Couldn't correctly resolve module of annotation.")
            return (ann.attr in mod.ghost_names or
                    self.is_ghost_type(mod.classes.get(ann.attr)))
        else:
            assert isinstance(ann, ast.Subscript), f"Unexpected type of {type(ann)}"
            # A generic ghost type, e.g. PSeq[int], is ghost no matter what its
            # type arguments are.
            if isinstance(ann.value, (ast.Name, ast.Constant, ast.Attribute)) and \
                    self.check_annotation(ann.value):
                return True
            if isinstance(ann.slice, (ast.Name, ast.Constant, ast.Subscript, ast.Attribute)):
                return self.check_annotation(ann.slice)
            assert isinstance(ann.slice, (ast.Tuple, ast.List)), f"Unexpected type of {type(ann.slice)}"
            sub_anns = ann.slice.elts
            if len(sub_anns) == 1:
                return self.check_annotation(sub_anns[0])

            if isinstance(sub_anns[0], ast.Constant) and sub_anns[0].value is None:
                start_idx = 1
            else:
                start_idx = 0
            fst = self.check_annotation(sub_anns[start_idx])
            for idx in range(start_idx+1, len(sub_anns)):
                sub_ann = sub_anns[idx]
                if isinstance(sub_ann, ast.Constant) and sub_ann.value is None:
                    # We ignore None and assume there is at least one other value in the subscript
                    continue
                next = self.check_annotation(sub_ann)
                if fst != next:
                    raise InvalidProgramException(ann, 'invalid.ghost.annotation')
            return fst

    def is_ghost_name(self, name: str) -> bool:
        """
        Returns whether the given name refers to a ghost type in the current module.
        """
        return name in self.current_module.ghost_names or name in ALL_GHOST_TYPE_NAMES

    def find_type(self, name: str) -> Optional[PythonType]:
        """
        Returns the class with the given name that is visible in the current
        module, if there is one. Used to resolve forward references.
        """
        modules = [self.current_module]
        modules.extend(self.current_module.get_included_modules(()))
        modules.append(self.global_module)
        for module in modules:
            cls = getattr(module, 'classes', {}).get(name)
            if cls is not None:
                return cls
        return None

    def get_mixed_return_parts(self, ann: Optional[annotation_t]
                               ) -> Optional[Tuple[annotation_t, annotation_t]]:
        """
        If the given return type annotation combines a regular and a ghost part,
        i.e. if it has the form Tuple[<regular type>, <ghost type>], returns the
        two parts. Returns None otherwise.
        """
        if not (isinstance(ann, ast.Subscript) and self.get_subscript_name(ann) == 'Tuple'):
            return None
        if not (isinstance(ann.slice, ast.Tuple) and len(ann.slice.elts) == 2):
            return None
        fst, snd = ann.slice.elts
        if self.check_annotation(fst) or not self.check_annotation(snd):
            return None
        return fst, snd

    def get_return_info(self, func: PythonMethod) -> return_info_t:
        """
        Returns the ghost information of the return value of the given function:
        None if it has no return type annotation, MIXED_RETURN if the annotation
        combines a regular and a ghost part, and otherwise whether the entire
        returned value is ghost.

        The annotation is interpreted in the module in which the function is
        defined, and the result is cached on the function.
        """
        cached = getattr(func, 'ghost_return_info', _UNCOMPUTED)
        if cached is not _UNCOMPUTED:
            return cached
        ann = func.node.returns if func.node is not None else None
        if self.is_ghost(func):
            info = True
        elif ann is None:
            # Interface methods have no annotation; we use the declared type.
            info = self.is_ghost_type(getattr(func, 'type', None))
        else:
            with self.module_scope(func.module):
                if self.get_mixed_return_parts(ann) is not None:
                    info = MIXED_RETURN
                else:
                    info = self.check_annotation(ann)
        func.ghost_return_info = info
        return info

    def check_call(self, call: ast.Call) -> Tuple[bool, return_info_t]:
        """
        Checks whether the call is valid in regards to ghost information. We also set the 'is_ghost', 'contains_ghost'
        and a 'is_pure' flag on the Call node.

        If the call is valid, we return whether the called function is ghost.
        If the function is regular, we additionally return the ghost information
        of its return value (see get_return_info).
        """
        func_name = get_func_name(call)
        if func_name in TRANSPARENT_CALLS and len(call.args) > TRANSPARENT_CALLS[func_name]:
            idx = TRANSPARENT_CALLS[func_name]
            res = self.is_ghost(call.args[idx]) #TODO: Should probably support keyword version
            call.is_ghost = res
            call.contains_ghost = True
            call.is_pure = True
            return res, None
        elif func_name in IO_MIXED_RETURN_FUNCS:
            # The result consists of a regular value and a place.
            call.is_ghost = False
            call.contains_ghost = True
            call.is_pure = True
            return False, MIXED_RETURN
        elif func_name in IGNORE_REG_CALLS:
            call.is_ghost = False
            call.contains_ghost = False
            call.is_pure = False
            return False, None
        elif func_name in ALL_CONTRACT_ELEMS:
            call.is_ghost = True
            call.contains_ghost = True
            call.is_pure = True
            return True, None
        elif func_name in PURE_REG_CALLS:
            return self._check_unresolved_call(call, False)


        called_func = None
        # A call on a ghost receiver may only happen in ghost code, since the
        # receiver does not exist at runtime.
        is_receiver_ghost = self.check_receiver(call)
        if isinstance(call.func, ast.Attribute):
            called_type = self.get_type(call.func.value, self.ctx)
            if isinstance(called_type, PythonClass) and called_type.name in THREADING:
                return self._check_thread_call(call)
            elif isinstance(called_type, UnionType):
                types = [t for t in called_type.get_types() if t is not None]
                funcs = [t.get_func_or_method(func_name) or t.get_predicate(func_name)
                         for t in types]
                if not funcs or None in funcs:
                    raise InvalidProgramException(call, 'invalid.ghost.call', f"Cannot resolve {func_name} of all possible types.")
                if not self.only_equivalent_signatures(funcs):
                    raise InvalidProgramException(call, 'invalid.ghost.call', "Call of function with multiple possible signatures.")
                called_func = funcs[0]

        if isinstance(call.func, ast.Subscript):
            # A generic class is instantiated, e.g. Cell[int](5). We cannot check
            # the arguments against the parameters, since their types depend on
            # the type arguments, so we only take the class itself into account.
            if self.is_ghost_type(self.get_target(call.func.value, self.ctx)):
                return self._check_ghost_func(call)
            return self._check_unresolved_call(call, is_receiver_ghost)

        if called_func is None:
            called_func = self.get_target(call.func, self.ctx)

        if isinstance(called_func, PythonIOOperation):
            # IO operations only exist during verification.
            return self._check_ghost_func(call)

        if isinstance(called_func, (PythonClass, PythonVarBase)):
            if isinstance(called_func, PythonVarBase):
                # Function stored in var is called.
                # Currently, this should only be calling classmethod's cls element
                curr_cls = self.ctx.current_class
            else:
                # Instantiation of the class
                curr_cls = called_func

            # We resolve this as a call to __init__
            init = None
            while curr_cls is not None and curr_cls.name != OBJECT_TYPE:
                init = curr_cls.get_func_or_method('__init__')
                if init is not None:
                    break
                curr_cls = curr_cls.superclass
            if init is None:
                # Empty object init
                res = self.is_ghost(called_func) or self.in_ghost_ctx or is_receiver_ghost
                call.is_ghost = res
                call.contains_ghost = res
                call.is_pure = True
                return res, None
            # Constructor calls return an instance of the class, not the result
            # of __init__, so we remember the ghost information of the class here.
            is_class_ghost = self.is_ghost(called_func)
            called_func = init
        else:
            is_class_ghost = False

        if not isinstance(called_func, PythonMethod):
            # Nagini resolves some calls (e.g. to builtins) only during translation.
            # We conservatively treat those as pure regular functions, i.e. the call
            # is ghost exactly if one of its arguments or its receiver is ghost.
            return self._check_unresolved_call(call, is_receiver_ghost)

        is_func_ghost = self.is_ghost(called_func) or is_class_ghost
        is_func_pure = called_func.pure
        call.is_pure = is_func_pure

        # We cannot call an impure regular function in a ghost context, since
        # removing the ghost code would remove its effect as well.
        if self.in_ghost_ctx or is_receiver_ghost:
            if not is_func_ghost and not is_func_pure:
                current_function = self.ctx.current_function
                if current_function is not None and current_function.pure:
                    # Report the more specific error Nagini uses for this case.
                    raise InvalidProgramException(call, 'purity.violated')
                raise InvalidProgramException(
                    call, 'invalid.ghost.call',
                    f"Cannot call the impure function {func_name} in ghost code.")
            # The function is either already ghost or is pure and now used as ghost
            is_func_ghost = True

        if is_func_ghost:
            return self._check_ghost_func(call)

        contains_ghost = False

        # Get expected parameters
        params = OrderedDict(called_func.args)
        if called_func.cls is not None and not called_func.method_type == MethodType.static_method \
                and params:
            # class function: ignore self argument
            params.popitem(last=False)
        # Arguments which are passed to a variadic parameter must all be regular,
        # which is already guaranteed by the check of the function definition.
        has_variadic_params = len(called_func.special_args) > 0

        # Get actual arguments
        args: list[ast.expr | bool] = []
        for arg in call.args:
            if isinstance(arg, ast.Starred):
                if isinstance(arg.value, ast.Call):
                    raise InvalidProgramException(arg, 'invalid.ghost.starred', "Do not use a star to unpack calls. Use an assignment instead.")
                    #TODO: Allow reg only and maybe ghost only returns to be unpacked with *
                #TODO: We currently assume the starred object to be a variable. This is not necessarily true
                is_var_ghost = self.is_ghost(arg.value)
                var_type = self.get_type(arg.value, self.ctx)
                nof_elements = len(var_type.type_args) if isinstance(var_type, GenericType) else 1
                for _ in range(nof_elements):
                    args.append(is_var_ghost)
                arg.is_ghost = is_var_ghost
                arg.contains_ghost = is_var_ghost
            else:
                args.append(arg)

        if len(args) > len(params) and not has_variadic_params:
            # More arguments than parameters can only happen for calls which
            # Nagini rejects later on; nothing to check here.
            args = args[:len(params)]

        # Check positional arguments
        for index, arg in enumerate(args):
            if index >= len(params):
                # Argument is passed to a variadic parameter, which is always regular.
                if self.is_ghost(arg):
                    raise InvalidProgramException(call, 'invalid.ghost.call')
                continue
            param = list(params.values())[index]
            is_param_ghost = self.is_ghost(param)
            if is_param_ghost:
                old_ctx = self.in_ghost_ctx
                self.in_ghost_ctx = True
            if not self.is_assignable(arg, param):
                # Reg input was expected but got ghost input.
                # If func is pure, we use it as ghost. Otherwise, the call is invalid
                if is_param_ghost:
                    self.in_ghost_ctx = old_ctx
                if is_func_pure:
                    return self._check_ghost_func(call)
                else:
                    raise InvalidProgramException(call, 'invalid.ghost.call')
            if is_param_ghost:
                self.in_ghost_ctx = old_ctx
                contains_ghost = True

        # Check keyword arguments
        for kw in call.keywords:
            if kw.arg is None or kw.arg not in params:
                # Variadic keywords, which are always regular.
                if self.is_ghost(kw.value):
                    raise InvalidProgramException(call, 'invalid.ghost.call')
                continue
            param = params[kw.arg]

            is_param_ghost = self.is_ghost(param)
            if is_param_ghost:
                old_ctx = self.in_ghost_ctx
                self.in_ghost_ctx = True
            if not self.is_assignable(kw.value, param):
                # Reg input was expected but got ghost input.
                # If func is pure, we use it as ghost. Otherwise, the call is invalid
                if is_param_ghost:
                    self.in_ghost_ctx = old_ctx
                if is_func_pure:
                    return self._check_ghost_func(call)
                else:
                    raise InvalidProgramException(call, 'invalid.ghost.call')
            if is_param_ghost:
                self.in_ghost_ctx = old_ctx
                contains_ghost = True

        call.is_ghost = False
        call.contains_ghost = contains_ghost

        return False, self.get_return_info(called_func)

    def _check_thread_call(self, call: ast.Call) -> Tuple[bool, return_info_t]:
        """
        Handles calls of the methods of Thread objects, which Nagini translates
        specially. Their arguments must all be regular.
        """
        contains_ghost = False
        arguments = list(call.args) + [kw.value for kw in call.keywords]
        for argument in arguments:
            if self.is_ghost(argument):
                raise InvalidProgramException(
                    call, 'invalid.ghost.call',
                    "Threads cannot be used with ghost values.")
            contains_ghost = contains_ghost or argument.contains_ghost
        call.is_ghost = False
        call.contains_ghost = contains_ghost
        call.is_pure = False
        return False, None

    def check_receiver(self, call: ast.Call) -> bool:
        """
        Determines whether the receiver of the given call (if any) is ghost.
        Module qualified calls like 'mod.foo()' do not have a receiver.
        """
        if not isinstance(call.func, ast.Attribute):
            return False
        receiver = call.func.value
        if isinstance(receiver, (ast.Name, ast.Attribute)) and \
                isinstance(self.get_target(receiver, self.ctx), PythonModule):
            return False
        return self.is_ghost(receiver)

    def _check_unresolved_call(self, call: ast.Call,
                               is_receiver_ghost: bool) -> Tuple[bool, return_info_t]:
        """
        Handles calls whose target Nagini only resolves during translation, e.g.
        calls to some builtins. We treat them like pure regular functions.
        """
        is_func_ghost = is_receiver_ghost or self.in_ghost_ctx
        for arg in call.args:
            is_func_ghost = self.is_ghost(arg) or is_func_ghost
        for kw in call.keywords:
            is_func_ghost = self.is_ghost(kw.value) or is_func_ghost
        call.is_ghost = is_func_ghost
        call.contains_ghost = is_func_ghost
        call.is_pure = True
        return is_func_ghost, None

    def only_equivalent_signatures(self, funcs: List[PythonMethod]) -> bool:
        """
        Returns whether all given functions agree on the ghost information of
        their arguments and of their return value, so that a call which may
        dispatch to any of them can be checked against the first one.
        """
        if len(funcs) < 2:
            return True
        fst = funcs[0]
        is_fst_ghost = self.is_ghost(fst)
        fst_return_info = self.get_return_info(fst)
        for next_func in funcs[1:]:
            # Compare ghost type and args of funcs
            if is_fst_ghost != self.is_ghost(next_func) or len(fst.args) != len(next_func.args):
                return False
            for fst_arg, next_arg in zip(fst.args.values(), next_func.args.values()):
                if self.is_ghost(fst_arg) != self.is_ghost(next_arg):
                    return False

            # Compare returns of funcs
            if not is_fst_ghost and fst_return_info != self.get_return_info(next_func):
                return False

        return True

    def _check_ghost_func(self, call: ast.Call) -> Tuple[bool, return_info_t]:
        # Ghost func calls accept all arguments and have no (informative) return.
        # However, we still need to check that there are no impure regular function calls in its arguments.
        old_ctx = self.in_ghost_ctx
        self.in_ghost_ctx = True
        self.check_for_call(call)
        self.in_ghost_ctx = old_ctx

        call.is_ghost = True
        call.contains_ghost = True
        return True, None

    def is_assignable(self, e1, e2, allow_conversion: bool = True) -> bool:
        """
        Returns whether e1 may be assigned to e2 in regards to ghost information.
        You may pass a boolean for either e1 or e2 instead when you already know whether they are ghost.

        If a regular element e1 is assigned to a ghost e2, we call this conversion. 
        Whether this should be considered valid can be configured via the allow_conversion boolean.

        If e1 is an AST node, we also update the is_ghost and contains_ghost flags during conversion.
        The exception to this is if e1 is an impure function call.
        """
        is_e1_ghost = self.is_ghost(e1)
        is_e2_ghost = self.is_ghost(e2)

        is_conversion = not is_e1_ghost and is_e2_ghost
        is_e1_impure_call = isinstance(e1, ast.Call) and not e1.is_pure
        if allow_conversion and is_conversion and isinstance(e1, ast.AST) and not is_e1_impure_call:
            e1.is_ghost = True
            e1.contains_ghost = True

        may_assign = (allow_conversion and is_conversion) or (is_e1_ghost == is_e2_ghost)
        in_this_ctx = (not self.in_ghost_ctx) or is_e2_ghost
        return may_assign and in_this_ctx
    
    def is_ghost(self, elem) -> bool:
        """
        Returns whether the given elem is ghost.
        Elements which are ghost are only used during verification.

        When a boolean is passed as elem, it returns the same boolean. 
        As such, you can replace the element with a boolean when you already know whether it is ghost.

        If given an AST node, this function also sets a "is_ghost" and a "contains_ghost" flag on it, 
        which are used for the termination analysis and the extraction.
        """
        if isinstance(elem, bool):
            return elem
        elif isinstance(elem, PythonVarBase):
            # A variable is ghost if it was declared as such or if its type only
            # exists during verification.
            return elem.is_ghost or self.is_ghost_type(elem.type)
        elif isinstance(elem, PythonField):
            # A field is ghost if it was declared as such, if its type only
            # exists during verification, or if its class is ghost.
            return (elem.is_ghost or self.is_ghost_type(elem.type) or
                    (elem.cls is not None and elem.cls.is_ghost))
        elif isinstance(elem, PythonMethod):
            if self.is_library_module(elem.module):
                # Nagini's contract library uses the Ghost decorator with its
                # original meaning, i.e. only to indicate that calls have no
                # effect at runtime. Its functions are not ghost code.
                return False
            return elem.is_ghost
        elif isinstance(elem, PythonIOOperation):
            # IO operations only exist during verification.
            return True
        elif isinstance(elem, PythonType):
            return self.is_ghost_type(elem)
        elif isinstance(elem, PythonModule):
            return False
        elif isinstance(elem, ast.AST) and hasattr(elem, 'is_ghost'):
            return elem.is_ghost
        elif isinstance(elem, ast.expr):
            return self._is_expr_ghost(elem)
        raise UnsupportedException(elem, f"Unsupported Ghost resolution of type {type(elem)}")

    def is_ghost_type(self, type: Optional[PythonType]) -> bool:
        """
        Returns whether values of the given type only exist during verification,
        i.e. whether the type is a ghost class or one of Nagini's built-in ghost
        types like PSeq.
        """
        if type is None:
            return False
        if isinstance(type, UnionType):
            return any([self.is_ghost_type(t) for t in type.get_types() if t is not None])
        if isinstance(type, GenericType):
            # A container of ghost values is itself ghost.
            if any([self.is_ghost_type(arg) for arg in type.type_args]):
                return True
            type = type.python_class
        if isinstance(type, PythonClass):
            return type.is_ghost or type.name in ALL_GHOST_TYPE_NAMES
        return False

    def _is_expr_ghost(self, expr: ast.Expr) -> bool:
        if isinstance(expr, ast.BoolOp):
            items = expr.values
            res = any([self.is_ghost(e) for e in items])
        elif isinstance(expr, ast.BinOp):
            left_b = self.is_ghost(expr.left)
            right_b = self.is_ghost(expr.right)
            res = left_b or right_b
            items = [expr.left, expr.right]
        elif isinstance(expr, ast.UnaryOp):
            items = [expr.operand]
            res = self.is_ghost(expr.operand)
        elif isinstance(expr, ast.Lambda):
            old_ctx = self.in_ghost_ctx
            self.in_ghost_ctx = True
            self.check_for_call(expr.value)
            self.in_ghost_ctx = old_ctx

            items = []
            res = True        
        elif isinstance(expr, ast.IfExp):
            items = [expr.test, expr.body, expr.orelse]
            res = any([self.is_ghost(e) for e in items])
        elif isinstance(expr, ast.Dict):
            items = expr.keys + expr.values
            res = any([self.is_ghost(e) for e in items if e is not None])
        elif isinstance(expr, ast.Set):
            items = expr.elts
            res = any([self.is_ghost(e) for e in items])
        elif isinstance(expr, (ast.DictComp, ast.ListComp, ast.SetComp, ast.GeneratorExp)):
            if len(expr.generators) != 1 or expr.generators[0].ifs:
                # Nagini does not support these and reports that itself; we only
                # have to be conservative about the ghost information here.
                items = [generator.iter for generator in expr.generators]
                res = any([self.is_ghost(item) for item in items])
                expr.is_ghost = res
                self.set_contains_ghost(expr, res, *items)
                return res

            # Create alias for loop variable
            name = construct_lambda_prefix(expr.lineno, expr.col_offset)
            target = expr.generators[0].target
            local_name = name + '$' + target.id
            element_var = self.ctx.actual_function.special_vars[local_name]
            self.ctx.set_alias(target.id, element_var)
            
            gen = expr.generators[0].iter
            is_gen_ghost = self.is_ghost(gen)
            target.contains_ghost = is_gen_ghost
            element_var.is_ghost = is_gen_ghost
            if isinstance(expr, ast.DictComp):
                is_elt_ghost = self.is_ghost(expr.key) or self.is_ghost(expr.value)
                items = [expr.key, expr.value, gen]
            else:
                is_elt_ghost = self.is_ghost(expr.elt)
                items = [expr.elt, gen]

            self.ctx.remove_alias(target.id)
            res = is_gen_ghost or is_elt_ghost
        elif isinstance(expr, ast.JoinedStr):
            # A formatted string is ghost if one of its interpolated values is.
            items = expr.values
            res = any([self.is_ghost(e) for e in items])
        elif isinstance(expr, ast.FormattedValue):
            items = [e for e in (expr.value, expr.format_spec) if e is not None]
            res = any([self.is_ghost(e) for e in items])
        elif isinstance(expr, ast.Await):
            items = [expr.value]
            res = self.is_ghost(expr.value)
        elif isinstance(expr, ast.Compare):
            items = [expr.left] + expr.comparators
            res = any([self.is_ghost(e) for e in items])
        elif isinstance(expr, ast.Call):
            is_func_ghost, ret_info = self.check_call(expr)
            # A return value which has a ghost part may only be used as a whole
            # in ghost code.
            return is_func_ghost or ret_info is True or ret_info == MIXED_RETURN
        elif isinstance(expr, ast.Constant):
            items = []
            res = False
        elif isinstance(expr, ast.Attribute):
            items = []
            res = self.resolve_target_ghost(expr)
        elif isinstance(expr, ast.Subscript):
            name = self.get_subscript_name(expr)
            if name in ["Union", "Tuple"] and isinstance(expr.slice, ast.Tuple):
                items = expr.slice.elts
                res = any([self.is_ghost(e) for e in items])
            elif name in ["Optional", "List"]:
                items = [expr.slice]
                res = self.is_ghost(expr.slice)
            else:
                # Subscripting a ghost collection, or indexing with a ghost
                # value, yields a ghost value.
                items = [expr.value, expr.slice]
                res = any([self.is_ghost(e) for e in items])
        elif isinstance(expr, ast.Slice):
            items = [e for e in (expr.lower, expr.upper, expr.step) if e is not None]
            res = any([self.is_ghost(e) for e in items])
        elif isinstance(expr, ast.Starred):
            if isinstance(expr.value, ast.Call):
                raise InvalidProgramException(expr, 'invalid.ghost.starred', "Do not use a star to unpack calls. Use an assignment instead.")
            items = [expr.value]
            res = self.is_ghost(expr.value)
        elif isinstance(expr, ast.Name):
            items = []
            if self.is_ghost_name(expr.id):
                res = True
            elif expr.id in self.current_module.type_vars:
                res = False
            else:
                res = self.resolve_target_ghost(expr)
        elif isinstance(expr, (ast.List, ast.Tuple)):
            items = expr.elts
            res = any([self.is_ghost(e) for e in items])
        else:
            raise UnsupportedException(expr, f"Unsupported Expression of type {type(expr)}")
        
        expr.is_ghost = res
        self.set_contains_ghost(expr, res, *items)
        return res

    def resolve_target_ghost(self, expr: Union[ast.Name, ast.Attribute]) -> bool:
        """
        Returns whether the given name or attribute refers to a ghost element.
        Some elements (e.g. exception variables or builtins) are only resolved
        during translation; for those we fall back to the static type of the
        expression.
        """
        target = self.get_target(expr, self.ctx)
        if target is not None:
            return self.is_ghost(target)
        return self.is_ghost_type(self.get_type(expr, self.ctx))

    def set_contains_ghost(self, node: ast.AST, is_node_ghost: bool, *sub_exprs: ast.AST) -> None:
        node.contains_ghost = is_node_ghost or any(
            [sub_expr.contains_ghost for sub_expr in sub_exprs if isinstance(sub_expr, ast.AST)]
            )

    def has_mixed_elems(self, elems: List[ast.expr]) -> bool:
        if len(elems) < 2:
            return False

        is_fst_ghost = self.is_ghost(elems[0])
        for e in elems[1:]:
            if self.is_ghost(e) != is_fst_ghost:
                return True
        return False

    def get_subscript_name(self, sub: ast.Subscript) -> Optional[str]:
        return sub.value.id if isinstance(sub.value, ast.Name) else None

    def get_target(self, node: ast.AST, ctx: Context) -> Optional[PythonNode]:
        container = ctx.actual_function if ctx.actual_function else ctx.module
        containers = [ctx]
        if ctx.current_class:
            containers.append(ctx.current_class)
        if isinstance(container, (PythonMethod, PythonIOOperation)):
            containers.append(container)
            containers.extend(container.module.get_included_modules())
        else:
            # Assume module
            containers.extend(container.get_included_modules(()))
        result = do_get_target(node, containers, container)
        return result

    def get_type(self, node: ast.AST, ctx: Context) -> Optional[PythonType]:
        """
        Returns the type of the expression represented by node as a PythonType,
        or None if the type is void.
        """
        container = ctx.actual_function if ctx.actual_function else ctx.module
        containers = [ctx]
        if ctx.current_class:
            containers.append(ctx.current_class)
        if isinstance(container, (PythonMethod, PythonIOOperation)):
            containers.append(container)
            containers.extend(container.module.get_included_modules())
        else:
            # Assume module
            containers.extend(container.get_included_modules())
        return do_get_type(node, containers, container)