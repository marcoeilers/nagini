import ast

from collections import OrderedDict
from nagini_contracts.contracts import (
    CONTRACT_FUNCS,
    CONTRACT_WRAPPER_FUNCS
)
from nagini_contracts.io import IO_CONTRACT_FUNCS
from nagini_contracts.obligations import OBLIGATION_CONTRACT_FUNCS
from nagini_translation.lib.silver_nodes.types import BoolType
from nagini_translation.lib.constants import (
    BUILTINS,
    DICT_TYPE,
    END_LABEL,
    ERROR_NAME,
    PRIMITIVES,
    PRIMITIVE_BOOL_TYPE,
    PRIMITIVE_INT_TYPE,
    RANGE_TYPE,
    RESULT_NAME,
    SET_TYPE,
    STRING_TYPE,
    TUPLE_TYPE,
    THREADING)
from nagini_translation.lib.program_nodes import (
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
from nagini_translation.lib.typedefs import (
    Expr,
    Stmt,
    StmtsAndExpr,
)
from nagini_translation.lib.util import (
    get_body_indices,
    get_func_name,
    InvalidProgramException,
    UnsupportedException,
)
from nagini_translation.translators.abstract import Context
from nagini_translation.translators.common import CommonTranslator
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

    def _translate_str(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        assert len(node.args) == 1
        stmt, target = self.translate_expr(node.args[0], ctx)
        args = [target]
        arg_type = self.get_type(node.args[0], ctx)
        call = self.get_function_call(arg_type, '__str__', [target], [None],
                                      node, ctx)
        return stmt, call

    def _translate_bool(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        assert len(node.args) == 1
        stmt, target = self.translate_expr(node.args[0], ctx)
        args = [target]
        arg_type = self.get_type(node.args[0], ctx)
        call = self.get_function_call(arg_type, '__bool__', [target], [None],
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
        result_type = self.get_type(node, ctx)
        pos = self.to_position(node, ctx)

        # Temporarily bind the type variables of the constructed class to
        # the concrete type arguments.
        old_bound_type_vars = ctx.bound_type_vars
        ctx.bound_type_vars = old_bound_type_vars.copy()
        current_type = result_type
        while current_type:
            if isinstance(current_type, GenericType):
                vars_args = zip(current_type.cls.type_vars.items(),
                                current_type.type_args)
                for (name, var), arg in vars_args:
                    literal = self.type_factory.translate_type_literal(arg, pos,
                                                                       ctx)
                    key = (var.target_type.name, name)
                    ctx.bound_type_vars[key] = literal
            current_type = current_type.superclass

        fields = list(target_class.all_fields)
        may_set_inhales = [self.viper.Inhale(ms, pos, self.no_info(ctx))
                           for ms in self.get_may_set_predicates(fields, ctx)]

        ctx.bound_type_vars = old_bound_type_vars
        new = self.viper.NewStmt(res_var.ref(), [], self.no_position(ctx),
                                 self.no_info(ctx))

        result_has_type = self.type_factory.type_check(res_var.ref(), result_type, pos,
                                                       ctx, concrete=True)

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
        elif func_name == 'str':
            return self._translate_str(node, ctx)
        elif func_name == 'bool':
            return self._translate_bool(node, ctx)
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

    def translate_normal_call_node(self, node: ast.Call, ctx: Context,
                                   impure=False) -> StmtsAndExpr:
        """
        Translates a call node which refers to a 'normal' function, method or predicate.
        """
        arg_stmts, args, arg_types = self._translate_call_args(node, ctx)
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
                return self._translate_thread_creation(node,ctx)
        if self._is_cls_call(node, ctx):
            return self._translate_cls_call(node, ctx)
        elif isinstance(self.get_target(node, ctx), PythonIOOperation):
            return self.translate_io_operation_call(node, ctx)
        elif (isinstance(node.func,ast.Attribute) and self.get_type(node.func.value,ctx).name == "Thread"
            and node.func.attr == "start") :
            return self._translate_thread_start(node,ctx)
        elif (isinstance(node.func,ast.Attribute) and self.get_type(node.func.value,ctx).name == "Thread"
            and node.func.attr == "join"):
                return self._translate_thread_join(node,ctx)


        else:
            return self.translate_normal_call_node(node, ctx, impure)

    def _translate_thread_creation(self, node: ast.Call,
                                       ctx: Context) -> StmtsAndExpr:
        """Translates the instantiation of a Thread object."""
        pos,infos = self.to_position(node,ctx),self.no_info(ctx)
        assert len(node.args) == 2
        target = self.get_target(node.args[0], ctx)
        assert isinstance(target,PythonMethod)
        meth_args = node.args[1].elts
        thr_var = ctx.actual_function.create_variable("threadingVar",
                                                       ctx.module.global_module.classes["Thread"],
                                                       self.translator)
        newstmt = self.viper.NewStmt(thr_var.ref(),
                                     [self.viper.Field("state", self.viper.DomainType("State", {}, []),
                                                          pos, infos)],
                                     pos, infos)
        #This should be t := new(state)
        createdstmt = self.viper.FieldAssign(
            self.viper.FieldAccess(thr_var.ref(),
                                   self.viper.Field("state",self.viper.DomainType("State",{},[]),pos,infos),pos,infos),
                                                 self.viper.DomainFuncApp("CREATED", [],
                                                                           self.viper.DomainType("State",{},[]),
                                                                           pos,infos,
                                                                          "State"),
                                                 pos, infos)
        #This should be t.state := CREATED()
        my_args = []
        assign_stmts = []
        for i in meth_args:
            stmts,expr = self.translate_expr(i,ctx,self.viper.Ref)
            my_args.append(expr)
            assign_stmts.extend(stmts)
        argseq = self.viper.ExplicitSeq(my_args,pos,infos)
        inhalestmt = self.viper.Inhale(
            self.viper.And(self.viper.EqCmp(
                self.viper.DomainFuncApp('getMethod',[thr_var.ref()],self.viper.DomainType("ThreadingID",{},[]),
                                         pos,infos,"Thread"),
                self.viper.DomainFuncApp(target.threading_id,[],self.viper.DomainType("ThreadingID",{},[]),pos,infos,
                                         "ThreadingID"),pos,infos),
                (self.viper.EqCmp(self.viper.DomainFuncApp('getArgs', [thr_var.ref()],
                                                           self.viper.SeqType(self.viper.Ref),pos,infos,"Thread"),
                                  argseq,pos,infos)),pos,infos),pos,infos)

        """This is where we affect its MethodID and Arguments to the thread object"""
        return [newstmt, createdstmt] + assign_stmts + [inhalestmt], thr_var.ref()

    def _olds_collector(self, expr_list, ctx):
        return [] #TODO : DFS every expr in expr_list and return the list of all the exprs in an old.
    def _translate_thread_start(self, node: ast.Call,
                                    ctx: Context):
        pos, info = self.to_position(node, ctx), self.no_info(ctx)
        assert isinstance(node.func, ast.Attribute)
        my_thr = self.get_target(node.func.value, ctx)
        my_methods = []
        for i in range(0, len(node.args)):
            my_methods.append(self.get_target(node.args[i], ctx))
        to_stock_list = self._olds_collector(my_methods,ctx)
        ref_list = []
        decl_list = []
        for exp in to_stock_list:
            ref_list.append(self.to_ref(exp,ctx))
        if ref_list :
            oldsinhale = self.viper.Inhale(
                self.viper.EqCmp(self.viper.DomainFuncApp(
                    "getOlds",[my_thr.ref()],self.viper.SeqType(self.viper.Ref),pos,info,"Thread"),
                    self.viper.ExplicitSeq(ref_list,pos,info),pos,info),pos,info)
        else :
            oldsinhale = self.viper.Inhale(
                self.viper.EqCmp(self.viper.DomainFuncApp(
                    "getOlds", [my_thr.ref()], self.viper.SeqType(self.viper.Ref), pos, info, "Thread"),
                    self.viper.EmptySeq(self.viper.Ref,pos, info), pos, info), pos, info)
        precond_to_exhale = self.viper.TrueLit(pos,info)
        check_methods = self.viper.FalseLit(pos,info)
        precond_renaming_stmt = []
        for m in my_methods :
            for index,param in enumerate(m._args):
                my_temp_var = ctx.actual_function.create_variable(
                    param+"_temp",m._args[param].type,self.translator,False)
                decl_list.append(my_temp_var.decl)
                precond_renaming_stmt.append(
                    self.viper.LocalVarAssign(
                        my_temp_var.ref(),
                        self.viper.DomainFuncApp("getArg",[my_thr.ref(),self.viper.IntLit(index,pos,info)],
                                                 self.viper.Ref,pos,info,"Thread"),pos,info))
                ctx.set_alias(param,my_temp_var,None)
            renamed_precond = self.viper.TrueLit(pos,info)
            for i in range(0,len(m.precondition)):
                stmt,expr = self.translate_expr(m.precondition[i][0],ctx,self.viper.Bool,True)
                renamed_precond = self.viper.And(renamed_precond,expr,pos,info)
            precond_to_exhale = self.viper.And(
                precond_to_exhale,
                self.viper.Implies(
                    self.viper.EqCmp(
                        self.viper.DomainFuncApp("getMethod",[my_thr.ref()],
                                                 self.viper.DomainType("ThreadingID",{},[]),pos,info,"Thread"),
                        self.viper.DomainFuncApp(m.threading_id,[],self.viper.DomainType("ThreadingID",{},[]),pos,info,
                                                 "ThreadingID"),pos,info),
                    renamed_precond,pos,info),pos,info)
            for index,param in enumerate(m._args):
                ctx.remove_alias(param)
            check_methods = self.viper.Or(
                check_methods,
                self.viper.EqCmp(
                    self.viper.DomainFuncApp("getMethod",[my_thr.ref()],
                                             self.viper.DomainType("ThreadingID",{},[]),pos,info,"Thread"),
                    self.viper.DomainFuncApp(m.threading_id,[],self.viper.DomainType("ThreadingID",{},[]),pos,info,
                                             "ThreadingID"),pos,info),pos,info)
        precond_exhaled = self.viper.Exhale(precond_to_exhale,pos,info)
        check_methods = self.viper.Assert(check_methods,pos,info)
        check_thr_created = self.viper.Assert(
            self.viper.EqCmp(self.viper.FieldAccess(my_thr.ref(),
                                                    self.viper.Field("state",self.viper.DomainType("State",{},[]),pos,
                                                                     info),
                                                    pos,info),
                             self.viper.DomainFuncApp("CREATED",[],self.viper.DomainType("State",{},[]),
                                                      pos,info,"State"),pos,info),pos,info)
        make_thr_started = self.viper.FieldAssign(
            self.viper.FieldAccess(my_thr.ref(),self.viper.Field("state",self.viper.DomainType("State",{},[]),pos,info),
                                   pos,info),
            self.viper.DomainFuncApp("STARTED",[],self.viper.DomainType("State",{},[]),pos,info,"State"),pos,info)
        return [self.viper.Seqn(precond_renaming_stmt+
                                [oldsinhale,precond_exhaled,check_methods,check_thr_created,make_thr_started],
                                pos,info,decl_list)],None


    def _translate_thread_join(self, node: ast.Call,
                                   ctx: Context):
        pos,info = self.to_position(node,ctx),self.no_info(ctx)
        assert isinstance(node.func, ast.Attribute)
        my_thr = self.get_target(node.func.value, ctx)
        my_bool = ctx.actual_function.create_variable("b",ctx.module.global_module.classes[PRIMITIVE_BOOL_TYPE],self.translator)

        #Is "Bool" ok ?
        myexpr = self.viper.TrueLit(self.to_position(node, ctx), self.no_info(ctx))
        postcond_renaming_stmt_list = []
        decl_list = []
        for i in range(0, len(node.args)):
            method = self.get_target(node.args[i],ctx)
            for index,param in enumerate(method._args):
                my_temp_var = ctx.actual_function.create_variable(
                    param+"_temp",method._args[param].type,self.translator,False)
                decl_list.append(my_temp_var.decl)
                postcond_renaming_stmt_list.append(
                    self.viper.LocalVarAssign(my_temp_var.ref(),
                                              self.viper.DomainFuncApp("getArg", [my_thr.ref(),
                                                                                  self.viper.IntLit(index, pos, info)],
                                                                       self.viper.Ref,pos,info,"Thread"),pos,info))
                ctx.set_alias(param,my_temp_var,None)
            mypostcond = self.viper.TrueLit(pos,info)
            for j in reversed(range(0, len(method.postcondition))):
                stsms,expr = self.translate_expr(method.postcondition[j][0],ctx,self.viper.Bool,True)
                mypostcond = self.viper.And(mypostcond,expr,pos,info)
                myexpr = self.viper.And(
                    myexpr,
                    self.viper.Implies(self.viper.EqCmp(
                        self.viper.DomainFuncApp('getMethod',
                                                 [my_thr.ref()],self.viper.DomainType("ThreadingID",{},[])
                                             ,pos,info,"Thread"),
                        self.viper.DomainFuncApp(
                            self.get_target(node.args[i],ctx).threading_id,[],self.viper.DomainType("ThreadingID",{},[]),
                            pos,info,"ThreadingID"),pos,info),
                        mypostcond,pos,info),pos,info)

            for index,param in enumerate(method._args):
                ctx.remove_alias(param)
        joiningstmt = self.viper.MethodCall("Thread_joining",[my_thr.ref()],
                                                                      [my_bool.ref()],pos,info)
        inhalingstmt = self.viper.If(
            my_bool.ref(),
            self.viper.Inhale(
                self.viper.Implies(self.viper.EqCmp(
                    self.viper.FieldAccess(my_thr.ref(),
                                           self.viper.Field("state",self.viper.DomainType("State",{},[]),pos,info),
                                           pos,info),
                    self.viper.DomainFuncApp("JOINED",[],self.viper.DomainType("State",{},[]),pos,info,"State"),
                    pos,info),
                    myexpr,pos,info),pos,info),self.viper.Seqn([],pos,info),pos,info)
        return [self.viper.Seqn(postcond_renaming_stmt_list+[joiningstmt,inhalingstmt],pos,info,decl_list)],None



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
        may_set_inhales = [self.viper.Inhale(ms, pos, self.no_info(ctx))
                           for ms in self.get_may_set_predicates(fields, ctx)]
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
