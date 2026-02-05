"""
Copyright (c) 2025 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
import ast
from typing import List, Optional, Union, Tuple, Callable

from nagini_contracts.contracts import (
    CONTRACT_FUNCS, GHOST_BUILTINS, CONTRACT_WRAPPER_FUNCS, 
    CONTRACT_DECORATORS, SPECIAL_PREDICATES
    )
from nagini_contracts.io_contracts import (
    BUILTIN_IO_OPERATIONS, IO_CONTRACT_FUNCS, 
    IO_OPERATION_PROPERTY_FUNCS, IO_FUNCS, IO_DECORATORS
    )
from nagini_translation.lib.constants import OBJECT_TYPE, THREADING
from nagini_translation.lib.program_nodes import (
    PythonModule, PythonType, PythonMethod, PythonIOOperation, 
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

ALL_CONTRACT_ELEMS = (CONTRACT_FUNCS + CONTRACT_WRAPPER_FUNCS + THREADING +
                        IO_CONTRACT_FUNCS + IO_OPERATION_PROPERTY_FUNCS +
                        list(BUILTIN_IO_OPERATIONS) + IO_FUNCS + SPECIAL_PREDICATES)

NAGINI_DECORATORS = CONTRACT_DECORATORS + IO_DECORATORS

# Nagini functions which can be used in a regular context, when the given Nth argument is regular
TRANSPARENT_CALLS = {'Unfolding': 1, 'Reveal': 0}

IGNORE_REG_CALLS = ['TypeVar']

PURE_REG_CALLS = ['len', 'isinstance']

NAGINI_IMPORT = 'nagini_contracts'

class GhostChecker(ast.NodeVisitor):
    """
    Walks through the Python AST and checks for ill-formed ghost elements.
    """
    
    def __init__(self, modules: List[PythonModule]) -> None:
        self.modules = modules
        self.ctx = None
        self.in_ghost_ctx = False

    def check(self, ctx: Context) -> None:
        """
        Checks the defined modules for valid ghost information in the given context.
        It also stores additional ghost information on AST nodes, which is used for 
        the Termination analysis and the extraction.
        """
        # global_module = self.modules[0]
        main_module = self.modules[1]
        self.ctx = ctx
        self.visit(main_module.node)

    def generic_visit(self, node: ast.AST) -> None:
        node.is_ghost = self.in_ghost_ctx
        node.contains_ghost = self.in_ghost_ctx
        super().generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        current_class: PythonClass = self.modules[1].classes[node.name]
        self.ctx.current_class = current_class
        old_ghost_ctx = self.in_ghost_ctx # TODO: Do we need to define classes within ghost context? 
        self.in_ghost_ctx = current_class.is_ghost

        # Classes may only have explicit bases of the same ghost type, 
        # i.e. ghost classes only have explicit ghost bases (and the implicit object base).
        OBJECT_NAME = ast.Name(OBJECT_TYPE, None) #TODO: Does a cleaner solution exist?
        object_class = self.get_target(OBJECT_NAME, self.ctx)
        superclass = current_class.superclass
        if not (superclass == object_class or superclass.is_ghost == current_class.is_ghost):
            raise InvalidProgramException(node, "invalid.ghost.classDef")

        for stmt in node.body:
            self.visit(stmt)

        self.in_ghost_ctx = old_ghost_ctx
        self.ctx.current_class = None
        node.is_ghost = current_class.is_ghost
        self.set_contains_ghost(node, current_class.is_ghost, *node.body)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        # Functions with the following decorators are assumed valid or are verified later, so we just proceed
        IGNORE_DECORATORS = ['ContractOnly', 'IOOperation', 'Predicate']
        decorators = {d.id for d in node.decorator_list if isinstance(d, ast.Name)}
        if any([dec in IGNORE_DECORATORS for dec in decorators]):
            is_func_ghost = 'Ghost' in decorators
            node.is_ghost = is_func_ghost
            node.contains_ghost = True
            return
        
        # Resolve created function
        if 'property' in decorators:
            if not isinstance(self.ctx.current_class, PythonClass):
                raise InvalidProgramException(node, 'invalid.property', "Property outside of class.")
            current_function = self.ctx.current_class.get_field(node.name)
        else:
            scope = self.ctx.current_class if self.ctx.current_class else self.modules[1]
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
            
            # Variadic arguments must be regular
            for arg in [node.args.vararg, node.args.kwarg]:
                if arg is not None and arg.annotation is not None and self.check_annotation(arg.annotation):
                    raise InvalidProgramException(arg, 'invalid.ghost.annotation')
            
            # The return must be None, a Tuple[only_reg, only_ghost] or clearly regular or ghost
            return_ann = node.returns
            if isinstance(return_ann, ast.Constant) and return_ann.value is None:
                return_ann.is_ghost = False
                return_ann.contains_ghost = False
            elif isinstance(return_ann, ast.Subscript) and \
                self.get_subscript_name(return_ann) == 'Tuple' and len(return_ann.slice.elts) == 2:
                is_fst_ghost = self.check_annotation(return_ann.slice.elts[0])
                is_snd_ghost = self.check_annotation(return_ann.slice.elts[1])
                if is_fst_ghost and not is_snd_ghost:
                    raise InvalidProgramException(return_ann, 'invalid.ghost.annotation')
                return_ann.is_ghost = is_fst_ghost and is_snd_ghost
                return_ann.contains_ghost = is_snd_ghost
                contains_ghost = contains_ghost or is_snd_ghost
            else:
                ann_type = self.check_annotation(return_ann)
                return_ann.is_ghost = ann_type
                return_ann.contains_ghost = ann_type
                contains_ghost = contains_ghost or ann_type
        else:
            # All elements must be ghost, so annotations do not need to be further analyzed.
            # However, the function may not have variadic arguments
            if node.args.vararg is not None or node.args.kwarg is not None:
                raise InvalidProgramException(node, 'invalid.ghost.functionDef')
            contains_ghost = True

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
                raise InvalidProgramException(node, 'invalid.ghost.return')
            expect_ret = self.ctx.current_function.node.returns
            contains_ghost = False
            if node.value is None:
                # Returning nothing cannot be invalid or mypy would throw error
                pass  
            elif isinstance(node.value, ast.Tuple):
                expect_list = expect_ret.slice.elts
                index = 0
                for ret in node.value.elts:
                    expect_ret = expect_list[index]
                    expect_type = self.check_annotation(expect_ret)
                    if not self.is_assignable(ret, expect_type):
                        raise InvalidProgramException(node, 'invalid.ghost.return')
                    contains_ghost = contains_ghost or expect_type
                    index += 1
            else:
                expect_type = self.check_annotation(expect_ret)
                if not self.is_assignable(node.value, expect_type):
                    raise InvalidProgramException(node, 'invalid.ghost.return')
                contains_ghost = expect_type
        
            node.is_ghost = False
            self.set_contains_ghost(node, contains_ghost)

    def visit_Delete(self, node: ast.Delete): #TODO: Add constraint: Each del may target elems of same ghost type
        if self.in_ghost_ctx:
            for target in node.targets:
                if not self.is_ghost(target):
                    raise InvalidProgramException(node, 'invalid.ghost.delete')
        
        is_node_ghost = all([self.is_ghost(target) for target in node.targets])
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
            if isinstance(target, ast.Tuple):
                all_targets.extend(target.elts)
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

        is_node_ghost = is_node_definitively_ghost or (is_target_ghost and node.value.is_pure)
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
            return
        self.check_assign(node.value, node.target)

        if is_node_definitively_ghost:
            self.in_ghost_ctx = old_ctx

        is_node_ghost = is_node_definitively_ghost or (is_target_ghost and node.value.is_pure)
        node.is_ghost = is_node_ghost
        self.set_contains_ghost(node, is_node_ghost, node.value, node.target)

    def check_assign(self, value: Union[ast.expr, bool], target: ast.expr) -> None:        
        if isinstance(target, (ast.Name, ast.Attribute)):
            if not self.is_assignable(value, target):
                raise InvalidProgramException(target, 'invalid.ghost.assign')
        else:
            assert isinstance(target, ast.Subscript), f"Unexpected type of {type(target)}"
            # The subscript of a ghost element may only be read
            if self.is_ghost(target) or self.is_ghost(value):
                raise InvalidProgramException(target, 'invalid.ghost.assign')

    def check_unpacking(self, value: Union[ast.expr, bool], target: Union[ast.List, ast.Tuple]) -> None:
        unpacked = target.elts

        if isinstance(value, ast.Name):
            # simple variable unpacking
            is_var_ghost = self.is_ghost(value)
            for sub_target in unpacked:
                if not self.is_assignable(is_var_ghost, sub_target):
                    raise InvalidProgramException(sub_target, 'invalid.ghost.assign')
            is_target_ghost = all([self.is_ghost(sub_target) for sub_target in unpacked])
            target.is_ghost = is_target_ghost
            self.set_contains_ghost(target, is_target_ghost, *unpacked)
            return
        elif isinstance(value, (ast.Tuple, ast.List)):
            values = value.elts
        elif isinstance(value, ast.Subscript):
            # Tuple/List annotation from call 
            values = value.slice.elts
        elif isinstance(value, ast.Call):
            is_func_ghost, ret_type = self.check_call(value)
            if ret_type is None:
                values = [False] * len(unpacked)
            elif is_func_ghost:
                values = [True] * len(ret_type.slice.elts)
            else:
                values = ret_type.slice.elts
        else:
            assert isinstance(value, bool), f"Unexpected type of {type(value)}"
            values = [value] * len(unpacked)
        
        if any(isinstance(item, ast.Starred) for item in unpacked):
            # For simplicity, we only allow starred unpacking in regular code
            items = unpacked + values
            for item in items:
                if self.is_ghost(item):
                    raise InvalidProgramException(item, 'invalid.ghost.unpacking')
            target.is_ghost = False
            self.set_contains_ghost(target, False, *items)
        else:
            for sub_target, sub_value in zip(unpacked, values):
                if isinstance(sub_target, (ast.List, ast.Tuple)):
                    self.check_unpacking(sub_value, sub_target)
                else:
                    self.check_assign(sub_value, sub_target)
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
            self.call_on_vars(node.target, set_var_ghost)
        else:
            # We do not allow loop vars to be defined ghost elsewhere
            def check_var(var: PythonVarBase) -> None:
                if var.is_ghost:
                    raise InvalidProgramException(node, 'invalid.ghost.For')
            self.call_on_vars(node.target, check_var)
        self.check_control_flow(is_iter_ghost, node.iter, node.body, node.orelse)

        node.is_ghost = is_iter_ghost
        self.set_contains_ghost(node, is_iter_ghost, node.iter, *node.body, *node.orelse)

    def call_on_vars(self, expr: Union[ast.Name, ast.Tuple, ast.List], f: Callable[[PythonVarBase], None]):
        if isinstance(expr, ast.Name):
            var = self.get_target(expr, self.ctx)
            assert isinstance(var, PythonVarBase), f"Unexpected type of {type(var)}"
            f(var)
        else:
            assert isinstance(expr, (ast.Tuple, ast.List)), f"Unexpected type of {type(expr)}"
            for e in expr.elts:
                self.call_on_vars(e, f)

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
        self.set_contains_ghost(node, False)

    def visit_Raise(self, node: ast.Raise):
        if self.in_ghost_ctx:
            raise InvalidProgramException(node, 'invalid.ghost.raise')

        node.is_ghost = False
        self.set_contains_ghost(node, False)

    def visit_Assert(self, node: ast.Assert):
        is_test_ghost = self.is_ghost(node.test)
        is_msg_ghost = self.is_ghost(node.msg) if node.msg is not None else False
        if self.in_ghost_ctx or is_test_ghost or is_msg_ghost:
            raise InvalidProgramException(node, 'invalid.ghost.assert', "Use the Assert contract function when working with ghost elements.")
        
        node.is_ghost = False
        self.set_contains_ghost(node, False)

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
            raise InvalidProgramException(node, 'invalid.ghost.break')
        node.is_ghost = False
        node.contains_ghost = False
    
    def visit_Continue(self, node: ast.Continue):
        if self.in_ghost_ctx:
            raise InvalidProgramException(node, 'invalid.ghost.continue')
        node.is_ghost = False
        node.contains_ghost = False

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if NAGINI_IMPORT in node.module.split('.'):
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
            return ann.id in self.modules[1].ghost_names or ann.id in GHOST_BUILTINS
        elif isinstance(ann, ast.Constant):
            # Must be valid or mypy would throw error
            return ann.value in self.modules[1].ghost_names or ann.value in GHOST_BUILTINS
        elif isinstance(ann, ast.Attribute):
            # Must be valid or mypy would throw error. Find module and check for ghost name
            mod: Optional[PythonModule] = self.get_target(ann.value, self.ctx)
            if mod is None:
                raise InvalidProgramException(ann, 'invalid.ghost.annotation', f"Couldn't correctly resolve module {ann.value.id}")
            return ann.attr in mod.ghost_names
        else: 
            assert isinstance(ann, ast.Subscript), f"Unexpected type of {type(ann)}"
            if isinstance(ann.slice, (ast.Name, ast.Subscript)): #TODO: Find cleaner way to deal with subscripts?
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

    def check_call(self, call: ast.Call) -> Tuple[bool, Optional[annotation_t]]:
        """
        Checks whether the call is valid in regards to ghost information. We also set the 'is_ghost', 'contains_ghost' 
        and a 'is_pure' flag on the Call node.

        If the call is valid, we return whether the called function is ghost. 
        If the function is regular and has an annotation for its return type, we return the annotation as well.
        """     
        func_name = get_func_name(call)
        if func_name in TRANSPARENT_CALLS:
            idx = TRANSPARENT_CALLS[func_name]
            res = self.is_ghost(call.args[idx]) #TODO: Should support keyword version
            call.is_ghost = res
            call.contains_ghost = True
            call.is_pure = True
            return res, None
        elif func_name in ALL_CONTRACT_ELEMS:
            call.is_ghost = True
            call.contains_ghost = True
            call.is_pure = True
            return True, None
        elif func_name in IGNORE_REG_CALLS:
            call.is_ghost = False
            call.contains_ghost = False
            call.is_pure = False
            return False, None
        elif func_name in PURE_REG_CALLS:
            is_func_ghost = False
            for arg in call.args:
                is_func_ghost = is_func_ghost or self.is_ghost(arg)
            for kw in call.keywords:
                is_func_ghost = is_func_ghost or self.is_ghost(kw)
            call.is_ghost = is_func_ghost
            call.contains_ghost = is_func_ghost
            call.is_pure = True
            return is_func_ghost, None
        
        called_func = None
        if isinstance(call.func, ast.Attribute):
            called_type = self.get_type(call.func.value, self.ctx)
            if isinstance(called_type, PythonClass) and called_type.name in THREADING: #TODO: Thread should not be (automatically) ghost
                call.is_ghost = True
                call.contains_ghost = True
                call.is_pure = True
                return True, None
            if isinstance(called_type, UnionType):
                types = called_type.get_types()
                funcs = [t.get_func_or_method(func_name) for t in types]
                if None in funcs:
                    raise InvalidProgramException(call, 'invalid.ghost.call', f"Cannot resolve {func_name} of all possible types.")
                if not self.only_equivalent_signatures(funcs):
                    raise InvalidProgramException(call, 'invalid.ghost.call', "Call of function with multiple possible signatures.")
                called_func = funcs[0]
        
        if called_func is None:
            called_func = self.get_target(call.func, self.ctx)

        if isinstance(called_func, PythonClass):
            # Instantiation of the class: We resolve it as a call to __init__
            curr_cls = called_func
            while curr_cls is not None:
                if curr_cls.name == OBJECT_TYPE:
                    # Empty object init
                    res = self.is_ghost(called_func)
                    call.is_ghost = res
                    call.contains_ghost = res
                    call.is_pure = True
                    return res, None
                init = curr_cls.get_func_or_method('__init__')
                if init is None:
                    curr_cls = curr_cls.superclass
                else:
                    called_func = init
                    break
        elif isinstance(called_func, PythonVarBase):
            pass #TODO: Function stored in var is called, e.g. calling classmethod's cls element

        if not isinstance(called_func, PythonMethod):
            raise InvalidProgramException(call, 'invalid.ghost.call', f"Couldn't correctly resolve function {func_name}")

        is_func_ghost = self.is_ghost(called_func)
        is_func_pure = called_func.pure
        call.is_pure = is_func_pure

        # We cannot call a regular function in a ghost context
        if self.in_ghost_ctx:
            if not is_func_ghost and not is_func_pure:
                raise InvalidProgramException(call, 'invalid.ghost.call')
            # The function is either already ghost or is pure and now used as ghost
            is_func_ghost = True

        # Ghost func calls accept all arguments and have no (informative) return
        # However, we still need to check that there is no impure regular function in its arguments
        if is_func_ghost:
            old_ctx = self.in_ghost_ctx
            self.in_ghost_ctx = True
            self.check_for_call(call)
            self.in_ghost_ctx = old_ctx

            call.is_ghost = True
            call.contains_ghost = True
            return True, None
        
        contains_ghost = False

        # Get expected parameters
        params = called_func.args
        if called_func.cls is not None:
            # class function: ignore self argument
            params = OrderedDict(params)
            params.popitem(last=False)
        
        # Get actual arguments
        args: list[ast.expr | bool] = []
        for arg in call.args:
            if isinstance(arg, ast.Starred):
                if isinstance(arg.value, ast.Name):
                    var: PythonVarBase = self.get_target(arg.value, self.ctx) #TODO
                    assert var.type.name in ['tuple', 'list']
                    is_var_ghost = self.is_ghost(var)
                    for _ in range(len(var.type.type_args)):
                        args.append(is_var_ghost)
                    arg.is_ghost = is_var_ghost
                    arg.contains_ghost = is_var_ghost
                elif isinstance(arg.value, ast.Call):
                    raise InvalidProgramException(arg, 'invalid.ghost.starred', "Do not use a star to unpack calls. Use an assignment instead.")
                else:
                    raise UnsupportedException(arg, f"Starred argument of type {type(arg)}")
            else:
                args.append(arg)
        
        # Check positional arguments
        for arg, param in zip(args, params.values()):
            is_param_ghost = self.is_ghost(param)
            if is_param_ghost:
                old_ctx = self.in_ghost_ctx
                self.in_ghost_ctx = True
            if not self.is_assignable(arg, param):
                raise InvalidProgramException(call, 'invalid.ghost.call')
            if is_param_ghost:
                self.in_ghost_ctx = old_ctx
                contains_ghost = True
        
        # Check keyword arguments
        for kw in call.keywords:
            if kw.arg is None:
                # Assume **kwargs
                raise UnsupportedException(kw, "Giving variadic keywords") #TODO
            param = params[kw.arg]

            is_param_ghost = self.is_ghost(param)
            if is_param_ghost:
                old_ctx = self.in_ghost_ctx
                self.in_ghost_ctx = True
            if not self.is_assignable(kw.value, param):
                raise InvalidProgramException(call, 'invalid.ghost.call')
            if is_param_ghost:
                self.in_ghost_ctx = old_ctx
                contains_ghost = True

        call.is_ghost = False
        call.contains_ghost = contains_ghost

        # Find the return type
        ret_type = called_func.node.returns if called_func.node is not None else None
        return False, ret_type
        
    def only_equivalent_signatures(self, funcs: List[PythonMethod]) -> bool:
        if len(funcs) < 2:
            return True
        fst = funcs[0]
        is_fst_ghost = self.is_ghost(fst)
        # is_fst_return_ghost = is_fst_ghost or self.check_annotation(fst.node.returns)
        for idx in range(1, len(funcs)):
            next_func = funcs[idx]
            if is_fst_ghost != self.is_ghost(next_func) or len(fst.args) != len(next_func.args):
                return False
            for fst_arg, next_arg in zip(fst.args, next_func.args):
                pass #TODO
            #TODO: Return types
        return True

    def is_assignable(self, e1, e2) -> bool:
        """
        Returns whether e1 may be assigned to e2 in regards to ghost information.
        You may pass a boolean for either e1 or e2 instead when you already know whether they are ghost.

        If e1 is an AST node, we also update the is_ghost and contains_ghost flags if e1 is regular but
        assigned to a ghost element. The exception to this is if e1 is an impure function call.
        """
        is_e1_ghost = self.is_ghost(e1)
        is_e2_ghost = self.is_ghost(e2)

        is_e1_impure_call = isinstance(e1, ast.Call) and not e1.is_pure
        if not is_e1_ghost and is_e2_ghost and isinstance(e1, ast.AST) and not is_e1_impure_call:
            e1.is_ghost = True
            e1.contains_ghost = True

        may_assign = is_e2_ghost or (not is_e1_ghost)
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
        if isinstance(elem, (PythonVarBase, PythonMethod, PythonClass, PythonField)) or (
            isinstance(elem, ast.AST) and hasattr(elem, 'is_ghost')):
            return elem.is_ghost
        elif isinstance(elem, ast.expr):
            return self._is_expr_ghost(elem)
        elif isinstance(elem, GenericType):
            return False #TODO: Maybe need to determine dynamically
        elif isinstance(elem, bool):
            return elem
        raise UnsupportedException(elem, f"Unsupported Ghost resolution of type {type(elem)}")

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
            if len(expr.generators) != 1:
                raise UnsupportedException(expr, 'Multiple generators in list comprehension.')
            if expr.generators[0].ifs:
                raise UnsupportedException(expr, 'Filter in list comprehension.')
            
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
        elif isinstance(expr, ast.Await):
            items = [expr.value]
            res = self.is_ghost(expr.value)
        elif isinstance(expr, ast.Compare):
            items = [expr.left] + expr.comparators
            res = any([self.is_ghost(e) for e in items])
        elif isinstance(expr, ast.Call):
            is_func_ghost, ret_type = self.check_call(expr)
            if is_func_ghost:
                return True
            elif ret_type is None:
                return False
            else:
                return self.is_ghost(ret_type)
        elif isinstance(expr, ast.Constant):
            items = []
            res = False
        elif isinstance(expr, ast.Attribute):
            attr = self.get_target(expr, self.ctx)
            if attr is None:
                raise InvalidProgramException(expr, 'invalid.ghost.attribute', f"Couldn't correctly resolve attribute {expr.attr}")
            res = self.is_ghost(attr)
            items = []
        elif isinstance(expr, ast.Subscript):
            name = self.get_subscript_name(expr)
            if name in ["Union", "Tuple"]:
                items = expr.slice.elts
                res = any([self.is_ghost(e) for e in items])
            elif name in ["Optional", "List"]:
                items = [expr.slice]
                res = self.is_ghost(expr.slice)
            else:
                assert isinstance(expr.value, ast.Name), f"Unexpected type of {type(expr.value)}"
                items = [expr.value]
                res = self.is_ghost(expr.value)
        elif isinstance(expr, ast.Starred):
            if isinstance(expr.value, ast.Call):
                raise InvalidProgramException(expr, 'invalid.ghost.starred', "Do not use a star to unpack calls. Use an assignment instead.")
            items = [expr.value]
            res = self.is_ghost(expr.value)
        elif isinstance(expr, ast.Name):
            items = []
            if expr.id in self.modules[1].ghost_names or expr.id in GHOST_BUILTINS:
                res = True
            elif expr.id in self.modules[1].type_vars:
                res = False
            else:
                obj = self.get_target(expr, self.ctx)
                if obj is None:
                    raise InvalidProgramException(expr, 'invalid.ghost.name', f"Couldn't correctly resolve name {expr.id}")
                res = self.is_ghost(obj)
        elif isinstance(expr, (ast.List, ast.Tuple)):
            items = expr.elts
            res = any([self.is_ghost(e) for e in items])
        else:
            raise UnsupportedException(expr, f"Unsupported Expression of type {type(expr)}")
        
        expr.is_ghost = res
        self.set_contains_ghost(expr, res, *items)
        return res

    def set_contains_ghost(self, node: ast.AST, is_node_ghost: bool, *sub_exprs: ast.AST) -> None:
        node.contains_ghost = is_node_ghost or any(
            [sub_expr.contains_ghost for sub_expr in sub_exprs if isinstance(sub_expr, ast.AST)]
            )

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