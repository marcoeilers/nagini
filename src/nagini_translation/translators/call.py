"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import ast
import copy
from collections import OrderedDict
from typing import Dict, List, Tuple, Union

from nagini_contracts.contracts import (
    CONTRACT_FUNCS,
    CONTRACT_WRAPPER_FUNCS
)
from nagini_contracts.io_contracts import IO_CONTRACT_FUNCS
from nagini_contracts.obligations import OBLIGATION_CONTRACT_FUNCS
from nagini_translation.lib.config import obligation_config
from nagini_translation.lib import silver_nodes as sil
from nagini_translation.lib.constants import (
    BUILTIN_PREDICATES,
    BUILTINS,
    DICT_TYPE,
    END_LABEL,
    ERROR_NAME,
    GET_ARG_FUNC,
    GET_METHOD_FUNC,
    GET_OLD_FUNC,
    INT_TYPE,
    JOINABLE_FUNC,
    LIST_TYPE,
    METHOD_ID_DOMAIN,
    OBJECT_TYPE,
    PRIMITIVE_INT_TYPE,
    PRIMITIVES,
    RANGE_TYPE,
    RESULT_NAME,
    SET_TYPE,
    STRING_TYPE,
    THREAD_DOMAIN,
    THREAD_POST_PRED,
    THREAD_START_PRED,
    TUPLE_TYPE,
)
from nagini_translation.lib.errors import rules
from nagini_translation.lib.program_nodes import (
    chain_cond_exp,
    GenericType,
    MethodType,
    OptionalType,
    PythonClass,
    PythonIOOperation,
    PythonMethod,
    PythonModule,
    PythonType,
    PythonVar,
    UnionType,
    toposort_classes,
    chain_if_stmts,
    SilverType,
)
from nagini_translation.lib.typedefs import (
    Expr,
    FuncApp,
    Position,
    Stmt,
    StmtsAndExpr,
)
from nagini_translation.lib.util import (
    get_body_indices,
    get_func_name,
    InvalidProgramException,
    OldExpressionCollector,
    OldExpressionTransformer,
    pprint,
    UnsupportedException,
)
from nagini_translation.translators.abstract import Context
from nagini_translation.translators.common import CommonTranslator


class CallTranslator(CommonTranslator):


    def _translate_isinstance(self, node: ast.Call,
                              ctx: Context) -> StmtsAndExpr:
        assert len(node.args) == 2
        target = self.get_target(node.args[1], ctx)
        assert isinstance(target, (PythonType, PythonVar))
        stmt, obj = self.translate_expr(node.args[0], ctx)
        pos = self.to_position(node, ctx)
        if isinstance(target, PythonType):
            check = self.type_check(obj, target, pos, ctx, inhale_exhale=False)
        else:
            check = self.type_factory.dynamic_type_check(obj, target.ref(), pos,
                                                         ctx)
        return stmt, check

    def _translate_type_func(self, node: ast.Call,
                             ctx: Context) -> StmtsAndExpr:
        assert len(node.args) == 1
        stmt, obj = self.translate_expr(node.args[0], ctx)
        pos = self.to_position(node, ctx)
        result = self.type_factory.typeof(obj, ctx)
        return stmt, result

    def _translate_cast_func(self, node: ast.Call,
                             ctx: Context) -> StmtsAndExpr:
        stmt, object_arg = self.translate_expr(node.args[1], ctx)
        cast_type = self.get_type(node, ctx)
        arg_pos = self.to_position(node.args[0], ctx)
        type_arg = self.type_factory.translate_type_literal(cast_type,
                                                            arg_pos, ctx)
        object_class = ctx.module.global_module.classes['object']
        result = self.get_function_call(object_class, '__cast__',
                                        [type_arg, object_arg], [None, None],
                                        node, ctx)
        return stmt, result

    def _translate_len(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        assert len(node.args) == 1
        stmt, target = self.translate_expr(node.args[0], ctx)
        arg_type = self.get_type(node.args[0], ctx).try_box()
        len_stmt, len_val = self.get_func_or_method_call(arg_type, '__len__', [target],
                                                         [None], node, ctx)
        return stmt + len_stmt, len_val

    def _translate_str(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        assert len(node.args) == 1
        stmt, target = self.translate_expr(node.args[0], ctx)
        arg_type = self.get_type(node.args[0], ctx)
        str_stmt, str_val = self.get_func_or_method_call(arg_type, '__str__', [target],
                                                         [None], node, ctx)
        return stmt + str_stmt, str_val


    def _translate_int(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        assert len(node.args) == 1
        stmt, target = self.translate_expr(node.args[0], ctx)
        arg_type = self.get_type(node.args[0], ctx)
        str_stmt, str_val = self.get_func_or_method_call(arg_type, '__int__', [target],
                                                         [None], node, ctx)
        return stmt + str_stmt, str_val

    def _translate_bool(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        assert len(node.args) == 1
        stmt, target = self.translate_expr(node.args[0], ctx)
        arg_type = self.get_type(node.args[0], ctx)
        bool_stmt, bool_val = self.get_func_or_method_call(arg_type, '__bool__', [target],
                                                           [None], node, ctx)
        return stmt + bool_stmt, bool_val

    def _translate_super(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        This will only be called if super() is called in some place that is not the
        receiver of a method call. Who knows what happens when you interact with that;
        we do not support it.
        """
        raise InvalidProgramException(node, 'invalid.super.call')

    def translate_adt_cons(self, cons: PythonClass, args: List[FuncApp],
                           pos: Position, ctx: Context) -> Expr:
        """
        Constructs ADTs via a sequence of constructor calls and
        boxing/unboxing calls.
        """
        info = self.no_info(ctx)
        adt_type = self.viper.DomainType(cons.adt_domain_name, {}, [])

        # If expected argument type is the ADT type (another constructor call),
        # unbox translated argument
        for index, (arg_type, translated_arg) in enumerate(zip(cons.fields.values(),
                                                               args)):
            if arg_type.type == cons.adt_def:
                unbox_func = self.viper.FuncApp(cons.fresh('unbox_' +
                                                cons.adt_domain_name),
                                                [translated_arg], pos,
                                                info, adt_type)
                args[index] = unbox_func
            else:
                if arg_type.type.name in PRIMITIVES:
                    v_type = self.translate_type(arg_type.type, ctx)
                    args[index] = self.to_type(translated_arg, v_type, ctx)

        # Translate constructor call
        cons_call = self.viper.DomainFuncApp(cons.fresh(cons.adt_prefix +
                                             cons.name), args, adt_type,
                                             pos, info, cons.adt_domain_name)

        # Box translated constructor
        box_func = self.viper.FuncApp(cons.fresh('box_' + cons.adt_domain_name),
                                      [cons_call], pos, info, self.viper.Ref)

        return box_func

    def _is_lock_subtype(self, cls: PythonClass) -> bool:
        if cls is None:
            return False
        if cls.name == 'Lock':
            return cls
        return self._is_lock_subtype(cls.superclass)

    def translate_constructor_call(self, target_class: PythonClass,
            node: ast.Call, args: List, arg_stmts: List,
            ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to the constructor of target_class with args, where
        node is the call node and arg_stmts are statements related to argument
        evaluation.
        """
        assert all(args), "Some args are None: {}".format(args)
        pos = self.to_position(node, ctx)

        if target_class.is_adt:
            return arg_stmts, self.translate_adt_cons(target_class, args, pos, ctx)

        res_var = ctx.current_function.create_variable(target_class.name +
                                                       '_res',
                                                       target_class,
                                                       self.translator)
        result_type = self.get_type(node, ctx)
        info = self.no_info(ctx)

        # Temporarily bind the type variables of the constructed class to
        # the concrete type arguments.
        old_bound_type_vars = ctx.bound_type_vars
        ctx.bound_type_vars = old_bound_type_vars.copy()
        current_type = result_type
        while current_type:
            if isinstance(current_type, GenericType):
                vars_args = zip(current_type.python_class.type_vars.items(),
                                current_type.type_args)
                for (name, var), arg in vars_args:
                    literal = self.type_factory.translate_type_literal(arg, pos,
                                                                       ctx)
                    key = (var.target_type.name, name)
                    ctx.bound_type_vars[key] = literal
            current_type = current_type.superclass

        fields = list(target_class.all_fields)
        may_set_inhales = [self.viper.Inhale(self.get_may_set_predicate(res_var.ref(),
                                                                        f, ctx),
                                             pos, self.no_info(ctx))
                           for f in fields]

        ctx.bound_type_vars = old_bound_type_vars
        new = self.viper.NewStmt(res_var.ref(), [], self.no_position(ctx),
                                 self.no_info(ctx))

        result_has_type = self.type_factory.type_check(res_var.ref(), result_type, pos,
                                                       ctx, concrete=True)
        defined_check = []
        if target_class.module is not target_class.module.global_module:
            # Mark the current function as depending on the called class. If we're in
            # a global context, assert that the called class and its dependencies are
            # defined.
            func_node = node.func if isinstance(node, ast.Call) else node
            self._add_dependencies(func_node, target_class, ctx)
            if self.is_main_method(ctx):
                defined_check = self.assert_global_defined(target_class, ctx.module,
                                                           node.func, ctx)

        # Inhale the type information about the newly created object
        # so that it's already present when calling __init__.
        type_inhale = self.viper.Inhale(result_has_type, pos,
                                        self.no_info(ctx))
        args = [res_var.ref()] + args
        stmts = [new, type_inhale] + may_set_inhales

        if self._is_lock_subtype(target_class):
            # For locks, fold the invariant predicate before actually calling the
            # constructor (which requires the predicate in its precondition).
            lock_pos = self.to_position(node, ctx, rules=rules.LOCK_RELEASE_INVARIANT)
            lock_class = self._is_lock_subtype(target_class)
            locked_obj = self.get_function_call(lock_class, 'get_locked', [res_var.ref()],
                                                [None], node, ctx, lock_pos)
            arg_is_locked = self.viper.EqCmp(locked_obj, args[1], lock_pos, info)
            stmts.append(self.viper.Inhale(arg_is_locked, lock_pos, info))
            invariant_pred = lock_class.get_predicate('invariant')
            full_perm = self.viper.FullPerm(lock_pos, info)
            pred_acc = self.viper.PredicateAccess([res_var.ref()],
                                                  invariant_pred.sil_name, lock_pos, info)
            acc_pred = self.viper.PredicateAccessPredicate(pred_acc, full_perm,
                                                           lock_pos, info)
            stmts.append(self.viper.Fold(acc_pred, lock_pos, info))

        target = target_class.get_method('__init__')
        if target:
            target_class = target.cls
            targets = []
            if target.declared_exceptions:
                error_var = self.get_error_var(node, ctx)
                targets.append(error_var)
            method_name = target_class.get_method('__init__').sil_name
            init = self.create_method_call_node(
                ctx, method_name, args, targets, self.to_position(node, ctx),
                self.no_info(ctx), target_method=target, target_node=node)
            stmts.extend(init)
            if target.declared_exceptions:
                catchers = self.create_exception_catchers(error_var,
                    ctx.actual_function.try_blocks, node, ctx)
                stmts = stmts + catchers
        return arg_stmts + defined_check + stmts, res_var.ref()

    def _translate_list(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        contents = None
        stmts = []
        if node.args:
            assert len(node.args) == 1
            arg_stmt, arg_val = self.translate_expr(node.args[0], ctx)
            stmts.extend(arg_stmt)
            contents = arg_val
        list_class = ctx.module.global_module.classes[LIST_TYPE]
        res_var = ctx.current_function.create_variable('list',
                                                       list_class, self.translator)
        targets = [res_var.ref()]
        constr_call = self.get_method_call(list_class, '__init__', [],
                                           [], targets, node, ctx)
        stmts.extend(constr_call)
        # Inhale the type of the newly created set (including type arguments)
        set_type = self.get_type(node, ctx)
        if (node._parent and isinstance(node._parent, ast.Assign) and
                    len(node._parent.targets) == 1):
            set_type = self.get_type(node._parent.targets[0], ctx)
        position = self.to_position(node, ctx)
        info = self.no_info(ctx)
        result_var = res_var.ref(node, ctx)
        stmts.append(self.viper.Inhale(self.type_check(result_var,
                                                       set_type, position, ctx),
                                       position, self.no_info(ctx)))
        if contents:
            sil_ref_seq = self.viper.SeqType(self.viper.Ref)
            ref_seq = SilverType(sil_ref_seq, ctx.module)
            havoc_var = ctx.actual_function.create_variable('havoc_seq', ref_seq,
                                                            self.translator)
            seq_field = self.viper.Field('list_acc', sil_ref_seq, position, info)
            content_field = self.viper.FieldAccess(result_var, seq_field, position, info)
            stmts.append(self.viper.FieldAssign(content_field, havoc_var.ref(), position,
                                                info))
            arg_type = self.get_type(node.args[0], ctx)
            arg_seq = self.get_sequence(arg_type, contents, None, node, ctx, position)
            res_seq = self.get_sequence(set_type, result_var, None, node, ctx, position)
            seq_equal = self.viper.EqCmp(arg_seq, res_seq, position, info)
            stmts.append(self.viper.Inhale(seq_equal, position, info))
        return stmts, result_var

    def _translate_set(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        contents = None
        stmts = []
        if node.args:
            assert len(node.args) == 1
            arg_stmt, arg_val = self.translate_expr(node.args[0], ctx)
            stmts.extend(arg_stmt)
            contents = arg_val
        set_class = ctx.module.global_module.classes[SET_TYPE]
        res_var = ctx.current_function.create_variable('set',
            set_class, self.translator)
        targets = [res_var.ref()]
        constr_call = self.get_method_call(set_class, '__init__', [],
                                           [], targets, node, ctx)
        stmts.extend(constr_call)
        # Inhale the type of the newly created set (including type arguments)
        set_type = self.get_type(node, ctx)
        if (node._parent and isinstance(node._parent, ast.Assign) and
                len(node._parent.targets) == 1):
            set_type = self.get_type(node._parent.targets[0], ctx)
        position = self.to_position(node, ctx)
        info = self.no_info(ctx)
        result_var = res_var.ref(node, ctx)
        stmts.append(self.viper.Inhale(self.type_check(result_var,
                                                       set_type, position, ctx),
                                       position, self.no_info(ctx)))
        if contents:
            sil_ref_set = self.viper.SetType(self.viper.Ref)
            ref_set = SilverType(sil_ref_set, ctx.module)
            havoc_var = ctx.actual_function.create_variable('havoc_set', ref_set,
                                                            self.translator)
            set_field = self.viper.Field('set_acc', sil_ref_set, position, info)
            content_field = self.viper.FieldAccess(result_var, set_field, position, info)
            stmts.append(self.viper.FieldAssign(content_field, havoc_var.ref(), position,
                                                info))
            arg_type = self.get_type(node.args[0], ctx)
            quant_var_name = ctx.actual_function.get_fresh_name('item')
            quant_var = self.viper.LocalVar(quant_var_name, self.viper.Ref, position,
                                            info)
            quant_var_decl = self.viper.LocalVarDecl(quant_var_name, self.viper.Ref,
                                                     position, info)
            arg_contains = self.get_function_call(arg_type, '__contains__',
                                                  [contents, quant_var], [None, None],
                                                  node, ctx)
            res_contains = self.get_function_call(set_type, '__contains__',
                                                  [result_var, quant_var], [None, None],
                                                  node, ctx)
            contain_equal = self.viper.EqCmp(arg_contains, res_contains, position, info)
            trigger = self.viper.Trigger([res_contains], position, info)
            quantifier = self.viper.Forall([quant_var_decl], [trigger], contain_equal,
                                           position, info)
            stmts.append(self.viper.Inhale(quantifier, position, info))
        return stmts, result_var

    def _translate_range(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        if len(node.args) != 2:
            msg = 'range() is currently only supported with two args.'
            raise UnsupportedException(node, msg)
        range_class = ctx.module.global_module.classes[RANGE_TYPE]
        start_stmt, start = self.translate_expr(node.args[0], ctx,
                                                self.viper.Int)
        end_stmt, end = self.translate_expr(node.args[1], ctx, self.viper.Int)
        # Add unique integer to make new instance different from other ranges.
        args = [start, end, self.get_fresh_int_lit(ctx)]
        arg_types = [None, None, None]
        call = self.get_function_call(range_class, '__create__', args,
                                      arg_types, node, ctx)
        return start_stmt + end_stmt, call

    def _translate_enumerate(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translate a call to enumerate(iterable) to a creation of a new list-object,
        an inhale about its type, and an inhale defining the contents of the new
        list.
        """
        if len(node.args) != 1:
            msg = 'enumerate() is currently only supported with one args.'
            raise UnsupportedException(node, msg)
        pos = self.to_position(node, ctx, rules=rules.INHALE_TO_CALL)
        info = self.no_info(ctx)
        result_type = self.get_type(node, ctx)
        arg_type = self.get_type(node.args[0], ctx)
        arg_stmt, arg = self.translate_expr(node.args[0], ctx)
        arg_contents = self.get_sequence(arg_type, arg, None, node.args[0], ctx)
        new_list = ctx.actual_function.create_variable('enumerate_res', result_type,
                                                       self.translator)
        sil_ref_seq = self.viper.SeqType(self.viper.Ref)
        seq_field = self.viper.Field('list_acc', sil_ref_seq, pos, info)
        new_stmt = self.viper.NewStmt(new_list.ref(), [seq_field], pos, info)
        seq_ref = self.viper.FieldAccess(new_list.ref(), seq_field, pos, info)
        prim_int_type = ctx.module.global_module.classes[PRIMITIVE_INT_TYPE]
        int_type = ctx.module.global_module.classes[INT_TYPE]
        list_type_info = self.type_check(new_list.ref(), result_type, pos, ctx)
        list_len_info = self.viper.EqCmp(self.viper.SeqLength(seq_ref, pos, info),
                                         self.viper.SeqLength(arg_contents, pos, info),
                                         pos, info)
        type_inhale = self.viper.Inhale(self.viper.And(list_type_info, list_len_info,
                                                       pos, info),
                                        pos, info)
        i_var = ctx.actual_function.create_variable('i', prim_int_type, self.translator,
                                                    False)
        orig_seq_i = self.viper.SeqIndex(arg_contents, i_var.ref(), pos, info)
        content_type = result_type.type_args[0].type_args[1]
        content_has_type = self.type_check(orig_seq_i, content_type, pos, ctx, False)
        tuple_for_i = self.create_tuple([i_var.ref(), orig_seq_i],
                                        [int_type, content_type], node, ctx)
        new_list_i = self.viper.SeqIndex(seq_ref, i_var.ref(), pos, info)
        equal_content = self.viper.EqCmp(new_list_i, tuple_for_i, pos, info)
        i_positive = self.viper.GeCmp(i_var.ref(), self.viper.IntLit(0, pos, info), pos,
                                      info)
        i_lt_len = self.viper.LtCmp(i_var.ref(), self.viper.SeqLength(seq_ref, pos, info),
                                    pos, info)
        i_in_bounds = self.viper.And(i_positive, i_lt_len, pos, info)
        content_info = self.viper.And(content_has_type, equal_content, pos, info)
        body = self.viper.Implies(i_in_bounds, content_info, pos, info)
        trigger = self.viper.Trigger([new_list_i], pos, info)
        contents_info = self.viper.Forall([i_var.decl], [trigger], body, pos, info)
        contents_inhale = self.viper.Inhale(contents_info, pos, info)
        return arg_stmt + [new_stmt, type_inhale, contents_inhale], new_list.ref(node,
                                                                                 ctx)

    def _translate_builtin_func(self, node: ast.Call,
                                ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to a builtin function like len() or isinstance()
        """
        func_name = get_func_name(node)
        if func_name == 'isinstance':
            return self._translate_isinstance(node, ctx)
        elif func_name == 'super':
            return self._translate_super(node, ctx)
        elif func_name == 'len':
            return self._translate_len(node, ctx)
        elif func_name == 'str':
            return self._translate_str(node, ctx)
        elif func_name == 'int':
            return self._translate_int(node, ctx)
        elif func_name == 'bool':
            return self._translate_bool(node, ctx)
        elif func_name == 'set':
            return self._translate_set(node, ctx)
        elif func_name == 'list':
            return self._translate_list(node, ctx)
        elif func_name == 'range':
            return self._translate_range(node, ctx)
        elif func_name == 'enumerate':
            return self._translate_enumerate(node, ctx)
        elif func_name == 'type':
            return self._translate_type_func(node, ctx)
        elif func_name == 'cast':
            return self._translate_cast_func(node, ctx)
        else:
            raise UnsupportedException(node)

    def _translate_method_call(self, target: PythonMethod, args: List[Expr],
                               arg_stmts: List[Stmt],
                               position: 'silver.ast.Position', node: ast.AST,
                               ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to an impure method, and performs any additional steps around
        it that might be necessary (e.g., folding/unfolding invariant predicates if the
        call is a lock release/acquire).
        """
        stmts = arg_stmts
        if target.name in ('acquire', 'release'):
            if (target.cls and target.cls.name == 'Lock' and
                        target.cls.module.type_prefix == 'nagini_contracts.lock'):
                if ctx.sif is True:
                    raise InvalidProgramException(node, 'concurrency.in.sif')
                # Store receiver for later use (contents of args list get changed by
                # subsequent call).
                receiver = args[0]
        call_stmt, res = self._only_translate_method_call(target, args, position, node,
                                                          ctx)
        if target.name in ('acquire', 'release'):
            if (target.cls and target.cls.name == 'Lock' and
                        target.cls.module.type_prefix == 'nagini_contracts.lock'):
                # Automatically fold/unfold the invariant predicate.
                target_name = target.cls.get_predicate('invariant').sil_name
                pos = self.to_position(node, ctx, rules=rules.LOCK_RELEASE_INVARIANT)
                info = self.no_info(ctx)
                pa = self.viper.PredicateAccess([receiver], target_name, pos, info)
                full_perm = self.viper.FullPerm(pos, info)
                pap = self.viper.PredicateAccessPredicate(pa, full_perm, pos, info)
                if target.name == 'acquire':
                    stmts.extend(call_stmt)
                    unfold = self.viper.Unfold(pap, pos, info)
                    stmts.append(unfold)
                else:
                    fold = self.viper.Fold(pap, pos, info)
                    stmts.append(fold)
                    stmts.extend(call_stmt)
        else:
            stmts.extend(call_stmt)
        return stmts, res

    def _only_translate_method_call(self, target: PythonMethod, args: List[Expr],
                                    position: 'silver.ast.Position', node: ast.AST,
                                    ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to an impure method.
        """
        targets = []
        result_var = None
        if target.type is not None:
            result_var = ctx.current_function.create_variable(
                target.name + '_res', target.type, self.translator)
            targets.append(result_var.ref())
        if target.declared_exceptions:
            error_var = self.get_error_var(node, ctx)
            targets.append(error_var)
        defined_check = []
        if target.module is not target.module.global_module:
            # Mark the current function as depending on the called method. If we're in
            # a global context, assert that the called method and its dependencies are
            # defined.
            self._add_dependencies(node.func, target, ctx)
            if self.is_main_method(ctx) and not target.cls:
                defined_check = self.assert_global_defined(target, ctx.module, node.func,
                                                           ctx)
        call = self.create_method_call_node(
            ctx, target.sil_name, args, targets, position, self.no_info(ctx),
            target_method=target, target_node=node)
        if target.declared_exceptions:
            call = call + self.create_exception_catchers(error_var,
                ctx.actual_function.try_blocks, node, ctx)
        return (defined_check + call,
                result_var.ref() if result_var else None)

    def _add_dependencies(self, reference: ast.AST, target: PythonMethod,
                          ctx: Context) -> None:
        """
        Tracks that the current container (method or class) depends on the given target,
        referring to it via the given reference.
        """
        if ctx.current_function and not self.is_main_method(ctx):
            if ctx.current_function:
                current_container = ctx.current_function.call_deps
            else:
                current_container = ctx.current_class.definition_deps
            if (isinstance(target, PythonMethod) and target.cls and
                        target.method_type == MethodType.normal):
                for subclass in target.cls.all_subclasses:
                    current = subclass.get_method(target.name)
                    current_container.add((reference, current, ctx.module, subclass))
            else:
                current_container.add((reference, target, ctx.module))

    def _translate_function_call(self, target: PythonMethod, args: List[Expr],
                                 formal_args: List[Expr], arg_stmts: List[Stmt],
                                 position: 'silver.ast.Position', node: ast.AST,
                                 ctx: Context) -> StmtsAndExpr:
        """Translates a call to a pure method."""
        type = self.translate_type(target.type, ctx)
        call = self.viper.FuncApp(target.sil_name, args, position,
                                  self.no_info(ctx), type, formal_args)
        if target.module is not target.module.global_module:
            # Mark the current function as depending on the called function. If we're in
            # a global context, wrap the result into a check that the called function and its
            # dependencies are defined.
            self._add_dependencies(node.func, target, ctx)
            if not target.cls and self.is_main_method(ctx):
                call = self.wrap_global_defined_check(call, target, ctx.module, node.func, ctx)
        return arg_stmts, call

    def _get_call_target(self, node: ast.Call,
                         ctx: Context) -> Union[PythonClass, PythonMethod]:
        """
        Returns the target of the given call; for constructor calls, the class
        whose constructor is called, for everything else the method.
        """
        target = self.get_target(node.func, ctx)
        if target:
            return target
        name = get_func_name(node)
        if name in ctx.module.classes:
            # Constructor call
            return ctx.module.classes[name]
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                if node.func.value.id in ctx.module.classes:
                    # Statically bound call
                    target_class = ctx.module.classes[node.func.value.id]
                    return target_class.get_func_or_method(node.func.attr)
            if isinstance(node.func.value, ast.Call):
                if get_func_name(node.func.value) == 'super':
                    # Super call
                    target_class = self.get_target(node.func.value, ctx)
                    return target_class.get_func_or_method(node.func.attr)
            # Method called on an object
            receiver_class = self.get_type(node.func.value, ctx)
            # When receiver's type is union, a method call have multiple
            # targets, therefore None is returned in such cases
            if isinstance(receiver_class, UnionType):
                return None
            target = receiver_class.get_predicate(node.func.attr)
            if not target:
                target = receiver_class.get_func_or_method(node.func.attr)
            return target
        else:
            # Global function/method called
            receiver_class = None
            target = ctx.module.predicates.get(name)
            if not target:
                target = ctx.module.get_func_or_method(name)
            return target

    def _has_implicit_receiver_arg(self, node: ast.Call, ctx: Context) -> bool:
        """
        Checks if the given call node will have to have a receiver added to the
        arguments in the Silver encoding.
        """
        # Get target
        called_func = self.get_target(node.func, ctx)
        if isinstance(called_func, PythonClass):
            # constructor
            return True
        # If normal
        assert isinstance(called_func, PythonMethod)
        if (isinstance(node.func, ast.Attribute) and
                get_func_name(node.func.value) == 'super'):
            return True
        if called_func.method_type == MethodType.normal:
            if isinstance(node.func, ast.Attribute):
                called_name = get_func_name(node.func.value)
                if called_name == 'Result':
                    return True
                rec_target = self.get_target(node.func.value, ctx)
                if isinstance(rec_target, PythonModule):
                    return False
                elif (isinstance(rec_target, PythonClass) and
                      not isinstance(node.func.value, ast.Call) and
                      not isinstance(node.func.value, ast.Str)):
                    return False
                else:
                    return True
            else:
                return False
        elif called_func.method_type == MethodType.class_method:
            return True
        else:
            return False

    def _translate_call_args(self, node: ast.Call,
                             ctx: Context) -> Tuple[List[Stmt], List[Expr],
                                              List[PythonType]]:
        target = self._get_call_target(node, ctx)
        if isinstance(target, PythonClass):
            constr = target.get_method('__init__')
            target = constr
        return self.translate_args(target, node.args, node.keywords, node, ctx)

    def translate_args(self, target: PythonMethod, arg_nodes: List,
                       keywords: List, node: ast.AST, ctx: Context,
                       implicit_receiver=None) -> Tuple[List[Stmt], List[Expr],
                                                        List[PythonType]]:
        """
        Returns the args and types of the given call. Named args are put into
        the correct position; for *args and **kwargs, tuples and dicts are
        created and all arguments not bound to any other parameter are put in
        there.
        """
        arg_stmts = []

        unpacked_args = []
        unpacked_arg_types = []

        for arg in arg_nodes:
            if isinstance(arg, ast.Starred):
                # If it's a starred expression, unpack all values separately
                # into unpacked_args.
                arg_stmt, arg_expr = self.translate_expr(arg.value, ctx)
                arg_type = self.get_type(arg.value, ctx)
                arg_stmts += arg_stmt

                if (isinstance(arg_type, GenericType) and
                            arg_type.name == TUPLE_TYPE):
                    if not arg_type.exact_length:
                        raise UnsupportedException(arg, 'Starred expression '
                                                        'with statically '
                                                        'unknown length.')
                    nargs = len(arg_type.type_args)
                    for i, type_arg in enumerate(arg_type.type_args):
                        index = self.viper.IntLit(i, self.no_position(ctx),
                                                  self.no_info(ctx))
                        item = self.get_function_call(arg_type, '__getitem__',
                                                      [arg_expr, index],
                                                      [None, None], arg, ctx)
                        unpacked_args.append(item)
                        unpacked_arg_types.append(type_arg)
                else:
                    raise UnsupportedException(arg, 'Starred expression which '
                                                    'is not a tuple.')
            else:
                arg_stmt, arg_expr = self.translate_expr(arg, ctx)
                arg_type = self.get_type(arg, ctx)
                arg_stmts += arg_stmt
                unpacked_args.append(arg_expr)
                unpacked_arg_types.append(arg_type)

        if not target:
            return arg_stmts, unpacked_args, unpacked_arg_types

        if implicit_receiver is None:
            implicit_receiver = self._has_implicit_receiver_arg(node, ctx)

        if target.interface:
            # For interface functions defined directly in silver, missing arguments
            # are just set to null.
            if keywords:
                raise UnsupportedException(node, desc='Keyword arguments in call to '
                                                      'builtin function.')
            diff = target.nargs - len(unpacked_args)
            if diff < 0:
                raise UnsupportedException(node, 'Unsupported version of builtin '
                                                 'function.')
            if diff > 0:
                null = self.viper.NullLit(self.no_position(ctx), self.no_info(ctx))
                unpacked_args += [null] * diff
                unpacked_arg_types += [None] * diff
            return arg_stmts, unpacked_args, unpacked_arg_types

        nargs = target.nargs
        keys = list(target.args.keys())
        if implicit_receiver:
            nargs -= 1
            keys = keys[1:]
        args = unpacked_args[:nargs]
        arg_types = unpacked_arg_types[:nargs]

        var_args = unpacked_args[nargs:]
        var_arg_types = unpacked_arg_types[nargs:]

        no_missing = len(keys) - len(args)
        args += [False] * no_missing
        arg_types += [False] * no_missing

        kw_args = OrderedDict()

        # Named args
        for kw in keywords:
            if kw.arg in keys:
                index = keys.index(kw.arg)
                arg_stmt, arg_expr = self.translate_expr(kw.value, ctx)
                arg_type = self.get_type(kw.value, ctx)
                arg_stmts += arg_stmt
                args[index] = arg_expr
                arg_types[index] = arg_type
            else:
                if target.kw_arg:
                    kw_args[kw.arg] = kw.value

        # Default args
        for index, (arg, key) in enumerate(zip(args, keys)):
            if arg is False:
                # Not set yet, need default
                args[index] = target.args[key].default_expr
                assert args[index], '{} arg={}'.format(target.name, key)
                arg_types[index] = self.get_type(target.args[key].default, ctx)

        if target.var_arg:
            var_arg_list = self.create_tuple(var_args, var_arg_types, node, ctx)
            args.append(var_arg_list)
            arg_types.append(target.var_arg.type)

        if target.kw_arg:
            kw_stmt, kw_arg_dict = self._wrap_kw_args(kw_args, node,
                                                      target.kw_arg.type, ctx)
            args.append(kw_arg_dict)
            arg_types.append(target.kw_arg.type)
            arg_stmts += kw_stmt
        assert all(args), "Args translated into None: {}.".format(args)
        return arg_stmts, args, arg_types

    def _translate_receiver(self, node: ast.Call, target: PythonMethod,
            ctx: Context) -> Tuple[List[Stmt], List[Expr], List[PythonType]]:
        rec_stmts, receiver = self.translate_expr(node.func.value, ctx)
        receiver_type = self.get_type(node.func.value, ctx)
        if (target.method_type == MethodType.class_method and
                receiver_type.name != 'type'):
            receiver = self.type_factory.typeof(receiver, ctx)

        return rec_stmts, [receiver], [receiver_type]

    def _wrap_kw_args(self, args: Dict[str, ast.AST], node: ast.Call,
                      kw_type: PythonType, ctx: Context) -> StmtsAndExpr:
        """
        Wraps the given arguments into a dict to be passed to an **kwargs param.
        """
        res_var = ctx.current_function.create_variable('kw_args',
            ctx.module.global_module.classes[DICT_TYPE], self.translator)
        dict_class = ctx.module.global_module.classes[DICT_TYPE]
        constr_call = self.get_method_call(dict_class, '__init__', [],
                                           [], [res_var.ref()], node, ctx)
        position = self.to_position(node, ctx)
        type_inhale = self.viper.Inhale(self.type_check(res_var.ref(), kw_type,
                                                        position, ctx),
                                        position, self.no_info(ctx))
        stmt = constr_call + [type_inhale]
        str_type = ctx.module.global_module.classes[STRING_TYPE]
        for key, val in args.items():
            # Key string literal
            length = len(key)
            length_arg = self.viper.IntLit(length, self.no_position(ctx),
                                           self.no_info(ctx))
            val_arg = self.viper.IntLit(self._get_string_value(key),
                                        self.no_position(ctx),
                                        self.no_info(ctx))
            str_create_args = [length_arg, val_arg]
            str_create_arg_types = [None, None]
            func_name = '__create__'
            key_val = self.get_function_call(str_type, func_name,
                                             str_create_args,
                                             str_create_arg_types, node, ctx)
            val_stmt, val_val = self.translate_expr(val, ctx)
            val_type = self.get_type(val, ctx)
            args = [res_var.ref(), key_val, val_val]
            arg_types = [None, str_type, val_type]
            append_call = self.get_method_call(dict_class, '__setitem__', args,
                                               arg_types, [], node, ctx)
            stmt += val_stmt + append_call
        return stmt, res_var.ref()

    def inline_method(self, method: PythonMethod, args: List[PythonVar],
                      result_var: PythonVar, error_var: PythonVar,
                      ctx: Context) -> Tuple[List[Stmt], 'silver.ast.Label']:
        """
        Inlines a call to the given method, if the given argument vars contain
        the values of the arguments. Saves the result in result_var and any
        uncaught exceptions in error_var.
        """
        old_label_aliases = ctx.label_aliases.copy()
        old_var_aliases = ctx.var_aliases
        var_aliases = {}

        for name, arg in zip(method.args.keys(), args):
            var_aliases[name] = arg

        var_aliases[RESULT_NAME] = result_var
        if error_var:
            var_aliases[ERROR_NAME] = error_var
        ctx.inlined_calls.append(method)
        ctx.var_aliases = var_aliases
        ctx.label_aliases = {}
        ctx.ignore_waitlevel_constraints = True

        # Create local var aliases
        locals_to_copy = method.locals.copy()
        for local_name, local in locals_to_copy.items():
            local_var = ctx.current_function.create_variable(local_name,
                                                             local.type,
                                                             self.translator)
            ctx.set_alias(local_name, local_var, local)

        # Create label aliases
        for label in method.labels:
            new_label = ctx.current_function.get_fresh_name(label)
            ctx.label_aliases[label] = new_label
        end_label_name = ctx.label_aliases[END_LABEL]
        end_label = self.viper.Label(end_label_name, self.no_position(ctx),
                                     self.no_info(ctx))
        ctx.added_handlers.append((method, ctx.var_aliases, ctx.label_aliases))

        # Translate body
        start, end = get_body_indices(method.node.body)
        stmts = []

        for stmt in method.node.body[start:end]:
            stmts += self.translate_stmt(stmt, ctx)

        ctx.inlined_calls.remove(method)
        ctx.var_aliases = old_var_aliases
        ctx.label_aliases = old_label_aliases
        return stmts, end_label

    def _inline_call(self, method: PythonMethod, node: ast.Call, is_super: bool,
                     inline_reason: str, ctx: Context) -> StmtsAndExpr:
        """
        Inlines a statically bound call to the given method. If is_super is set,
        adds self to the arguments, since this will not be part of the args
        of the call node.
        """
        assert ctx.current_function
        if method in ctx.inlined_calls:
            raise InvalidProgramException(node, 'recursive.static.call')
        position = self.to_position(node, ctx)
        old_position = ctx.position
        ctx.position.append((inline_reason, position))
        arg_stmts, arg_vals, arg_types = self._translate_call_args(node, ctx)
        args = []
        stmts = arg_stmts

        # Create local vars for parameters and assign args to them
        if is_super:
            arg_vals = ([next(iter(ctx.actual_function.args.values())).ref()] +
                        arg_vals)
        for arg_val, (_, arg) in zip(arg_vals, method.args.items()):
            arg_var = ctx.current_function.create_variable('arg', arg.type,
                                                           self.translator)
            assign = self.viper.LocalVarAssign(arg_var.ref(), arg_val,
                                               self.to_position(node, ctx),
                                               self.no_info(ctx))
            stmts.append(assign)
            args.append(arg_var)

        # Create target vars
        res_var = None
        if method.type:
            res_var = ctx.current_function.create_variable(RESULT_NAME,
                                                           method.type,
                                                           self.translator)
        optional_error_var = None
        error_var = self.get_error_var(node, ctx)
        if method.declared_exceptions:
            var = PythonVar(ERROR_NAME, None,
                            ctx.module.global_module.classes['Exception'])
            var._ref = error_var
            optional_error_var = var
        old_fold = ctx.ignore_family_folds
        ctx.ignore_family_folds = True
        inline_stmts, end_lbl = self.inline_method(method, args, res_var,
                                                   optional_error_var, ctx)
        ctx.ignore_family_folds = old_fold
        stmts += inline_stmts
        if end_lbl:
            stmts.append(end_lbl)
        if method.declared_exceptions:
            stmts += self.create_exception_catchers(error_var,
                ctx.actual_function.try_blocks, node, ctx)
        # Return result
        result = res_var.ref() if method.type else None
        ctx.position.pop()
        return stmts, result

    def translate_call_in_union(self, arg_stmts: List[Stmt], args: List[Expr],
                                arg_types: List[PythonType], rectype: UnionType,
                                node: ast.Call, ctx: Context,
                                impure: bool) -> StmtsAndExpr:
        """
        Translate a method call or function call when the receiver is of type
        union. A chain of if-then-else statements or expressions will be used
        to call the method or function of each class in the union.
        """
        pos = self.to_position(node, ctx)
        info = self.no_info(ctx)
        guard_stmts_expr = []
        value_returned = False
        pure = True

        # For each type in union (subclasses first)
        for type in toposort_classes(rectype.get_types() - {None}):

            # Create guard checking if receiver is an instance of this type
            guard = self.var_type_check(node.func.value.id, type, pos, ctx)

            # Translate the method call (method of this type)
            stmts, expr = self.translate_normal_call(
                type.get_func_or_method(node.func.attr), arg_stmts, args,
                arg_types, node, ctx, impure)

            # Stores guard and translated method call as tuple
            guard_stmts_expr.append((guard, stmts, expr))

            # Calculate properties about the return value
            value_returned = value_returned or expr is not None
            pure = pure and len(stmts) == 0

        # Sanitize return value properties
        assert not pure or value_returned

        if not pure and value_returned:

            # Create a variable to assign the returned value
            return_var = ctx.current_function.create_variable('return_var',
                         ctx.module.global_module.classes[OBJECT_TYPE],
                         self.translator)

            for _, stmts, expr in guard_stmts_expr:
                if expr is not None:

                    # Assign the returned value to fresh variable
                    stmts.append(self.viper.LocalVarAssign(return_var.ref(
                                 node, ctx), expr, pos, info))

        if pure:

            # Chain list of guard and pure expression tuples in an if-then-else
            # expression
            guarded_expr = [(guard, expr) for guard, _, expr in guard_stmts_expr]
            return [], chain_cond_exp(guarded_expr, self.viper, pos, info, ctx)
        else:

            # Chain guards and blocks in an if-then-else statement
            guarded_blocks = [(guard, self.translate_block(stmts, pos, info))
                              for guard, stmts, _ in guard_stmts_expr]
            return ([chain_if_stmts(guarded_blocks, self.viper, pos, info, ctx)],
                    return_var._ref if value_returned else None)

    def translate_normal_call_node(self, node: ast.Call, ctx: Context,
                                   impure=False) -> StmtsAndExpr:
        """
        Translates a call node which refers to a 'normal' function, method or predicate.
        """
        arg_stmts, args, arg_types = self._translate_call_args(node, ctx)
        target = self._get_call_target(node, ctx)
        if not target:
            # Handle method calls when receiver's type is union
            if isinstance(node.func, ast.Attribute):
                rectype = self.get_type(node.func.value, ctx)
                if (isinstance(rectype, UnionType) and
                        not isinstance(rectype, OptionalType)):
                    # Check if the call refers to a predicate (family),
                    # in which case we don't need special treatment.
                    target_pred = rectype.python_class.get_predicate(node.func.attr)
                    if target_pred:
                        return self.translate_normal_call(target_pred, arg_stmts, args,
                                                          arg_types, node, ctx, impure)
                    # Otherwise apply special union treatment.
                    return self.translate_call_in_union(arg_stmts, args, arg_types,
                                                        rectype, node, ctx, impure)

            # Must be a function that exists (otherwise mypy would complain)
            # we don't know, so probably some builtin we don't support yet.
            msg = 'Unsupported builtin function'
            if ctx.actual_function.method_type == MethodType.class_method:
                msg += ' or indirect call of classmethod argument'
            raise UnsupportedException(node, msg + '.')
        if isinstance(target, PythonClass):
            return self.translate_constructor_call(target, node, args,
                                                   arg_stmts, ctx)
        return self.translate_normal_call(target, arg_stmts, args, arg_types, node, ctx,
                                          impure)

    def translate_normal_call(self, target: PythonMethod, arg_stmts: List[Stmt],
                              args: List[Expr], arg_types: List[PythonType],
                              node: ast.AST, ctx: Context, impure=False) -> StmtsAndExpr:
        """
        Translates a 'normal' function call, i.e., target must refer to a normal function,
        method or predicate.
        """
        formal_args = []
        name = get_func_name(node)
        position = self.to_position(node, ctx)
        is_predicate = True
        if isinstance(node.func, ast.Attribute):
            receiver_target = self.get_target(node.func.value, ctx)
            if (isinstance(receiver_target, PythonClass) and
                    (not isinstance(node.func.value, (ast.Call, ast.Str)) or
                             get_func_name(node.func.value) == 'super')):
                if target.method_type == MethodType.static_method:
                    # Static method
                    receiver_class = None
                    is_predicate = target.predicate
                elif target.method_type == MethodType.class_method:
                    rec_stmt, receiver = self.translate_expr(node.func.value,
                                                             ctx)
                    arg_stmts = rec_stmt + arg_stmts
                    args = [receiver] + args
                    arg_types = ([ctx.module.global_module.classes['type']] +
                                 arg_types)
                    receiver_class = receiver_target
                    is_predicate = False
                else:
                    # Statically bound call
                    is_super = get_func_name(node.func.value) == 'super'
                    if is_super:
                        if not self.is_valid_super_call(node.func.value,
                                                        ctx.actual_function):
                            raise InvalidProgramException(node.func.value,
                                                          'invalid.super.call')
                    return self._inline_call(target, node, is_super,
                                            'static call', ctx)
            elif isinstance(receiver_target, PythonModule):
                # Normal, receiverless call to imported function
                receiver_class = None
                is_predicate = target.predicate
            elif (isinstance(node.func.value, ast.Call) and
                        get_func_name(node.func.value) == 'super' and not (target.cls and target.cls.name == 'dict')):
                    # Super call
                    return self._inline_call(target, node, True, 'static call',
                                             ctx)
            else:
                # Method called on an object
                recv_stmts, recv_exprs, recv_types = self._translate_receiver(
                    node, target, ctx)
                if ctx.sif == 'prob' and target.method_type == MethodType.normal and not target.pure and not target.predicate:
                    info = self.no_info(ctx)
                    recv_pos = self.to_position(node.func.value, ctx, rules=rules.BRANCH_RECEIVER_LOW)
                    recv_stmts.append(self.viper.Assert(self.viper.Low(self.type_factory.typeof(recv_exprs[0], ctx), None, recv_pos, info), recv_pos, info))
                is_predicate = target.predicate
                receiver_class = target.cls
                if target.method_type != MethodType.static_method:
                    arg_stmts = recv_stmts + arg_stmts
                    args = recv_exprs + args
                    arg_types = recv_types + arg_types
        else:
            # Global function/method called
            receiver_class = None
            is_predicate = target.predicate
        actual_args = []
        target_params = target.get_args()
        if target.var_arg:
            target_params.append(target.var_arg)
        if target.kw_arg:
            target_params.append(target.kw_arg)
        for arg, param, type in zip(args, target_params, arg_types):
            target_type = self.translate_type(param.type, ctx)
            actual_args.append(self.convert_to_type(arg, target_type, ctx))
        args = actual_args
        for arg in target.get_args():
            formal_args.append(arg.decl)
        target_name = target.sil_name
        if is_predicate:
            if receiver_class:
                family_root = receiver_class
                while (family_root.superclass and
                       family_root.superclass.get_predicate(name)):
                    family_root = family_root.superclass
                target_name = family_root.get_predicate(name).sil_name
            perm = self.viper.FullPerm(position, self.no_info(ctx))
            if not impure:
                raise InvalidProgramException(node, 'invalid.contract.position')
            return arg_stmts, self.create_predicate_access(target_name, args,
                                                           perm, node, ctx)
        elif target.pure:
            return self._translate_function_call(target, args, formal_args,
                                                 arg_stmts, position, node, ctx)
        else:
            return self._translate_method_call(target, args, arg_stmts,
                                               position, node, ctx)

    def _is_thread_method_call(self, node: ast.Call, name: str, ctx: Context) -> bool:
        """
        Checks if a given call calls a method of the given name defined by the Thread
        class.
        """
        if isinstance(node.func, ast.Attribute):
            val_type = self.get_type(node.func.value, ctx)
            if (isinstance(val_type, PythonClass) and
                    val_type.name == "Thread" and
                    node.func.attr == name):
                return True
        return False

    def translate_Call(self, node: ast.Call, ctx: Context, impure=False,
                       statement=False) -> StmtsAndExpr:
        """
        Translates any kind of call. This can be a call to a contract function
        like Assert, a builtin Python function like isinstance, a
        constructor call, a 'call' to a predicate, a pure function or impure
        method call, on a receiver object or not.
        Top-level contract statements like Assert are only allowed if the
        'statement' flag is set.
        """

        is_name = isinstance(node.func, ast.Name)

        if is_name:
            func_name = get_func_name(node)
            if func_name in CONTRACT_WRAPPER_FUNCS:
                raise InvalidProgramException(node, 'invalid.contract.position')
            elif func_name in CONTRACT_FUNCS:
                old_allow_statements = ctx.allow_statements
                ctx.allow_statements = False
                res = self.translate_contractfunc_call(node, ctx, impure, statement)
                ctx.allow_statements = old_allow_statements
                return res
            elif func_name in IO_CONTRACT_FUNCS:
                old_allow_statements = ctx.allow_statements
                ctx.allow_statements = False
                res = self.translate_io_contractfunc_call(node, ctx, impure, statement)
                ctx.allow_statements = old_allow_statements
                return res
            elif func_name in OBLIGATION_CONTRACT_FUNCS:
                return self.translate_obligation_contractfunc_call(node, ctx, impure)
            elif func_name in BUILTINS:
                return self._translate_builtin_func(node, ctx)
            elif func_name == "Thread":
                return self._translate_thread_creation(node, ctx)
            elif func_name in BUILTIN_PREDICATES:
                return self.translate_contractfunc_call(node, ctx, impure)
        elif isinstance(node.func, ast.Call):
            if get_func_name(node.func) == 'IOExists':
                return self.translate_expr(node.args[0].body, ctx, impure=impure)
        if self._is_cls_call(node, ctx):
            return self._translate_cls_call(node, ctx)
        elif isinstance(self.get_target(node, ctx), PythonIOOperation):
            if not impure:
                raise InvalidProgramException(node, 'invalid.contract.position')
            return self.translate_io_operation_call(node, ctx)
        elif self._is_thread_method_call(node, 'start', ctx):
            return self._translate_thread_start(node, ctx)
        elif self._is_thread_method_call(node, 'join', ctx):
            return self._translate_thread_join(node, ctx)
        else:
            return self.translate_normal_call_node(node, ctx, impure)

    def _get_arg(self, nargs: int, keywords: List[str], index: int, kw: str) -> int:
        if nargs > index:
            return index
        if kw in keywords:
            return nargs + keywords.index(kw)
        return None

    def _handle_thread_constructor_args(self, node: ast.Call, ctx: Context):
        pos, info = self.to_position(node, ctx), self.no_info(ctx)
        # Map arguments to parameters
        arg_exprs = [a for a in node.args] + [kw.value for kw in node.keywords]
        keywords = [kw.arg for kw in node.keywords]

        group_arg = self._get_arg(len(node.args), keywords, 0, 'group')
        target_arg = self._get_arg(len(node.args), keywords, 1, 'target')
        name_arg = self._get_arg(len(node.args), keywords, 2, 'name')
        args_arg = self._get_arg(len(node.args), keywords, 3, 'args')
        kwargs_arg = self._get_arg(len(node.args), keywords, 4, 'kwargs')
        daemon_arg = self._get_arg(len(node.args), keywords, 5, 'daemon')

        if target_arg is None:
            raise InvalidProgramException(node, 'invalid.thread.creation')
        if kwargs_arg or daemon_arg:
            raise UnsupportedException(node, 'Unsupported thread parameter.')

        # Translate argument expressions, except target and args.
        thread_arg_stmts = []
        thread_arg_vals = []
        for index, expr in enumerate(arg_exprs):
            if index is target_arg or index is args_arg:
                thread_arg_vals.append(None)
                continue
            arg_stmt, arg_val = self.translate_expr(expr, ctx)
            thread_arg_stmts.extend(arg_stmt)
            thread_arg_vals.append(arg_val)

        target_arg = arg_exprs[target_arg]
        args_arg = arg_exprs[args_arg]

        if group_arg is not None:
            # The group argument must be None, everything else leads to a runtime error.
            group_none_pos = self.to_position(node, ctx, error_string='group is None',
                                              rules=rules.THREAD_CREATION_GROUP_NONE)
            null = self.viper.NullLit(group_none_pos, info)
            is_none = self.viper.EqCmp(thread_arg_vals[group_arg], null, group_none_pos,
                                       info)
            assert_none = self.viper.Assert(is_none, group_none_pos, info)
            thread_arg_stmts.append(assert_none)

        target = self.get_target(target_arg, ctx)
        if not isinstance(target, PythonMethod):
            raise InvalidProgramException(node, 'invalid.thread.creation')
        if target.pure or target.predicate:
            raise InvalidProgramException(node, 'invalid.thread.creation')
        if not isinstance(args_arg, ast.Tuple):
            raise InvalidProgramException(node, 'invalid.thread.creation')
        meth_args = args_arg.elts if args_arg is not None else []

        if isinstance(target_arg, ast.Attribute):
            receiver = self.get_target(target_arg.value, ctx)
            if not isinstance(receiver, PythonType):
                meth_args = [target_arg.value] + meth_args

        if len(meth_args) != len(target.args):
            no_default_args = [arg for arg in target.args.values()
                               if arg.default_expr is None]
            if len(no_default_args) != len(target.args):
                raise UnsupportedException(node, 'Thread target with default arguments.')
            else:
                raise InvalidProgramException(node, 'invalid.thread.creation')
        return thread_arg_stmts, meth_args, target

    def _translate_thread_creation(self, node: ast.Call,
                                   ctx: Context) -> StmtsAndExpr:
        """Translates the instantiation of a Thread object."""
        if ctx.sif is True:
            raise InvalidProgramException(node, 'concurrency.in.sif')
        ctx.are_threading_constants_used = True
        pos, info = self.to_position(node, ctx), self.no_info(ctx)

        thread_arg_stmts, meth_args, target = self._handle_thread_constructor_args(node,
                                                                                   ctx)

        # Create thread object
        thread_class = ctx.module.global_module.classes['Thread']
        thread_var = ctx.actual_function.create_variable('threadingVar', thread_class,
                                                         self.translator)
        thread = thread_var.ref(node, ctx)
        newstmt = self.viper.NewStmt(thread, [], pos, info)

        thread_object_type = self.type_check(thread, thread_class, pos, ctx)
        inhale_thread_type = self.viper.Inhale(thread_object_type, pos, info)

        # Inhale MayStart(t)
        start_pred_acc = self.viper.PredicateAccess([thread], THREAD_START_PRED,
                                                    pos, info)
        full_perm = self.viper.FullPerm(pos, info)
        start_pred = self.viper.PredicateAccessPredicate(start_pred_acc, full_perm, pos,
                                                         info)
        inhale_start_perm = self.viper.Inhale(start_pred, pos, info)

        # Check that given arguments match target method's parameter types,
        # and associate arguments and target method with thread object (by inhaling
        # getArg and getMethod information).
        arg_stmts = []
        arg_assumptions = self.viper.TrueLit(pos, info)
        arg_type_checks = self.viper.TrueLit(pos, info)
        method_args = list(target._args.values())
        for i, arg in enumerate(meth_args):
            arg_stmt, arg_val = self.translate_expr(arg, ctx, self.viper.Ref)
            arg_stmts.extend(arg_stmt)
            index = self.viper.IntLit(i, pos, info)
            arg_func = self.viper.DomainFuncApp(GET_ARG_FUNC, [thread, index],
                                                self.viper.Ref, pos, info, THREAD_DOMAIN)
            func_equal = self.viper.EqCmp(arg_func, arg_val, pos, info)
            arg_assumptions = self.viper.And(arg_assumptions, func_equal, pos, info)
            arg_type_check = self.type_check(arg_val, method_args[i].type, pos, ctx)
            arg_type_checks = self.viper.EqCmp(arg_type_checks, arg_type_check, pos, info)

        method_id_type = self.viper.DomainType(METHOD_ID_DOMAIN, {}, [])
        thread_method = self.viper.DomainFuncApp(GET_METHOD_FUNC, [thread],
                                                 method_id_type, pos, info, THREAD_DOMAIN)
        actual_method = self.viper.DomainFuncApp(target.threading_id, [], method_id_type,
                                                 pos, info, METHOD_ID_DOMAIN)
        inhale_method = self.viper.Inhale(self.viper.EqCmp(thread_method, actual_method,
                                                           pos, info),
                                          pos, info)
        arg_check_pos = self.to_position(node, ctx, rules=rules.THREAD_CREATION_ARG_TYPE)
        check_arg_types = self.viper.Assert(arg_type_checks, arg_check_pos, info)
        inhale_args = self.viper.Inhale(arg_assumptions, pos, info)
        stmts = thread_arg_stmts + arg_stmts + [newstmt, inhale_thread_type,
                                                inhale_method, check_arg_types,
                                                inhale_args, inhale_start_perm]
        return stmts, thread

    def _translate_thread_start(self, node: ast.Call,
                                ctx: Context) -> StmtsAndExpr:
        """Translates a thread start call."""
        if ctx.sif is True:
            raise InvalidProgramException(node, 'concurrency.in.sif')
        ctx.are_threading_constants_used = True
        pos, info = self.to_position(node, ctx), self.no_info(ctx)
        assert isinstance(node.func, ast.Attribute)
        thread_stmt, thread = self.translate_expr(node.func.value, ctx)
        ctx.current_thread_object, ctx.is_thread_start = thread, True

        # Resolve list of possible target methods.
        method_options = []
        for arg in node.args:
            target = self.get_target(arg, ctx)
            if not (isinstance(target, PythonMethod) and not target.pure and
                        not target.predicate):
                raise InvalidProgramException(node, 'invalid.thread.start')
            method_options.append(target)

        stmts = []

        # Exhale MayStart predicate
        start_pred_pos = self.to_position(node, ctx, rules=rules.THREAD_START_PERMISSION)
        full_perm = self.viper.FullPerm(start_pred_pos, info)
        start_pred_acc = self.viper.PredicateAccess([thread], THREAD_START_PRED,
                                                    start_pred_pos,
                                                    info)
        start_pred = self.viper.PredicateAccessPredicate(start_pred_acc, full_perm,
                                                         start_pred_pos, info)
        stmts.append(self.viper.Exhale(start_pred, start_pred_pos, info))

        # Assert that actual target method is in list of options.
        options_pos = self.to_position(node, ctx,
                                       rules=rules.THREAD_START_METHOD_UNLISTED)
        correct_method = self.viper.FalseLit(options_pos, info)
        method_id_type = self.viper.DomainType(METHOD_ID_DOMAIN, {}, [])
        actual_method = self.viper.DomainFuncApp(GET_METHOD_FUNC, [thread],
                                                 method_id_type, options_pos, info,
                                                 THREAD_DOMAIN)
        for method in method_options:
            this_method = self.viper.DomainFuncApp(method.threading_id, [],
                                                   method_id_type, options_pos, info,
                                                   METHOD_ID_DOMAIN)
            this_option = self.viper.EqCmp(actual_method, this_method, options_pos, info)
            correct_method = self.viper.Or(correct_method, this_option, options_pos, info)
        stmts.append(self.viper.Assert(correct_method, options_pos, info))
        precond_pos = self.to_position(node, ctx, rules=rules.THREAD_START_PRECONDITION)

        # Actual fork operation is carried out elsewhere.
        stmts.extend(self.create_method_fork(ctx, method_options, thread, precond_pos,
                                             info, node))
        ctx.current_thread_object, ctx.is_thread_start = None, False
        return thread_stmt + stmts, None

    def _translate_thread_join(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """Translates a thread join call."""
        if ctx.sif is True:
            raise InvalidProgramException(node, 'concurrency.in.sif')
        ctx.are_threading_constants_used = True
        pos, info = self.to_position(node, ctx), self.no_info(ctx)
        assert isinstance(node.func, ast.Attribute)
        thread_stmt, thread = self.translate_expr(node.func.value, ctx)
        ctx.current_thread_object, ctx.is_thread_start = thread, False
        stmts = thread_stmt

        # Assert that thread may be joined.
        joinable_pos = self.to_position(node, ctx, rules=rules.THREAD_JOIN_JOINABLE)
        joinable_func = self.viper.FuncApp(JOINABLE_FUNC, [thread],
                                           joinable_pos, info,
                                           self.viper.Bool)

        stmts.append(self.viper.Assert(joinable_func, joinable_pos, info))

        # Check that thread wait level is above current wait level (prevents deadlocks).
        wait_level_pos = self.to_position(node, ctx, rules=rules.THREAD_JOIN_WAITLEVEL)
        thread_level = self.create_level_call(sil.RefExpr(thread))
        residue_var = sil.PermVar(ctx.actual_function.obligation_info.residue_level)
        obligation_assertion = self.create_level_below(thread_level, residue_var, ctx)
        obligation_assertion = obligation_assertion.translate(self, ctx, wait_level_pos,
                                                              info)
        if not obligation_config.disable_waitlevel_check:
            stmts.append(self.viper.Assert(obligation_assertion, wait_level_pos, info))

        # Check how much permission is held to ThreadPost. This amount of the thread
        # postcondition will be inhaled later.
        post_pred_acc = self.viper.PredicateAccess([thread], THREAD_POST_PRED, pos, info)
        post_perm = self.viper.CurrentPerm(post_pred_acc, pos, info)
        any_perm = self.viper.PermGtCmp(post_perm, self.viper.NoPerm(pos, info), pos,
                                        info)

        # Any subsequently translated assertions (postconditions) are multiplied by this
        # amount of permission.
        ctx.perm_factor = post_perm

        object_class = ctx.module.global_module.classes[OBJECT_TYPE]
        res_var = ctx.actual_function.create_variable('join_result', object_class,
                                                      self.translator)

        # Resolve list of possible thread target methods.
        method_options = []
        for arg in node.args:
            target = self.get_target(arg, ctx)
            if not (isinstance(target, PythonMethod) and not target.pure and
                        not target.predicate):
                raise InvalidProgramException(node, 'invalid.thread.join')
            method_options.append(target)

        # Conditionally inhale postconditions of target methods.
        for method in method_options:
            stmts.append(self._inhale_possible_thread_post(method, thread, res_var,
                                                           any_perm, pos, ctx))

        ctx.perm_factor = None

        post_pred = self.viper.PredicateAccessPredicate(post_pred_acc, post_perm, pos,
                                                        info)
        exhale_pred = self.viper.Exhale(post_pred, pos, info)
        stmts.append(exhale_pred)
        ctx.current_thread_object, ctx.is_thread_start = None, False

        return stmts, None

    def _inhale_possible_thread_post(self, method: PythonMethod, thread: Expr,
                                     res_var: PythonVar, any_perm: Expr, pos: Position,
                                     ctx: Context) -> Stmt:
        """
        Creates a statement that inhales this method's postcondition if this is
        the target method of the given thread.
        """
        method_stmts = []
        info = self.no_info(ctx)
        else_block = self.translate_block([], pos, info)
        method_id_type = self.viper.DomainType(METHOD_ID_DOMAIN, {}, [])
        actual_method = self.viper.DomainFuncApp(GET_METHOD_FUNC, [thread],
                                                 method_id_type, pos, info, THREAD_DOMAIN)

        # Set arg aliases with types
        for index, arg in enumerate(method._args.values()):
            arg_var = ctx.actual_function.create_variable('thread_arg', arg.type,
                                                          self.translator)
            ctx.set_alias(arg.name, arg_var)
            id = self.viper.IntLit(index, pos, info)
            arg_func = self.viper.DomainFuncApp(GET_ARG_FUNC, [thread, id],
                                                self.viper.Ref, pos, info,
                                                THREAD_DOMAIN)
            method_stmts.append(self.viper.LocalVarAssign(arg_var.ref(), arg_func,
                                                          pos, info))
            method_stmts.append(self.viper.Inhale(self.type_check(arg_var.ref(),
                                                                  arg.type, pos, ctx,
                                                                  inhale_exhale=False),
                                                  pos, info))
        if method.type:
            ctx.set_alias(RESULT_NAME, res_var)
            res_var.type = method.type

        # Set old values
        collector = OldExpressionCollector()
        normalizer = OldExpressionTransformer()
        normalizer.arg_names = [arg for arg in method._args]
        for post, _ in method.postcondition:
            collector.visit(post)
        for old in collector.expressions:
            print_old = normalizer.visit(copy.deepcopy(old))
            key = pprint(print_old)
            id = self.viper.IntLit(self._get_string_value(key), pos, info)
            old_func = self.viper.DomainFuncApp(GET_OLD_FUNC, [thread, id],
                                                self.viper.Ref, pos, info,
                                                THREAD_DOMAIN)
            ctx.set_old_expr_alias(key, old_func)
            old_type = self.get_type(old, ctx)
            method_stmts.append(self.viper.Inhale(self.type_check(old_func,
                                                                  old_type, pos, ctx,
                                                                  inhale_exhale=False),
                                                  pos, info))

        post_assertion = self.viper.TrueLit(pos, info)
        ctx.inlined_calls.append(method)

        # Translate postcondition
        for post, _ in method.postcondition:
            _, post_val = self.translate_expr(post, ctx, target_type=self.viper.Bool,
                                              impure=True)
            post_assertion = self.viper.And(post_assertion, post_val, pos, info)

        ctx.inlined_calls.pop()
        ctx.clear_old_expr_aliases()
        for name in method._args:
            ctx.remove_alias(name)
        ctx.remove_alias(RESULT_NAME)
        ctx.ignore_waitlevel_constraints = False

        # Inhale postcondition if there's a permission to ThreadPost and this method
        # is the actual method.
        method_stmts.append(self.viper.Inhale(post_assertion, pos, info))
        then_block = self.translate_block(method_stmts, pos, info)
        this_method = self.viper.DomainFuncApp(method.threading_id, [],
                                               method_id_type, pos, info,
                                               METHOD_ID_DOMAIN)
        correct_method = self.viper.EqCmp(actual_method, this_method, pos, info)
        cond = self.viper.And(any_perm, correct_method, pos, info)
        return self.viper.If(cond, then_block, else_block, pos, info)

    def _is_cls_call(self, node: ast.Call, ctx: Context) -> bool:
        """
        Checks if the given call is a call to the cls parameter in a class
        method.
        """
        if (ctx.actual_function and
            isinstance(ctx.actual_function, PythonMethod) and
            ctx.actual_function.method_type == MethodType.class_method):
            if isinstance(node.func, ast.Name):
                if node.func.id == next(iter(ctx.actual_function.args.keys())):
                    return True
        return False

    def _translate_cls_call(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to the cls parameter in a class method.
        """
        target_class = ctx.actual_function.cls
        args = []
        arg_stmts = []
        for arg in node.args:
            arg_stmt, arg_val = self.translate_expr(arg, ctx)
            arg_stmts += arg_stmt
            args.append(arg_val)
        res_var = ctx.current_function.create_variable(target_class.name +
                                                       '_res',
                                                       target_class,
                                                       self.translator)

        pos = self.to_position(node, ctx)
        fields = list(target_class.all_fields)
        may_set_inhales = [self.viper.Inhale(self.get_may_set_predicate(res_var.ref(),
                                                                        f, ctx),
                                             pos, self.no_info(ctx))
                           for f in fields]
        new = self.viper.NewStmt(res_var.ref(), [], self.no_position(ctx),
                                 self.no_info(ctx))

        type_stmt, dynamic_type = self.translate_expr(node.func, ctx)
        assert not type_stmt
        result_has_type = self.type_factory.dynamic_type_check(res_var.ref(),
            dynamic_type, self.to_position(node, ctx), ctx)
        # Inhale the type information about the newly created object
        # so that it's already present when calling __init__.
        type_inhale = self.viper.Inhale(result_has_type, pos,
                                        self.no_info(ctx))
        args = [res_var.ref()] + args
        stmts = [new, type_inhale] + may_set_inhales
        target = target_class.get_method('__init__')
        if target:
            target_class = target.cls
            targets = []
            if target.declared_exceptions:
                error_var = self.get_error_var(node, ctx)
                targets.append(error_var)
            target_method = target_class.get_method('__init__')
            method_name = target_method.sil_name
            init = self.create_method_call_node(ctx, method_name, args, targets,
                                                self.to_position(node, ctx),
                                                self.no_info(ctx),
                                                target_method=target_method,
                                                target_node=node)
            stmts.extend(init)
            if target.declared_exceptions:
                catchers = self.create_exception_catchers(error_var,
                    ctx.actual_function.try_blocks, node, ctx)
                stmts = stmts + catchers
        return arg_stmts + stmts, res_var.ref()
