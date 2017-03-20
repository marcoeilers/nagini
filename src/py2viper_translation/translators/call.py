import ast

from collections import OrderedDict
from py2viper_contracts.contracts import (
    CONTRACT_FUNCS,
    CONTRACT_WRAPPER_FUNCS
)
from py2viper_contracts.io import IO_CONTRACT_FUNCS
from py2viper_contracts.obligations import OBLIGATION_CONTRACT_FUNCS
from py2viper_translation.lib.constants import (
    BUILTINS,
    DICT_TYPE,
    END_LABEL,
    ERROR_NAME,
    PRIMITIVES,
    RANGE_TYPE,
    RESULT_NAME,
    SET_TYPE,
    STRING_TYPE,
    TUPLE_TYPE,
)
from py2viper_translation.lib.program_nodes import (
    GenericType,
    MethodType,
    PythonClass,
    PythonField,
    PythonIOOperation,
    PythonMethod,
    PythonModule,
    PythonType,
    PythonVar
)
from py2viper_translation.lib.typedefs import (
    Expr,
    Stmt,
    StmtsAndExpr,
)
from py2viper_translation.lib.util import (
    get_body_start_index,
    get_func_name,
    InvalidProgramException,
    UnsupportedException,
)
from py2viper_translation.translators.abstract import Context
from py2viper_translation.translators.common import CommonTranslator
from typing import Dict, List, Tuple, Union


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
        pos = self.to_position(node, ctx)
        object_class = ctx.module.global_module.classes['object']
        result = self.get_function_call(object_class, '__cast__',
                                        [type_arg, object_arg], [None, None],
                                        node, ctx)
        return stmt, result

    def _translate_len(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        assert len(node.args) == 1
        stmt, target = self.translate_expr(node.args[0], ctx)
        args = [target]
        arg_type = self.get_type(node.args[0], ctx)
        call = self.get_function_call(arg_type, '__len__', [target], [None],
                                      node, ctx)
        return stmt, call

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

    def _var_concrete_type_check(self, name: str, type: PythonClass, position,
                                 ctx: Context) -> 'silver.ast.DomainFuncApp':
        """
        Creates an expression checking if the var with the given name
        is of exactly the given type.
        """
        obj_var = self.viper.LocalVar(name, self.viper.Ref,
                                      self.no_position(ctx),
                                      self.no_info(ctx))
        return self.type_factory.type_check(obj_var, type, position, ctx,
                                            concrete=True)

    def inhale_field_type(self, f: PythonField, receiver: Expr,
                          ctx: Context) -> Stmt:
        """
        Creates an inhale statement that inhales type information for the
        given field.
        """
        position = self.no_position(ctx)
        info = self.no_info(ctx)
        field_acc = self.viper.FieldAccess(receiver, f.sil_field, position,
                                           info)
        check = self.type_check(field_acc, f.type, position, ctx)
        return self.viper.Inhale(check, position, info)

    def translate_constructor_call(self, target_class: PythonClass,
            node: ast.Call, args: List, arg_stmts: List,
            ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to the constructor of target_class with args, where
        node is the call node and arg_stmts are statements related to argument
        evaluation.
        """
        assert all(args), "Some args are None: {}".format(args)
        if ctx.current_function is None:
            raise UnsupportedException(node, 'Global constructor calls are not '
                                             'supported.')
        res_var = ctx.current_function.create_variable(target_class.name +
                                                       '_res',
                                                       target_class,
                                                       self.translator)
        fields = target_class.all_sil_fields
        field_type_inhales = [self.inhale_field_type(field, res_var.ref(), ctx)
                              for field in target_class.all_fields
                              if field.type.name not in PRIMITIVES]
        new = self.viper.NewStmt(res_var.ref(), fields, self.no_position(ctx),
                                 self.no_info(ctx))
        pos = self.to_position(node, ctx)
        result_has_type = self._var_concrete_type_check(res_var.name,
                                                        target_class,
                                                        pos,
                                                        ctx)
        # Inhale the type information about the newly created object
        # so that it's already present when calling __init__.
        type_inhale = self.viper.Inhale(result_has_type, pos,
                                        self.no_info(ctx))
        args = [res_var.ref()] + args
        stmts = [new, type_inhale] + field_type_inhales
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
        return arg_stmts + stmts, res_var.ref()

    def _translate_set(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        if node.args:
            raise UnsupportedException(node)
        args = []
        set_class = ctx.module.global_module.classes[SET_TYPE]
        res_var = ctx.current_function.create_variable('set',
            set_class, self.translator)
        targets = [res_var.ref()]
        constr_call = self.get_method_call(set_class, '__init__', [],
                                           [], targets, node, ctx)
        stmt = constr_call
        # Inhale the type of the newly created set (including type arguments)
        set_type = self.get_type(node, ctx)
        if (node._parent and isinstance(node._parent, ast.Assign) and
                len(node._parent.targets) == 1):
            set_type = self.get_type(node._parent.targets[0], ctx)
        position = self.to_position(node, ctx)
        stmt.append(self.viper.Inhale(self.type_check(res_var.ref(node, ctx),
                                                      set_type, position, ctx),
                                      position, self.no_info(ctx)))
        return stmt, res_var.ref()

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
        elif func_name == 'set':
            return self._translate_set(node, ctx)
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
        if ctx.current_function is None:
            if ctx.current_class is None:
                # Global variable
                raise UnsupportedException(node, 'Global method call '
                                           'not supported.')
            else:
                # Static field
                raise UnsupportedException(node, 'Static fields not supported')
        if target.type is not None:
            result_var = ctx.current_function.create_variable(
                target.name + '_res', target.type, self.translator)
            targets.append(result_var.ref())
        if target.declared_exceptions:
            error_var = self.get_error_var(node, ctx)
            targets.append(error_var)
        call = self.create_method_call_node(
            ctx, target.sil_name, args, targets, position, self.no_info(ctx),
            target_method=target, target_node=node)
        if target.declared_exceptions:
            call = call + self.create_exception_catchers(error_var,
                ctx.actual_function.try_blocks, node, ctx)
        return (arg_stmts + call,
                result_var.ref() if result_var else None)

    def _translate_function_call(self, target: PythonMethod, args: List[Expr],
                                 formal_args: List[Expr], arg_stmts: List[Stmt],
                                 position: 'silver.ast.Position', node: ast.AST,
                                 ctx: Context) -> StmtsAndExpr:
        """Translates a call to a pure method."""
        type = self.translate_type(target.type, ctx)
        call = self.viper.FuncApp(target.sil_name, args, position,
                                  self.no_info(ctx), type, formal_args)
        call_type = self.get_type(node, ctx)
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
        args = []
        arg_types = []
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

    def _wrap_var_args(self, args: List[Expr], types: List[PythonType],
                       node: ast.AST, ctx: Context) -> StmtsAndExpr:
        """
        Wraps the given arguments into a tuple to be passed to an *args param.
        """
        position = self.to_position(node, ctx)
        info = self.no_info(ctx)
        tuple_class = ctx.module.global_module.classes[TUPLE_TYPE]
        stmts = []
        func_name = '__create' + str(len(args)) + '__'
        # __createX__ must be called with the types of the arguments as
        # additional arguments.
        val_seq = self.viper.ExplicitSeq(args, position, info)
        types = [self.type_factory.translate_type_literal(t, position, ctx)
                 for t in types]
        type_seq = self.viper.ExplicitSeq(types, position, info)
        # Also add a running integer s.t. other tuples with same contents are not
        # reference-identical.
        # args = [val_seq, type_seq, self.get_fresh_int_lit(ctx)]
        args = args + types
        if args:
            args.append(self.get_fresh_int_lit(ctx))
        arg_types = [None] * len(args)
        call = self.get_function_call(tuple_class, func_name, args, arg_types,
                                      node, ctx)
        return stmts, call

    def _wrap_kw_args(self, args: Dict[str, ast.AST], node: ast.Call,
                      kw_type: PythonType, ctx: Context) -> StmtsAndExpr:
        """
        Wraps the given arguments into a dict to be passed to an **kwargs param.
        """
        res_var = ctx.current_function.create_variable('kw_args',
            ctx.module.global_module.classes[DICT_TYPE], self.translator)
        dict_class = ctx.module.global_module.classes[DICT_TYPE]
        arg_types = []
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
        old_label_aliases = ctx.label_aliases
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
        index = get_body_start_index(method.node.body)
        stmts = []

        for stmt in method.node.body[index:]:
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

    def _translate_normal_call(self, node: ast.Call,
                               ctx: Context) -> StmtsAndExpr:
        """
        Translates 'normal' function calls, i.e. function, method, constructor
        or predicate calls.
        """
        formal_args = []
        arg_stmts, args, arg_types = self._translate_call_args(node, ctx)
        name = get_func_name(node)
        position = self.to_position(node, ctx)
        target = self._get_call_target(node, ctx)
        if not target:
            # Must be a function that exists (otherwise mypy would complain)
            # we don't know, so probably some builtin we don't support yet.
            msg = 'Unsupported builtin function'
            if ctx.actual_function.method_type == MethodType.class_method:
                msg += ' or indirect call of classmethod argument'
            raise UnsupportedException(node, msg + '.')
        if isinstance(target, PythonClass):
            return self.translate_constructor_call(target, node, args,
                                                   arg_stmts, ctx)
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
            perm = self.viper.FullPerm(position, self.no_info(ctx))
            return arg_stmts, self.create_predicate_access(target_name, args,
                                                           perm, node, ctx)
        elif target.pure:
            return self._translate_function_call(target, args, formal_args,
                                                 arg_stmts, position, node, ctx)
        else:
            return self._translate_method_call(target, args, arg_stmts,
                                               position, node, ctx)

    def translate_Call(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
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
                return self.translate_contractfunc_call(node, ctx)
            elif func_name in IO_CONTRACT_FUNCS:
                return self.translate_io_contractfunc_call(node, ctx)
            elif func_name in OBLIGATION_CONTRACT_FUNCS:
                return self.translate_obligation_contractfunc_call(node, ctx)
            elif func_name in BUILTINS:
                return self._translate_builtin_func(node, ctx)
        if self._is_cls_call(node, ctx):
            return self._translate_cls_call(node, ctx)
        elif isinstance(self.get_target(node, ctx), PythonIOOperation):
            return self.translate_io_operation_call(node, ctx)
        else:
            return self._translate_normal_call(node, ctx)

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

        fields = target_class.all_sil_fields
        new = self.viper.NewStmt(res_var.ref(), fields, self.no_position(ctx),
                                 self.no_info(ctx))
        pos = self.to_position(node, ctx)
        type_stmt, dynamic_type = self.translate_expr(node.func, ctx)
        assert not type_stmt
        result_has_type = self.type_factory.dynamic_type_check(res_var.ref(),
            dynamic_type, self.to_position(node, ctx), ctx)
        # Inhale the type information about the newly created object
        # so that it's already present when calling __init__.
        type_inhale = self.viper.Inhale(result_has_type, pos,
                                        self.no_info(ctx))
        args = [res_var.ref()] + args
        stmts = [new, type_inhale]
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
