"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import ast
import copy

from collections import OrderedDict
from nagini_contracts.contracts import (
    CONTRACT_FUNCS,
    CONTRACT_WRAPPER_FUNCS
)
from nagini_contracts.io import IO_CONTRACT_FUNCS
from nagini_contracts.obligations import OBLIGATION_CONTRACT_FUNCS
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
    JOINABLE_FUNC,
    LIST_TYPE,
    METHOD_ID_DOMAIN,
    OBJECT_TYPE,
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
    GenericType,
    MethodType,
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
    Stmt,
    StmtsAndExpr,
)
from nagini_translation.lib.util import (
    get_body_indices,
    get_func_name,
    InvalidProgramException,
    OldExpressionCollector,
    OldExpressionNormalizer,
    pprint,
    UnsupportedException,
)
from nagini_translation.translators.abstract import Context
from nagini_translation.translators.common import CommonTranslator
from typing import Dict, List, Tuple, Union, Set


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
        arg_type = self.get_type(node.args[0], ctx)
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

    def _translate_bool(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        assert len(node.args) == 1
        stmt, target = self.translate_expr(node.args[0], ctx)
        arg_type = self.get_type(node.args[0], ctx)
        bool_stmt, bool_val = self.get_func_or_method_call(arg_type, '__bool__', [target],
                                                           [None], node, ctx)
        return stmt + bool_stmt, bool_val

    def _translate_super(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        if len(node.args) == 2:
            if self.is_valid_super_call(node, ctx):
                return self.translate_expr(node.args[1], ctx)
            else:
                raise InvalidProgramException(node, 'invalid.super.call')
        elif not node.args:
            arg_name = next(iter(ctx.actual_function.args))
            if arg_name in ctx.var_aliases:
                replacement = ctx.var_aliases[arg_name]
                return replacement.ref(node, ctx)
            return [], ctx.current_function.args[arg_name].ref(node, ctx)
        else:
            raise InvalidProgramException(node, 'invalid.super.call')

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
        res_var = ctx.current_function.create_variable(target_class.name +
                                                       '_res',
                                                       target_class,
                                                       self.translator)
        result_type = self.get_type(node, ctx)
        pos = self.to_position(node, ctx)
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
        # Mark the current function as depending on the called class. If we're in
        # a global context, assert that the called class and its dependencies are defined.
        func_node = node.func if isinstance(node, ast.Call) else node
        self._add_dependencies(func_node, target_class, ctx)
        defined_check = []
        if self.is_main_method(ctx):
            defined_check = self.assert_global_defined(target_class, ctx.module, node.func,
                                                       ctx)

        # Inhale the type information about the newly created object
        # so that it's already present when calling __init__.
        type_inhale = self.viper.Inhale(result_has_type, pos,
                                        self.no_info(ctx))
        args = [res_var.ref()] + args
        stmts = [new, type_inhale] + may_set_inhales

        if self._is_lock_subtype(target_class):
            lock_class = self._is_lock_subtype(target_class)
            locked_obj = self.get_function_call(lock_class, 'get_locked', [res_var.ref()],
                                                [None], node, ctx, pos)
            arg_is_locked = self.viper.EqCmp(locked_obj, args[1], pos, info)
            stmts.append(self.viper.Inhale(arg_is_locked, pos, info))
            invariant_pred = lock_class.get_predicate('invariant')
            full_perm = self.viper.FullPerm(pos, info)
            pred_acc = self.viper.PredicateAccess([res_var.ref()],
                                                  invariant_pred.sil_name, pos, info)
            acc_pred = self.viper.PredicateAccessPredicate(pred_acc, full_perm, pos, info)
            stmts.append(self.viper.Fold(acc_pred, pos, info))

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
            havoc_var = ctx.actual_function.create_variable('havoc_seq', ref_seq, self.translator)
            seq_field = self.viper.Field('list_acc', sil_ref_seq, position, info)
            content_field = self.viper.FieldAccess(result_var, seq_field, position, info)
            stmts.append(self.viper.FieldAssign(content_field, havoc_var.ref(), position,
                                                info))
            arg_type = self.get_type(node.args[0], ctx)
            arg_seq = self.get_function_call(arg_type, '__sil_seq__', [contents], [None], node, ctx)
            res_seq = self.get_function_call(set_type, '__sil_seq__', [result_var], [None], node, ctx)
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
            havoc_var = ctx.actual_function.create_variable('havoc_set', ref_set, self.translator)
            set_field = self.viper.Field('set_acc', sil_ref_set, position, info)
            content_field = self.viper.FieldAccess(result_var, set_field, position, info)
            stmts.append(self.viper.FieldAssign(content_field, havoc_var.ref(), position,
                                                info))
            arg_type = self.get_type(node.args[0], ctx)
            quant_var_name = ctx.actual_function.get_fresh_name('item')
            quant_var = self.viper.LocalVar(quant_var_name, self.viper.Ref, position, info)
            quant_var_decl = self.viper.LocalVarDecl(quant_var_name, self.viper.Ref, position,
                                                     info)
            arg_contains = self.get_function_call(arg_type, '__contains__', [contents, quant_var], [None, None], node, ctx)
            res_contains = self.get_function_call(set_type, '__contains__', [result_var, quant_var], [None, None], node, ctx)
            contain_equal = self.viper.EqCmp(arg_contains, res_contains, position, info)
            trigger = self.viper.Trigger([res_contains], position, info)
            quantifier = self.viper.Forall([quant_var_decl], [trigger], contain_equal, position, info)
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
        elif func_name == 'bool':
            return self._translate_bool(node, ctx)
        elif func_name == 'set':
            return self._translate_set(node, ctx)
        elif func_name == 'list':
            return self._translate_list(node, ctx)
        elif func_name == 'range':
            return self._translate_range(node, ctx)
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
        return (arg_stmts + defined_check + call,
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
            # a global context, wrap the result into a check that the called function and
            # its dependencies are defined.
            self._add_dependencies(node.func, target, ctx)
            if not target.cls and self.is_main_method(ctx):
                call = self.wrap_global_defined_check(call, target, ctx.module, node.func,
                                                      ctx)
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
                if called_name in ('Result', 'TypedResult'):
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
        stmts.append(end_lbl)
        if method.declared_exceptions:
            stmts += self.create_exception_catchers(error_var,
                ctx.actual_function.try_blocks, node, ctx)
        # Return result
        result = res_var.ref() if method.type else None
        ctx.position.pop()
        return stmts, result

    def translate_method_call_in_union(self, arg_stmts: List[Stmt], args: List[Expr],
                                       arg_types: List[PythonType], rectype: UnionType,
                                       node: ast.Call, ctx: Context,
                                       impure) -> StmtsAndExpr:
        """
        Translate a method call, when the receiver is of type union, into an if-then-else
        chain of method calls, one for each class in the union according to receiver's
        type.
        """
        position = self.to_position(node, ctx)
        info = self.no_info(ctx)
        guarded_blocks = []
        # For each class in union
        for type in toposort_classes(rectype.get_types() - {None}):
            # If receiver is an instance of this particular class
            method_call_guard = self.var_type_check(node.func.value.id, type, position,
                                                    ctx)
            # Call its respective method
            method_call, return_var = self.translate_normal_call(
                type.get_func_or_method(node.func.attr), arg_stmts,
                args, arg_types, node, ctx, impure)
            if 'final_return_var' not in locals():
                final_return_var = return_var
            else:
                if return_var:
                    method_call.append(self.viper.LocalVarAssign(final_return_var,
                                       return_var, position, info))
            method_call_block = self.translate_block(method_call, position, info)
            guarded_blocks.append((method_call_guard, method_call_block))
        return ([chain_if_stmts(guarded_blocks, self.viper, position, info, ctx)],
                final_return_var)

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
                if isinstance(rectype, UnionType):
                    return self.translate_method_call_in_union(arg_stmts, args, arg_types,
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
                        get_func_name(node.func.value) == 'super'):
                    # Super call
                    return self._inline_call(target, node, True, 'static call',
                                             ctx)
            else:
                # Method called on an object
                recv_stmts, recv_exprs, recv_types = self._translate_receiver(
                    node, target, ctx)
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
            if ctx.current_function.pure:
                perm = self.viper.WildcardPerm(position, self.no_info(ctx))
            else:
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
        if isinstance(node.func, ast.Attribute):
            val_type = self.get_type(node.func.value, ctx)
            if (isinstance(val_type, PythonClass) and
                        val_type.name == "Thread" and
                        node.func.attr == name):
                return True
            return False

    def translate_Call(self, node: ast.Call, ctx: Context, impure=False) -> StmtsAndExpr:
        """
        Translates any kind of call. This can be a call to a contract function
        like Assert, a builtin Python function like isinstance, a
        constructor call, a 'call' to a predicate, a pure function or impure
        method call, on a receiver object or not.
        """

        is_name = isinstance(node.func, ast.Name)
        func_name = get_func_name(node)
        if is_name:
            if func_name in CONTRACT_WRAPPER_FUNCS:
                raise InvalidProgramException(node, 'invalid.contract.position')
            elif func_name in CONTRACT_FUNCS:
                return self.translate_contractfunc_call(node, ctx, impure)
            elif func_name in IO_CONTRACT_FUNCS:
                return self.translate_io_contractfunc_call(node, ctx)
            elif func_name in OBLIGATION_CONTRACT_FUNCS:
                return self.translate_obligation_contractfunc_call(node, ctx)
            elif func_name in BUILTINS:
                return self._translate_builtin_func(node, ctx)
            elif func_name == "Thread":
                return self._translate_thread_creation(node, ctx)
            elif func_name in BUILTIN_PREDICATES:
                return [], self.translate_contractfunc_call(node, ctx, impure)
        if self._is_cls_call(node, ctx):
            return self._translate_cls_call(node, ctx)
        elif isinstance(self.get_target(node, ctx), PythonIOOperation):
            return self.translate_io_operation_call(node, ctx)
        elif self._is_thread_method_call(node, 'start', ctx):
            return self._translate_thread_start(node,ctx)
        elif self._is_thread_method_call(node, 'join', ctx):
                return self._translate_thread_join(node,ctx)
        else:
            return self.translate_normal_call_node(node, ctx, impure)

    def _get_arg(self, nargs: int, keywords: List[str], index: int, kw: str) -> int:
        if nargs > index:
            return index
        if kw in keywords:
            return nargs + keywords.index(kw)
        return None

    def _translate_thread_creation(self, node: ast.Call,
                                   ctx: Context) -> StmtsAndExpr:
        """Translates the instantiation of a Thread object."""
        pos, info = self.to_position(node,ctx), self.no_info(ctx)

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

        thread_class = ctx.module.global_module.classes['Thread']
        thread_var = ctx.actual_function.create_variable('threadingVar', thread_class,
                                                         self.translator)
        thread = thread_var.ref(node, ctx)
        newstmt = self.viper.NewStmt(thread, [], pos, info)

        thread_object_type = self.type_check(thread, thread_class, pos, ctx)
        inhale_thread_type = self.viper.Inhale(thread_object_type, pos, info)

        start_pred_acc = self.viper.PredicateAccess([thread], THREAD_START_PRED,
                                                    pos, info)
        full_perm = self.viper.FullPerm(pos, info)
        start_pred = self.viper.PredicateAccessPredicate(start_pred_acc, full_perm, pos,
                                                         info)
        inhale_start_perm = self.viper.Inhale(start_pred, pos, info)

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
                                          pos,info)
        arg_check_pos = self.to_position(node, ctx, rules=rules.THREAD_CREATION_ARG_TYPE)
        check_arg_types = self.viper.Assert(arg_type_checks, arg_check_pos, info)
        inhale_args = self.viper.Inhale(arg_assumptions, pos, info)
        stmts = thread_arg_stmts + arg_stmts + [newstmt, inhale_thread_type,
                                                inhale_method, check_arg_types,
                                                inhale_args, inhale_start_perm]
        return stmts, thread

    def _translate_thread_start(self, node: ast.Call,
                                    ctx: Context):
        pos, info = self.to_position(node, ctx), self.no_info(ctx)
        assert isinstance(node.func, ast.Attribute)
        thread_stmt, thread = self.translate_expr(node.func.value, ctx)
        method_options = []
        for arg in node.args:
            target = self.get_target(arg, ctx)
            if not (isinstance(target, PythonMethod) and not target.pure and
                        not target.predicate):
                raise InvalidProgramException(node, 'invalid.thread.start')
            method_options.append(target)

        stmts = []
        # exhale mystart predicate
        start_pred_pos = self.to_position(node, ctx, rules=rules.THREAD_START_PERMISSION)
        full_perm = self.viper.FullPerm(start_pred_pos, info)
        start_pred_acc = self.viper.PredicateAccess([thread], THREAD_START_PRED, start_pred_pos,
                                                    info)
        start_pred = self.viper.PredicateAccessPredicate(start_pred_acc, full_perm,
                                                         start_pred_pos, info)
        stmts.append(self.viper.Exhale(start_pred, start_pred_pos, info))
        # exhale method in options
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
        stmts.extend(self.create_method_fork(ctx, method_options, thread, precond_pos,
                                             info, node))
        return thread_stmt + stmts, None

    def _translate_thread_join(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        pos, info = self.to_position(node,ctx), self.no_info(ctx)
        assert isinstance(node.func, ast.Attribute)
        thread_stmt, thread = self.translate_expr(node.func.value, ctx)
        stmts = thread_stmt
        joinable_pos = self.to_position(node, ctx, rules=rules.THREAD_JOIN_JOINABLE)
        joinable_func = self.viper.FuncApp(JOINABLE_FUNC, [thread],
                                           joinable_pos, info,
                                           self.viper.Bool)

        stmts.append(self.viper.Assert(joinable_func, joinable_pos, info))
        wait_level_pos = self.to_position(node, ctx, rules=rules.THREAD_JOIN_WAITLEVEL)
        thread_level = self.create_level_call(sil.RefExpr(thread))
        residue_var = sil.PermVar(ctx.actual_function.obligation_info.residue_level)
        obligation_assertion = self.create_level_below(thread_level, residue_var, ctx)
        obligation_assertion = obligation_assertion.translate(self, ctx, wait_level_pos,
                                                              info)
        stmts.append(self.viper.Assert(obligation_assertion, wait_level_pos, info))

        post_pred_acc = self.viper.PredicateAccess([thread], THREAD_POST_PRED, pos, info)
        post_perm = self.viper.CurrentPerm(post_pred_acc, pos, info)
        any_perm = self.viper.PermGtCmp(post_perm, self.viper.NoPerm(pos, info), pos, info)

        ctx.perm_factor = post_perm

        object_class = ctx.module.global_module.classes[OBJECT_TYPE]
        res_var = ctx.actual_function.create_variable('join_result', object_class,
                                                      self.translator)

        method_options = []
        for arg in node.args:
            target = self.get_target(arg, ctx)
            if not (isinstance(target, PythonMethod) and not target.pure and
                        not target.predicate):
                raise InvalidProgramException(node, 'invalid.thread.join')
            method_options.append(target)

        else_block = self.translate_block([], pos, info)
        method_id_type = self.viper.DomainType(METHOD_ID_DOMAIN, {}, [])
        actual_method = self.viper.DomainFuncApp(GET_METHOD_FUNC, [thread],
                                                 method_id_type, pos, info, THREAD_DOMAIN)

        for method in method_options:
            method_stmts = []

            # set arg aliases with types
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

            # set old values
            collector = OldExpressionCollector()
            normalizer = OldExpressionNormalizer()
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

            for post, _ in method.postcondition:
                _, post_val = self.translate_expr(post, ctx, impure=True)
                post_assertion = self.viper.And(post_assertion, post_val, pos, info)

            ctx.inlined_calls.pop()
            ctx.clear_old_expr_aliases()
            for name in method._args:
                ctx.remove_alias(name)
            ctx.remove_alias(RESULT_NAME)
            method_stmts.append(self.viper.Inhale(post_assertion, pos, info))
            then_block = self.translate_block(method_stmts, pos, info)
            this_method = self.viper.DomainFuncApp(method.threading_id, [],
                                                   method_id_type, pos, info,
                                                   METHOD_ID_DOMAIN)
            correct_method = self.viper.EqCmp(actual_method, this_method, pos, info)
            cond = self.viper.And(any_perm, correct_method, pos, info)
            stmts.append(self.viper.If(cond, then_block, else_block, pos, info))

        ctx.perm_factor = None

        post_pred = self.viper.PredicateAccessPredicate(post_pred_acc, post_perm, pos, info)
        exhale_pred = self.viper.Exhale(post_pred, pos, info)
        stmts.append(exhale_pred)

        return stmts, None

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
