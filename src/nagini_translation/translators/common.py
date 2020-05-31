"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import ast

from abc import ABCMeta
from nagini_translation.lib.constants import (
    ARBITRARY_BOOL_FUNC,
    ASSERTING_FUNC,
    COMBINE_NAME_FUNC,
    DICT_TYPE,
    INT_TYPE,
    IS_DEFINED_FUNC,
    LIST_TYPE,
    MAIN_METHOD_NAME,
    MAY_SET_PRED,
    NAME_DOMAIN,
    PRIMITIVE_BOOL_TYPE,
    PRIMITIVE_INT_TYPE,
    RANGE_TYPE,
    PSEQ_TYPE,
    PSET_TYPE,
    SET_TYPE,
    SINGLE_NAME,
    UNION_TYPE,
)
from nagini_translation.lib.context import Context
from nagini_translation.lib.errors import rules
from nagini_translation.lib.program_nodes import (
    chain_cond_exp,
    chain_if_stmts,
    OptionalType,
    PythonClass,
    PythonField,
    PythonIOOperation,
    PythonMethod,
    PythonModule,
    PythonNode,
    PythonType,
    PythonVar,
    toposort_classes,
    UnionType,
)
from nagini_translation.lib.resolver import get_target as do_get_target
from nagini_translation.lib.typedefs import (
    Expr,
    FuncApp,
    Info,
    Position,
    Stmt,
    StmtsAndExpr,
)
from nagini_translation.lib.util import (
    get_surrounding_try_blocks,
    InvalidProgramException,
    string_to_int,
    UnsupportedException
)
from nagini_translation.translators.abstract import AbstractTranslator
from typing import List, Tuple, Union


class CommonTranslator(AbstractTranslator, metaclass=ABCMeta):
    """
    Abstract class which all specialized translators extend. Provides some
    functionality which is needed by many or all specialized translators.
    """

    def translate_generic(self, node: ast.AST, ctx: Context) -> None:
        """
        Visitor that is used if no other visitor is implemented.
        Simply raises an exception.
        """
        raise UnsupportedException(node)

    def translate_block(self, stmtlist: List['silver.ast.Stmt'],
                        position: 'silver.ast.Position',
                        info: 'silver.ast.Info') -> Stmt:
        """
        Wraps a (Python) list of (Viper) statements into a Viper block
        """
        body = []
        for stmt in stmtlist:
            body.append(stmt)
        return self.viper.Seqn(body, position, info)

    def convert_to_type(self, e: Expr, target_type, ctx: Context,
                        node: ast.AST = None) -> Expr:
        """
        Converts expression ``e`` to the Viper type ``target_type`` if said
        type is Ref, Bool or Int.
        """
        result = e
        if target_type == self.viper.Ref:
            result = self.to_ref(e, ctx)
        elif target_type == self.viper.Bool:
            result = self.to_bool(e, ctx, node)
        elif target_type == self.viper.Int:
            result = self.to_int(e, ctx)
        return result

    def _is_pure(self, e: Expr) -> bool:
        e = self.unwrap(e)
        if isinstance(e, (self.viper.ast.And, self.viper.ast.Or)):
            return self._is_pure(e.left()) and self._is_pure(e.right())
        return e.isPure()

    def to_type(self, e: Expr, t, ctx) -> Expr:
        if t is self.viper.Ref:
            return self.to_ref(e, ctx)
        if t is self.viper.Int:
            return self.to_int(e, ctx)
        if t is self.viper.Bool:
            return self.to_bool(e, ctx)
        return e

    def to_ref(self, e: Expr, ctx: Context) -> Expr:
        """
        Converts the given expression to an expression of the Silver type Ref
        if it isn't already, either by boxing a primitive or undoing a
        previous unboxing operation.
        """
        # Avoid wrapping non-pure expressions (leads to errors within Silver's
        # Consistency object)
        if not self._is_pure(e):
            return e
        result = e
        if e.typ() == self.viper.Int:
            if (isinstance(e, self.viper.ast.FuncApp) and
                    e.funcname() == 'int___unbox__'):
                result = e.args().head()
            else:
                prim_int = ctx.module.global_module.classes[PRIMITIVE_INT_TYPE]
                result = self.get_function_call(prim_int, '__box__',
                                                [result], [None], None, ctx,
                                                position=e.pos())
        elif e.typ() == self.viper.Bool:
            if (isinstance(e, self.viper.ast.FuncApp) and
                    e.funcname() == 'bool___unbox__'):
                result = e.args().head()
            else:
                prim_bool = ctx.module.global_module.classes[PRIMITIVE_BOOL_TYPE]
                result = self.get_function_call(prim_bool, '__box__',
                                                [result], [None], None, ctx,
                                                position=e.pos())
        return result

    def to_bool(self, e: Expr, ctx: Context, node: ast.AST = None) -> Expr:
        """
        Converts the given expression to an expression of the Silver type Bool
        if it isn't already, either by calling __bool__ on an object and
        possibly unboxing the result, or by undoing a previous boxing operation.
        """
        # Avoid wrapping non-pure expressions (leads to errors within Silver's
        # Consistency object)
        if not self._is_pure(e):
            return e
        if e.typ() == self.viper.Bool:
            return e
        if e.typ() != self.viper.Ref:
            e = self.to_ref(e, ctx)
        if (isinstance(e, self.viper.ast.FuncApp) and
                e.funcname() == '__prim__bool___box__'):
            return e.args().head()
        result = e
        call_bool = True
        if node:
            node_type = self.get_type(node, ctx)
            if node_type.name == 'bool':
                call_bool = False
            if call_bool:
                result = self.get_function_call(node_type, '__bool__',
                                                [result], [None], node, ctx,
                                                position=e.pos())
        if result.typ() != self.viper.Bool:
            bool_type = ctx.module.global_module.classes['bool']
            result = self.get_function_call(bool_type, '__unbox__',
                                            [result], [None], node, ctx,
                                            position=e.pos())
        return result

    def to_int(self, e: Expr, ctx: Context) -> Expr:
        """
        Converts the given expression to an expression of the Silver type Int
        if it isn't already, either by unboxing a reference or undoing a
        previous boxing operation.
        """
        # Avoid wrapping non-pure expressions (leads to errors within Silver's
        # Consistency object)
        if not self._is_pure(e):
            return e
        if e.typ() == self.viper.Int:
            return e
        if e.typ() != self.viper.Ref:
            e = self.to_ref(e, ctx)
        if (isinstance(e, self.viper.ast.FuncApp) and
                    e.funcname() == '__prim__int___box__'):
            return e.args().head()
        result = e
        int_type = ctx.module.global_module.classes[INT_TYPE]
        result = self.get_function_call(int_type, '__unbox__',
                                        [result], [None], None, ctx,
                                        position=e.pos())
        return result

    def unwrap(self, e: Expr) -> Expr:
        if isinstance(e, self.viper.ast.FuncApp):
            if (e.funcname().endswith('__box__') or
                    e.funcname().endswith('__unbox__')):
                return e.args().head()
        return e

    def to_position(
            self, node: ast.AST, ctx: Context, error_string: str=None,
            rules: rules.Rules=None) -> 'silver.ast.Position':
        """
        Extracts the position from a node, assigns an ID to the node and stores
        the node and the position in the context for it.
        """
        return self.viper.to_position(node, ctx.position, error_string, rules,
                                      ctx.module.file, py_node=ctx.current_function)

    def no_position(self, ctx: Context, error_string: str=None,
            rules: rules.Rules=None) -> 'silver.ast.Position':
        return self.to_position(None, ctx, error_string, rules)

    def to_info(self, comments: List[str], ctx: Context) -> 'silver.ast.Info':
        """
        Wraps the given comments into an Info object.
        If ctx.info is set to override the given info, returns that.
        """
        if ctx.info is not None:
            return ctx.info
        if comments:
            return self.viper.SimpleInfo(comments)
        else:
            return self.viper.NoInfo

    def no_info(self, ctx: Context) -> 'silver.ast.Info':
        return self.to_info([], ctx)

    def normalize_type(self, typ: PythonType, ctx: Context) -> PythonType:
        """
        Normalizes a type, i.e., returns the actual NoneType if it's None,
        otherwise just returns the type.
        """
        if typ is None:
            return ctx.module.global_module.classes['NoneType']
        return typ

    def is_local_variable(self, var: PythonVar, ctx: Context) -> bool:
        """
        Assuming we are currently inside an impure method, checks if the given variable is
        a local variable in the Python program (i.e. not a parameter, not a variable that
        is quantified over).
        """
        if not ctx.actual_function:
            return False
        if var.name in ctx.actual_function.args:
            return False
        return var in ctx.actual_function.locals.values()

    def get_may_set_predicate(self, rec: Expr, field: PythonField, ctx: Context,
                              pos: Position = None) -> Expr:
        """
        Creates predicate instances representing the permissions to create the given
        field on the given receiver object.
        """
        if not pos:
            pos = self.no_position(ctx)
        info = self.no_info(ctx)
        full_perm = self.viper.FullPerm(pos, info)
        id = self.viper.IntLit(self._get_string_value(field.sil_name), pos, info)
        pred = self.viper.PredicateAccess([rec, id], MAY_SET_PRED, pos, info)
        pred_acc = self.viper.PredicateAccessPredicate(pred, full_perm, pos, info)
        return pred_acc

    def check_var_defined(self, target: PythonVar, position: Position,
                        info: Info) -> Expr:
        id = self.viper.IntLit(self._get_string_value(target.sil_name), position, info)
        id_param_decl = self.viper.LocalVarDecl('id', self.viper.Int, position, info)
        is_defined = self.viper.FuncApp(IS_DEFINED_FUNC, [id], position, info,
                                        self.viper.Bool, [id_param_decl])
        return is_defined

    def set_var_defined(self, target: PythonVar, position: Position,
                        info: Info) -> Stmt:
        """
        Returns an inhale which assumes that the given local variable is now defined.
        """
        is_defined = self.check_var_defined(target, position, info)
        return self.viper.Inhale(is_defined, position, info)

    def set_global_defined(self, declaration: PythonNode, module: PythonModule,
                           node: ast.AST, ctx: Context) -> Stmt:
        """
        Returns a statement that sets the name of the given declaration to be defined
        in the given module.
        """
        pos = self.to_position(node, ctx)
        info = self.no_info(ctx)
        module_set = module.names_var[1]
        decl_id = self.viper.IntLit(self._get_string_value(declaration.name), pos,
                                    info)
        return self._set_global_defined(decl_id, module_set, pos, info)

    def _set_global_defined(self, decl_int: Expr, module_var: Expr, pos: Position,
                            info: Info) -> Stmt:
        """
        Returns a statement that sets the name of represented by the integer decl_int to
        be defined in the given set of names.
        """
        if decl_int.typ() == self.viper.Int:
            decl_int = self.viper.DomainFuncApp(SINGLE_NAME, [decl_int], self.name_type(),
                                                pos, info, NAME_DOMAIN)
        new_set = self.viper.ExplicitSet([decl_int], pos, info)
        union = self.viper.AnySetUnion(module_var, new_set, pos, info)
        return self.viper.LocalVarAssign(module_var, union, pos, info)

    def name_type(self) -> 'silver.ast.DomainType':
        """
        The Silver type of global names, for which one can check if they are defined or
        not.
        """
        return self.viper.DomainType(NAME_DOMAIN, {}, [])

    def _is_defined(self, name: Expr, module: Expr, pos: Position, info: Info) -> Expr:
        """
        Returns an expression that is true iff the name represented by the given
        expression is defined in the module represented by the other expression.
        """
        name_type = self.viper.DomainType(NAME_DOMAIN, {}, [])
        if name.typ() == self.viper.Int:
            boxed_name = self.viper.DomainFuncApp(SINGLE_NAME, [name], name_type, pos,
                                                  info, NAME_DOMAIN)
        else:
            boxed_name = name
        return self.viper.AnySetContains(boxed_name, module, pos, info)

    def _combine_names(self, prefix: Expr, name: Expr, pos: Position, info: Info) -> Expr:
        """
        Returns an expression that combines the prefix-name and the name to a new name
        that represents 'prefix.name'.
        """
        name_type = self.viper.DomainType(NAME_DOMAIN, {}, [])
        if name.typ() == self.viper.Int:
            boxed_name = self.viper.DomainFuncApp(SINGLE_NAME, [name], name_type, pos,
                                                  info, NAME_DOMAIN)
        else:
            boxed_name = name
        if prefix.typ() == self.viper.Int:
            boxed_prefix = self.viper.DomainFuncApp(SINGLE_NAME, [prefix], name_type, pos,
                                                    info, NAME_DOMAIN)
        else:
            boxed_prefix = prefix
        return self.viper.DomainFuncApp(COMBINE_NAME_FUNC, [boxed_prefix, boxed_name],
                                        name_type, pos, info, NAME_DOMAIN)

    def extract_identifiers(self, ref: ast.AST, pos: Position,
                            info: Info) -> List[Expr]:
        """
        Returns a list containing all names contained by the given reference.
        """
        res = []
        if isinstance(ref, ast.Subscript):
            if isinstance(ref.value, ast.Name) and ref.value.id in ('Optional', 'Union'):
                if not isinstance(ref.slice.value, ast.Tuple):
                    return self.extract_identifiers(ref.slice.value, pos, info)
                for e in ref.slice.value.elts:
                    res.extend(self.extract_identifiers(e, pos, info))
                return res

        decl_id = None
        for name in reversed(self._get_name_parts(ref)):
            current = self.viper.IntLit(self._get_string_value(name), pos,
                                        info)
            if decl_id is None:
                decl_id = current
            else:
                decl_id = self._combine_names(current, decl_id, pos, info)
        if decl_id:
            return [decl_id]
        return []

    def _get_global_definedness_conditions(self, declaration: PythonNode,
                                           module: PythonModule, ref_node: ast.AST,
                                           ctx: Context) -> Tuple[Expr, Expr]:
        """
        Returns two boolean expressions that represent 1) if the name of the given
        declaration is defined in the given module, and 2) if all dependencies of the
        given declaration are currently defined.
        """
        msg = 'Name "' + declaration.name + '" is defined'
        pos = self.to_position(ref_node, ctx, error_string=msg)
        info = self.no_info(ctx)
        module_set = module.names_var[1]
        decl_ids = self.extract_identifiers(ref_node, pos, info)
        contains = self.viper.TrueLit(pos, info)
        for decl_id in decl_ids:
            contains = self.viper.And(contains, self._is_defined(decl_id, module_set, pos,
                                                                 info), pos, info)
        deps = set()
        if isinstance(declaration, (PythonMethod, PythonClass)):
            called = declaration
            if isinstance(called, PythonClass):
                called = called.get_method('__init__')
            if called:
                called.add_all_call_deps(deps)
        msg = 'all dependencies of "' + declaration.name + '" are defined'
        pos = self.to_position(ref_node, ctx, error_string=msg)
        deps_defined = self.viper.TrueLit(pos, info)
        for ref, decl, mod, *conds in deps:
            module_set = mod.names_var[1]
            decl_ids = self.extract_identifiers(ref, pos, info)
            for decl_id in decl_ids:
                contains_dep = self._is_defined(decl_id, module_set, pos, info)
                for cond in conds:
                    # Iterate over conditions (PythonNodes); the dependency must be
                    # defined if all such PythonNodes are currently defined in their
                    # respective modules.
                    module_set = cond.module.names_var[1]
                    decl_id = self.viper.IntLit(self._get_string_value(cond.name), pos,
                                                info)
                    cond_contains = self._is_defined(decl_id, module_set, pos, info)
                    contains_dep = self.viper.Implies(cond_contains, contains_dep, pos,
                                                      info)
                deps_defined = self.viper.And(deps_defined, contains_dep, pos, info)

        return contains, deps_defined

    def _get_name_parts(self, node: ast.AST) -> List[str]:
        """
        Converts an AST node representing some kind of reference to a list of strings.
        """
        while isinstance(node, ast.Subscript):
            node = node.value
        if isinstance(node, ast.Name):
            return [node.id]
        if isinstance(node, ast.Attribute):
            pref = self._get_name_parts(node.value)
            return pref + [node.attr]
        if isinstance(node, ast.Str):
            return []
        return [node.name]

    def assert_global_defined(self, declaration: PythonNode, module: PythonModule,
                              ref_node: ast.AST, ctx: Context,
                              call_deps=True) -> List[Stmt]:
        """
        Creates assertions that check that the given declaration and all its dependencies
        are currently defined in the given module.
        """
        info = self.no_info(ctx)
        name, deps = self._get_global_definedness_conditions(declaration, module,
                                                             ref_node, ctx)
        msg = 'Name "' + declaration.name + '" is defined'
        pos = self.to_position(ref_node, ctx, error_string=msg)
        assert_name = self.viper.Assert(name, pos, info)
        if not call_deps:
            return [assert_name]
        msg = 'all dependencies of "' + declaration.name + '" are defined'
        pos = self.to_position(ref_node, ctx, error_string=msg)
        assert_deps = self.viper.Assert(deps, pos, info)
        return [assert_name, assert_deps]

    def wrap_global_defined_check(self, val: Expr, declaration: PythonNode,
                                  module: PythonModule, ref_node: ast.AST,
                                  ctx: Context) -> Expr:
        """
        Wraps the given expression into a new expression that checks that the given
        declaration and all its dependencies are currently defined in the given module.
        """
        info = self.no_info(ctx)
        msg = 'Name "' + declaration.name + '" is defined'
        pos = self.to_position(ref_node, ctx, error_string=msg,
                               rules=rules.GLOBAL_NAME_NOT_DEFINED)
        msg = 'all dependencies of "' + declaration.name + '" are defined'
        deps_pos = self.to_position(ref_node, ctx, error_string=msg,
                                    rules=rules.DEPENDENCIES_NOT_DEFINED)
        name, deps = self._get_global_definedness_conditions(declaration, module,
                                                             ref_node, ctx)
        assertion_param_decl = self.viper.LocalVarDecl('ass',
                                                       self.viper.Bool, pos,
                                                       info)
        var_param_decl = self.viper.LocalVarDecl('val', self.viper.Ref, pos, info)
        deps_func = self.viper.FuncApp(ASSERTING_FUNC, [val, deps], deps_pos, info,
                                       self.viper.Ref, [var_param_decl,
                                                        assertion_param_decl])
        name_func = self.viper.FuncApp(ASSERTING_FUNC, [deps_func, name], pos, info,
                                       self.viper.Ref, [var_param_decl,
                                                        assertion_param_decl])
        return name_func

    def is_main_method(self, ctx: Context) -> bool:
        """
        Checks if we are currently translating the 'main method', i.e., the global
        statements of the program.
        """
        if not ctx.current_function:
            return False
        return ctx.current_function.name == MAIN_METHOD_NAME

    def get_tuple_type_arg(self, arg: Expr, arg_type: PythonType, node: ast.AST,
                           ctx: Context) -> Expr:
        """
        Creates an expression of type PyType that represents the type of 'arg',
        to be handed to the constructor function for tuples. This is different
        than what's used elsewhere. For, e.g., Optional[NoneType, A, C], this
        will return
        arg == null ? NoneType : issubtype(typeof(arg), A) ? A : C
        """
        position = self.no_position(ctx)
        info = self.no_info(ctx)
        if arg_type.name == UNION_TYPE:
            first_arg = self.normalize_type(arg_type.type_args[0], ctx)
            result = self.type_factory.translate_type_literal(first_arg,
                                                              position, ctx)
            for option in arg_type.type_args[1:]:
                option = self.normalize_type(option, ctx)
                check = self.type_check(arg, option, position, ctx, False)
                type_lit = self.type_factory.translate_type_literal(option,
                                                                    position,
                                                                    ctx)
                result = self.viper.CondExp(check, type_lit, result, position,
                                            info)
            return result
        arg_type = self.normalize_type(arg_type, ctx)
        type_lit = self.type_factory.translate_type_literal(arg_type,
                                                            position, ctx)
        return type_lit

    def get_func_or_method_call(self, receiver: PythonType, func_name: str,
                                args: List[Expr], arg_types: List[Expr],
                                node: ast.AST, ctx: Context) -> StmtsAndExpr:
        if receiver.has_function(func_name):
            call = self.get_function_call(receiver, func_name, args, arg_types, node, ctx)
            return [], call
        method = receiver.get_method(func_name)
        if method:
            assert method.type
            target_var = ctx.actual_function.create_variable('target', method.type,
                                                             self.translator)
            val = target_var.ref(node, ctx)
            call = self.get_method_call(receiver, func_name, args, arg_types, [val], node,
                                        ctx)
            return call, val
        return [], None

    def get_quantifier_lhs(self, in_expr: Expr, dom_type: PythonType, dom_arg: Expr,
                           node: ast.AST, ctx: Context, position: Position,
                           force_trigger=False) -> Expr:
        """
        Returns a contains-expression representing whether in_expr is in dom_arg.
        To be used on the left hand side of quantifiers (and in the corresponding
        triggers):
        Forall(iter, lambda x: e)
        becomes
        forall x: <quantifier_lhs> ==> e
        Defaults to in_expr in type___sil_seq__, but used simpler expressions for known
        types to improve performance/triggering.
        """
        position = position if position else self.to_position(node, ctx)
        info = self.no_info(ctx)
        res = None
        if not (isinstance(dom_type, UnionType) or isinstance(dom_type, OptionalType)):
            if dom_type.name in (DICT_TYPE, SET_TYPE, PSEQ_TYPE, PSET_TYPE):
                contains_constructor = self.viper.AnySetContains
                if dom_type.name == DICT_TYPE:
                    set_ref = self.viper.SetType(self.viper.Ref)
                    field = self.viper.Field('dict_acc', set_ref, position, info)
                    res = self.viper.FieldAccess(dom_arg, field, position, info)
                elif dom_type.name == SET_TYPE:
                    set_ref = self.viper.SetType(self.viper.Ref)
                    field = self.viper.Field('set_acc', set_ref, position, info)
                    res = self.viper.FieldAccess(dom_arg, field, position, info)
                elif dom_type.name == PSET_TYPE:
                    res = self.get_function_call(dom_type, '__unbox__', [dom_arg],
                                                 [None], node, ctx, position)
                else:
                    # PSEQ_TYPE
                    contains_constructor = self.viper.SeqContains
                    res = self.get_function_call(dom_type, '__sil_seq__', [dom_arg],
                                                 [None], node, ctx, position)
            if False and (dom_type.name == RANGE_TYPE and isinstance(node.func, ast.Name) and
                        node.func.id == 'range'):
                left = node.args[0]
                right = node.args[1]
                _, left_expr = self.translate_expr(left, ctx)
                _, right_expr = self.translate_expr(right, ctx)
                int_class = ctx.module.global_module.classes[INT_TYPE]
                left_bound = self.get_function_call(int_class, '__ge__',
                                                    [in_expr, left], [None, None],
                                                    node, ctx, position)
                right_bound = self.get_function_call(int_class, '__lt__',
                                                    [in_expr, right], [None, None],
                                                    node, ctx, position)
                if force_trigger:
                    return None
                else:
                    return self.viper.And(left_bound, right_bound, position, info)
        if res is None:
            contains_constructor = self.viper.SeqContains
            res = self.get_sequence(dom_type, dom_arg, None, node, ctx, position)
        return contains_constructor(in_expr, res, position, info)

    def get_sequence(self, receiver: PythonType, arg: Expr, arg_type: PythonType,
                     node: ast.AST, ctx: Context,
                     position: Position = None) -> Expr:
        """
        Returns a sequence (Viper type Seq[Ref]) representing the contents of arg.
        Defaults to type___sil_seq__, but used simpler expressions for known types
        to improve performance/triggering.
        """
        position = position if position else self.to_position(node, ctx)
        info = self.no_info(ctx)
        if not isinstance(receiver, UnionType) or isinstance(receiver, OptionalType):
            if receiver.name == LIST_TYPE:
                seq_ref = self.viper.SeqType(self.viper.Ref)
                field = self.viper.Field('list_acc', seq_ref, position, info)
                res = self.viper.FieldAccess(arg, field, position, info)
                return res
            if receiver.name == PSEQ_TYPE:
                if (isinstance(arg, self.viper.ast.FuncApp) and
                            arg.funcname() == 'PSeq___create__'):
                    args = self.viper.to_list(arg.args())
                    return args[0]
        return self.get_function_call(receiver, '__sil_seq__', [arg], [arg_type],
                                      node, ctx, position)

    def _get_function_call(self, receiver: PythonType,
                          func_name: str, args: List[Expr],
                          arg_types: List[PythonType], node: ast.AST,
                          ctx: Context,
                          position: Position = None) -> FuncApp:
        """
        Creates a function application of the function called func_name, with
        the given receiver and arguments. Boxes arguments if necessary, and
        unboxed the result if needed as well. This method only handles receivers
        of non-union types.
        """
        if receiver:
            target_cls = receiver
            func = target_cls.get_function(func_name)
        else:
            for container in ctx.module.get_included_modules():
                if func_name in container.functions:
                    func = container.functions[func_name]
                    break
        if not func:
            if receiver and target_cls.get_method(func_name):
                msg = 'Called method is expected to be pure: ' + func_name
                raise UnsupportedException(node, msg)
            raise InvalidProgramException(node, 'unknown.function.called')
        formal_args = []
        actual_args = []
        assert len(args) == len(func.get_args())
        for arg, param, type in zip(args, func.get_args(), arg_types):
            formal_args.append(param.decl)
            if param.type.name == '__prim__bool':
                actual_arg = self.to_bool(arg, ctx)
            elif param.type.name == '__prim__int':
                actual_arg = self.to_int(arg, ctx)
            else:
                actual_arg = self.to_ref(arg, ctx)
            actual_args.append(actual_arg)
        type = self.translate_type(func.type, ctx)
        sil_name = func.sil_name

        actual_position = position if position else self.to_position(node, ctx)
        call = self.viper.FuncApp(sil_name, actual_args,
                                  actual_position,
                                  self.no_info(ctx), type, formal_args)
        return call

    def get_function_call(self, receiver: PythonType,
                          func_name: str, args: List[Expr],
                          arg_types: List[PythonType], node: ast.AST,
                          ctx: Context,
                          position: Position = None) -> FuncApp:
        """
        Creates a function application of the function called func_name, with
        the given receiver and arguments. Boxes arguments if necessary, and
        unboxed the result if needed as well. When the receiver is of union
        type, a function call application is created for each type in the
        union with its respective guard.
        """
        if receiver and type(receiver) is UnionType:
            position = self.to_position(node, ctx) if position is None else position
            guarded_functions = []
            for cls in toposort_classes(receiver.get_types() - {None}):

                # Create guard checking if receiver is an instance of this class
                guard = self.type_check(args[0], cls, position, ctx)

                # Translate the function call on this particular receiver's class
                function = self._get_function_call(cls, func_name, args,
                                                   arg_types, node, ctx,
                                                   position)

                # Stores guard and translated function call as tuple in a list
                guarded_functions.append((guard, function))

            # Chain list of guard and function call tuples in an if-then-else
            # expression
            return chain_cond_exp(guarded_functions, self.viper, position,
                                  self.no_info(ctx), ctx)
        else:
            # Pass-through
            return self._get_function_call(receiver, func_name, args,
                                           arg_types, node, ctx, position)

    def _get_method_call(self, receiver: PythonType,
                        func_name: str, args: List[Expr],
                        arg_types: List[PythonType],
                        targets: List['silver.ast.LocalVarRef'],
                        node: ast.AST,
                        ctx: Context) -> List[Stmt]:
        """
        Creates a method call to the method called func_name, with the given
        receiver and arguments. Boxes arguments if necessary. This method only
        handles receivers of non-union types.
        """
        if receiver:
            target_cls = receiver
            func = target_cls.get_method(func_name)
        else:
            func = ctx.module.methods[func_name]
        if not func:
            raise InvalidProgramException(node, 'unknown.method.called')
        actual_args = []
        for arg, param, _ in zip(args, func.get_args(), arg_types):
            if param.type.name == PRIMITIVE_BOOL_TYPE:
                actual_arg = self.to_bool(arg, ctx)
            elif param.type.name == '__prim__int':
                actual_arg = self.to_int(arg, ctx)
            else:
                actual_arg = self.to_ref(arg, ctx)
            actual_args.append(actual_arg)
        sil_name = func.sil_name
        call = self.create_method_call_node(
            ctx, sil_name, actual_args, targets, self.to_position(node, ctx),
            self.no_info(ctx), target_method=func, target_node=node)
        return call

    def get_method_call(self, receiver: PythonType,
                        func_name: str, args: List[Expr],
                        arg_types: List[PythonType],
                        targets: List['silver.ast.LocalVarRef'],
                        node: ast.AST,
                        ctx: Context) -> List[Stmt]:
        """
        Creates a method call to the method called func_name, with the given
        receiver and arguments. Boxes arguments if necessary. When the receiver
        is of union type, a method call is created for each type in the union
        with its respective guard.
        """
        position = self.to_position(node, ctx)
        info = self.no_info(ctx)
        if receiver and type(receiver) is UnionType:
            guarded_methods = []
            for cls in toposort_classes(receiver.get_types() - {None}):

                # Create guard checking if receiver is an instance of this class
                guard = self.type_check(args[0], cls, position, ctx)

                # Translate the method call on this particular receiver's class
                method = self._get_method_call(cls, func_name, list(args), arg_types,
                                               list(targets), node, ctx)

                # Translated method call into a block
                block = self.translate_block(method, position, info)

                # Stores guard and translated method call as tuple in a list
                guarded_methods.append((guard, block))

            # Chain list of guard and function call tuples in an if-then-else
            # statement
            return [chain_if_stmts(guarded_methods, self.viper, position, info, ctx)]
        else:
            # Pass-through
            return self._get_method_call(receiver, func_name, args, arg_types,
                                         targets, node, ctx)

    def get_error_var(self, stmt: ast.AST,
                      ctx: Context) -> 'silver.ast.LocalVarRef':
        """
        Returns the error variable of the try-block protecting stmt, otherwise
        the error return variable of the surrounding function, otherwise
        creates a new local variable of type Exception.
        """
        tries = get_surrounding_try_blocks(ctx.actual_function.try_blocks,
                                           stmt)
        if tries:
            err_var = tries[0].get_error_var(self.translator)
            if err_var.sil_name in ctx.var_aliases:
                err_var = ctx.var_aliases[err_var.sil_name]
            return err_var.ref()
        if ctx.actual_function.declared_exceptions:
            return ctx.error_var.ref()
        else:
            new_var = ctx.current_function.create_variable('error',
                ctx.module.global_module.classes['Exception'], self.translator)
            return new_var.ref()

    def var_type_check(self, name: str, type: PythonType,
                       position: 'silver.ast.Position',
                       ctx: Context, inhale_exhale: bool=True) -> Expr:
        """
        Creates an expression checking if the var with the given name
        is of the given type.
        """
        if name in ctx.var_aliases:
            obj_var = ctx.var_aliases[name].ref()
        else:
            obj_var = self.viper.LocalVar(name, self.viper.Ref,
                                          self.no_position(ctx),
                                          self.no_info(ctx))
        return self.type_check(obj_var, type, position, ctx,
                               inhale_exhale=inhale_exhale)

    def create_predicate_access(self, pred_name: str, args: List, perm: Expr,
                                node: ast.AST, ctx: Context) -> Expr:
        """
        Creates a predicate access for the predicate with the given name,
        with the given args and permission.
        """
        pred_acc = self.viper.PredicateAccess(args, pred_name,
                                              self.to_position(node, ctx),
                                              self.no_info(ctx))
        if ctx.perm_factor:
            pos = self.to_position(node, ctx)
            info = self.no_info(ctx)
            perm = self.viper.PermMul(perm, ctx.perm_factor, pos, info)
        pred_acc_pred = self.viper.PredicateAccessPredicate(pred_acc, perm,
            self.to_position(node, ctx), self.no_info(ctx))
        return pred_acc_pred

    def add_handlers_for_inlines(self, ctx: Context) -> List[Stmt]:
        stmts = []
        old_var_valiases = ctx.var_aliases
        old_lbl_aliases = ctx.label_aliases
        for (added_method, var_aliases, lbl_aliases) in ctx.added_handlers:
            ctx.var_aliases = var_aliases
            ctx.label_aliases = lbl_aliases
            ctx.inlined_calls.append(added_method)
            for block in added_method.try_blocks:
                for handler in block.handlers:
                    stmts += self.translate_handler(handler, ctx)
                if block.else_block:
                    stmts += self.translate_handler(block.else_block, ctx)
                if block.finally_block:
                    stmts += self.translate_finally(block, ctx)
            ctx.inlined_calls.remove(added_method)
        ctx.added_handlers = []
        ctx.var_aliases = old_var_valiases
        ctx.label_aliases = old_lbl_aliases
        return stmts

    def _get_string_value(self, string: str) -> int:
        """
        Computes an integer value that uniquely represents the given string.
        """
        return string_to_int(string)

    def is_valid_super_call(self, node: ast.Call, container) -> bool:
        """
        Checks if a super() call is valid:
        It must either have no arguments, or otherwise the
        first arg must be a class, the second a reference to self.
        """
        if not node.args:
            return True
        elif len(node.args) == 2:
            target = do_get_target(node.args[0],
                                   container.module.get_included_modules(),
                                   container)
            return (isinstance(target, PythonClass) and
                    isinstance(node.args[1], ast.Name) and
                    (node.args[1].id == next(iter(container.args))))
        else:
            return False

    def get_target(self, node: ast.AST, ctx: Context) -> PythonModule:
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

    def get_fresh_int_lit(self, ctx: Context) -> Expr:
        """
        Returns an integer literal with a fresh value.
        """
        return self.viper.IntLit(ctx.get_fresh_int(), self.no_position(ctx),
                                 self.no_info(ctx))

    def get_unknown_bool(self, ctx: Context) -> Expr:
        """
        Returns an arbitrary but fixed boolean value.
        """
        pos = self.no_position(ctx)
        info = self.no_info(ctx)
        fresh_int = self.get_fresh_int_lit(ctx)
        param = self.viper.LocalVarDecl('i', self.viper.Int, pos, info)
        return self.viper.FuncApp(ARBITRARY_BOOL_FUNC, [fresh_int], pos, info,
                                  self.viper.Bool, [param])
