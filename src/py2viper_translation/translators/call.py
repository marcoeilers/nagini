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
    MethodType,
    PythonClass,
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

    def translate_isinstance(self, node: ast.Call,
                             ctx: Context) -> StmtsAndExpr:
        assert len(node.args) == 2
        target = self.get_target(node.args[1], ctx)
        assert isinstance(target, (PythonClass, PythonVar))
        stmt, obj = self.translate_expr(node.args[0], ctx)
        pos = self.to_position(node, ctx)
        if isinstance(target, PythonClass):
            check = self.type_check(obj, target, pos, ctx, inhale_exhale=False)
        else:
            check = self.type_factory.dynamic_type_check(obj, target.ref(), pos,
                                                         ctx)
        return stmt, check

    def translate_type_func(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        assert len(node.args) == 1
        stmt, obj = self.translate_expr(node.args[0], ctx)
        pos = self.to_position(node, ctx)
        result = self.type_factory.typeof(obj, ctx)
        return stmt, result

    def translate_len(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        assert len(node.args) == 1
        stmt, target = self.translate_expr(node.args[0], ctx)
        args = [target]
        arg_type = self.get_type(node.args[0], ctx)
        call = self.get_function_call(arg_type, '__len__', [target], [None],
                                      node, ctx)
        return stmt, call

    def translate_super(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
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

    def var_concrete_type_check(self, name: str, type: PythonClass, position,
                                ctx: Context) -> 'silver.ast.DomainFuncApp':
        """
        Creates an expression checking if the var with the given name
        is of exactly the given type.
        """
        obj_var = self.viper.LocalVar(name, self.viper.Ref,
                                      self.no_position(ctx),
                                      self.no_info(ctx))
        return self.type_factory.concrete_type_check(obj_var, type, position,
                                                     ctx)

    def _translate_constructor_call(self, target_class: PythonClass,
            node: ast.Call, args: List, arg_stmts: List,
            ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to the constructor of target_class with args, where
        node is the call node and arg_stmts are statements related to argument
        evaluation.
        """
        res_var = ctx.current_function.create_variable(target_class.name +
                                                       '_res',
                                                       target_class,
                                                       self.translator)
        fields = target_class.get_all_sil_fields()
        new = self.viper.NewStmt(res_var.ref(), fields, self.no_position(ctx),
                                 self.no_info(ctx))
        pos = self.to_position(node, ctx)
        result_has_type = self.var_concrete_type_check(res_var.name,
                                                       target_class,
                                                       pos,
                                                       ctx)
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

    def translate_set(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        if node.args:
            raise UnsupportedException(node)
        args = []
        set_class = ctx.module.global_module.classes[SET_TYPE]
        res_var = ctx.current_function.create_variable('set',
            set_class, self.translator)
        targets = [res_var.ref()]
        constr_call = self.get_method_call(set_class, '__init__', [],
                                           [], targets, node, ctx)
        return constr_call, res_var.ref()

    def translate_range(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        if len(node.args) != 2:
            msg = 'range() is currently only supported with two args.'
            raise UnsupportedException(node, msg)
        range_class = ctx.module.global_module.classes[RANGE_TYPE]
        start_stmt, start = self.translate_expr(node.args[0], ctx)
        end_stmt, end = self.translate_expr(node.args[1], ctx)

        length = self.viper.Sub(end, start, self.to_position(node.args[1], ctx),
                                self.no_info(ctx))
        args = [start, length]
        arg_types = [None, None]
        call = self.get_function_call(range_class, '__create__', args,
                                      arg_types, node, ctx)
        return start_stmt + end_stmt, call

    def translate_builtin_func(self, node: ast.Call,
                               ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to a builtin function like len() or isinstance()
        """
        func_name = get_func_name(node)
        if func_name == 'isinstance':
            return self.translate_isinstance(node, ctx)
        elif func_name == 'super':
            return self.translate_super(node, ctx)
        elif func_name == 'len':
            return self.translate_len(node, ctx)
        elif func_name == 'set':
            return self.translate_set(node, ctx)
        elif func_name == 'range':
            return self.translate_range(node, ctx)
        elif func_name == 'type':
            return self.translate_type_func(node, ctx)
        else:
            raise UnsupportedException(node)

    def translate_method_call(self, target: PythonMethod, args: List[Expr],
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
                raise UnsupportedException(node, "Global function call "
                                           "not supported.")
            else:
                # Static field
                raise UnsupportedException(node, "Static fields not supported")
        if target.type is not None:
            result_var = result_var = ctx.current_function.create_variable(
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

    def translate_function_call(self, target: PythonMethod, args: List[Expr],
                                formal_args: List[Expr], arg_stmts: List[Stmt],
                                position: 'silver.ast.Position', node: ast.AST,
                                ctx: Context) -> StmtsAndExpr:
        """Translates a call to a pure method."""
        type = self.translate_type(target.type, ctx)
        call = self.viper.FuncApp(target.sil_name, args, position,
                                  self.no_info(ctx), type, formal_args)
        call_type = self.get_type(node, ctx)
        if (call_type and call_type.name in PRIMITIVES and
                target.type.name not in PRIMITIVES):
            call = self.unbox_primitive(call, call_type, node, ctx)
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
                    target_class = self.get_type(node.func.value, ctx)
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
                elif isinstance(rec_target, PythonClass):
                    return False
                else:
                    return True
            else:
                return False
        elif called_func.method_type == MethodType.class_method:
            return True
        else:
            return False

    def _translate_args(self, node: ast.Call,
                        ctx: Context) -> Tuple[List[Stmt], List[Expr],
                                               List[PythonType]]:
        """
        Returns the args and types of the given call. Named args are put into
        the correct position; for *args and **kwargs, tuples and dicts are
        created and all arguments not bound to any other parameter are put in
        there.
        """
        target = self._get_call_target(node, ctx)
        if isinstance(target, PythonClass):
            constr = target.methods.get('__init__')
            target = constr

        args = []
        arg_types = []
        arg_stmts = []

        normal_args = node.args[:target.nargs] if target else node.args

        for arg in normal_args:
            arg_stmt, arg_expr = self.translate_expr(arg, ctx)
            arg_type = self.get_type(arg, ctx)
            arg_stmts += arg_stmt
            args.append(arg_expr)
            arg_types.append(arg_type)

        if not target:
            return arg_stmts, args, arg_types

        var_args = node.args[target.nargs:]

        keys = list(target.args.keys())
        if self._has_implicit_receiver_arg(node, ctx):
            keys = keys[1:]

        no_missing = len(keys) - len(args)
        args += [False] * no_missing
        arg_types += [False] * no_missing

        kw_args = OrderedDict()

        # Named args
        for kw in node.keywords:
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
                arg_types[index] = self.get_type(target.args[key].default, ctx)

        if target.var_arg:
            var_stmt, var_arg_list = self.wrap_var_args(var_args, node, ctx)
            args.append(var_arg_list)
            arg_types.append(target.var_arg.type)
            arg_stmts += var_stmt

        if target.kw_arg:
            kw_stmt, kw_arg_dict = self.wrap_kw_args(kw_args, node, ctx)
            args.append(kw_arg_dict)
            arg_types.append(target.kw_arg.type)
            arg_stmts += kw_stmt

        return arg_stmts, args, arg_types

    def wrap_var_args(self, args: List[ast.AST], node: ast.AST,
                      ctx: Context) -> StmtsAndExpr:
        """
        Wraps the given arguments into a tuple to be passed to an *args param.
        """
        tuple_class = ctx.module.global_module.classes[TUPLE_TYPE]
        stmts = []
        vals = []
        val_types = []
        for arg in args:
            arg_stmt, arg_val = self.translate_expr(arg, ctx)
            stmts += arg_stmt
            vals.append(arg_val)
            val_types.append(self.get_type(arg, ctx))
        func_name = '__create' + str(len(args)) + '__'
        call = self.get_function_call(tuple_class, func_name, vals, val_types,
                                      node, ctx)
        return stmts, call

    def wrap_kw_args(self, args: Dict[str, ast.AST], node: ast.Dict,
                     ctx: Context) -> StmtsAndExpr:
        """
        Wraps the given arguments into a dict to be passed to an **kwargs param.
        """
        res_var = ctx.current_function.create_variable('kw_args',
            ctx.module.global_module.classes[DICT_TYPE], self.translator)
        dict_class = ctx.module.global_module.classes[DICT_TYPE]
        arg_types = []
        constr_call = self.get_method_call(dict_class, '__init__', [],
                                           [], [res_var.ref()], node, ctx)
        stmt = constr_call
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

    def inline_call(self, method: PythonMethod, node: ast.Call, is_super: bool,
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
        arg_stmts, arg_vals, arg_types = self._translate_args(node, ctx)
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

    def translate_normal_call(self, node: ast.Call,
                              ctx: Context) -> StmtsAndExpr:
        """
        Translates 'normal' function calls, i.e. function, method, constructor
        or predicate calls.
        """
        formal_args = []
        arg_stmts, args, arg_types = self._translate_args(node, ctx)
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
            # This is a constructor call
            # constr_class = target
            # if isinstance(constr_class, PythonMethod):
            #     constr_class = constr_class.cls
            return self._translate_constructor_call(target, node, args,
                                                    arg_stmts, ctx)
        is_predicate = True
        if isinstance(node.func, ast.Attribute):
            receiver_target = self.get_target(node.func.value, ctx)
            print(receiver_target.name)
            if (isinstance(receiver_target, PythonClass) and
                    get_func_name(node.func.value) != 'Result'):
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
                    return self.inline_call(target, node, is_super,
                                            'static call', ctx)
            elif isinstance(receiver_target, PythonModule):
                # Normal, receiverless call to imported function
                receiver_class = None
                is_predicate = target.predicate
            elif (isinstance(node.func.value, ast.Call) and
                        get_func_name(node.func.value) == 'super'):
                    # Super call
                    return self.inline_call(target, node, True, 'static call',
                                            ctx)
            else:
                # Method called on an object
                rec_stmt, receiver = self.translate_expr(node.func.value, ctx)
                receiver_type = self.get_type(node.func.value, ctx)
                if (target.method_type == MethodType.class_method and
                        receiver_type.name != 'type'):
                    receiver = self.type_factory.typeof(receiver, ctx)
                is_predicate = target.predicate
                receiver_class = target.cls
                if target.method_type != MethodType.static_method:
                    arg_stmts = rec_stmt + arg_stmts
                    args = [receiver] + args
                    arg_types = [receiver_type] + arg_types
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
            if (type and type.name in PRIMITIVES and
                    param.type.name not in PRIMITIVES):
                actual_arg = self.box_primitive(arg, type, None, ctx)
            else:
                actual_arg = arg
            actual_args.append(actual_arg)
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
            return self.translate_function_call(target, args, formal_args,
                                                arg_stmts, position, node, ctx)
        else:
            return self.translate_method_call(target, args, arg_stmts,
                                              position, node, ctx)

    def translate_Call(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translates any kind of call. This can be a call to a contract function
        like Assert, a builtin Python function like isinstance, a
        constructor call, a 'call' to a predicate, a pure function or impure
        method call, on a receiver object or not.
        """
        if get_func_name(node) in CONTRACT_WRAPPER_FUNCS:
            raise InvalidProgramException(node, 'invalid.contract.position')
        elif get_func_name(node) in CONTRACT_FUNCS:
            return self.translate_contractfunc_call(node, ctx)
        elif get_func_name(node) in IO_CONTRACT_FUNCS:
            return self.translate_io_contractfunc_call(node, ctx)
        elif get_func_name(node) in OBLIGATION_CONTRACT_FUNCS:
            return self.translate_obligation_contractfunc_call(node, ctx)
        elif get_func_name(node) in BUILTINS:
            return self.translate_builtin_func(node, ctx)
        elif self._is_cls_call(node, ctx):
            return self.translate_cls_call(node, ctx)
        elif isinstance(self.get_target(node, ctx), PythonIOOperation):
            return self.translate_io_operation_call(node, ctx)
        else:
            return self.translate_normal_call(node, ctx)

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

    def translate_cls_call(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
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

        fields = target_class.get_all_sil_fields()
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
