import ast

from py2viper_contracts.contracts import CONTRACT_FUNCS
from py2viper_translation.lib.constants import (
    BOOL_TYPE,
    BUILTINS,
    DICT_TYPE,
    INT_TYPE,
    LIST_TYPE,
    OBJECT_TYPE,
    OPERATOR_FUNCTIONS,
    PRIMITIVES,
    RANGE_TYPE,
    SET_TYPE,
    STRING_TYPE,
    TUPLE_TYPE,
    UNION_TYPE,
)
from py2viper_translation.lib.program_nodes import (
    GenericType,
    PythonClass,
    PythonMethod,
    PythonModule,
    PythonNode,
    PythonType,
    PythonVar,
    PythonVarBase,
)
from py2viper_translation.lib.jvmaccess import JVM
from py2viper_translation.lib.typedefs import (
    Expr,
    Stmt,
    StmtsAndExpr,
)
from py2viper_translation.lib.typeinfo import TypeInfo
from py2viper_translation.lib.util import (
    get_func_name,
    InvalidProgramException,
    UnsupportedException,
)
from py2viper_translation.lib.viper_ast import ViperAST
from py2viper_translation.translators.abstract import (
    Context,
    TranslatorConfig,
)
from py2viper_translation.translators.common import CommonTranslator
from typing import List


class TypeTranslator(CommonTranslator):

    def __init__(self, config: TranslatorConfig, jvm: JVM, source_file: str,
                 type_info: TypeInfo, viper_ast: ViperAST) -> None:
        super().__init__(config, jvm, source_file, type_info, viper_ast)
        self.builtins = {'builtins.int': viper_ast.Int,
                         'builtins.bool': viper_ast.Bool}

    def translate_type(self, cls: PythonClass,
                       ctx: Context) -> 'silver.ast.Type':
        """
        Translates the given type to the corresponding Viper type (Int, Ref, ..)
        """
        if 'builtins.' + cls.name in self.builtins:
            return self.builtins['builtins.' + cls.name]
        elif cls.name == 'type':
            return self.type_factory.type_type()
        else:
            return self.viper.Ref

    def get_type(self, node: ast.AST, ctx: Context) -> PythonClass:
        """
        Returns the type of the expression represented by node as a PythonClass
        """
        target = self.get_target(node, ctx)
        if target:
            if isinstance(target, PythonVarBase):
                col = node.col_offset if hasattr(node, 'col_offset') else None
                key = (node.lineno, col)
                if key in target.alt_types:
                    return target.alt_types[key]
                else:
                    return target.type
            if isinstance(target, PythonMethod):
                if isinstance(node.func, ast.Attribute):
                    rec_target = self.get_target(node.func.value, ctx)
                    if not isinstance(rec_target, PythonModule):
                        rectype = self.get_type(node.func.value, ctx)
                        if target.generic_type != -1:
                            return rectype.type_args[target.generic_type]
                return target.type
            if isinstance(target, PythonClass):
                return target

        if isinstance(node, ast.Attribute):
            receiver = self.get_type(node.value, ctx)
            if receiver.name == 'type':
                receiver = receiver.type_args[0]
            rec_field = receiver.get_field(node.attr)
            if not rec_field:
                return receiver.get_static_field(node.attr)
            return rec_field.type
        elif isinstance(node, ast.Name):
            if node.id in ctx.module.global_vars:
                return ctx.module.global_vars[node.id].type
            else:
                # Var aliases should never change the type of a variable, but
                # we might still get alt_type information from them that we
                # don't get from the normal variable in case where there *is*
                # no normal variable, lambda arguments.
                var = ctx.actual_function.get_variable(node.id)
                if not var and node.id in ctx.var_aliases:
                    var = ctx.var_aliases[node.id]
                col = node.col_offset if hasattr(node, 'col_offset') else None
                key = (node.lineno, col)
                if key in var.alt_types:
                    return var.alt_types[key]
                else:
                    return var.type
        elif isinstance(node, ast.Num):
            return ctx.module.global_module.classes[INT_TYPE]
        elif isinstance(node, ast.Tuple):
            args = [self.get_type(arg, ctx) for arg in node.elts]
            return GenericType(ctx.module.global_module.classes[TUPLE_TYPE],
                               args)
        elif isinstance(node, ast.Subscript):
            value_type = self.get_type(node.value, ctx)
            if value_type.name == TUPLE_TYPE:
                if len(value_type.type_args) == 1:
                    return value_type.type_args[0]
                return value_type.type_args[node.slice.value.n]
            elif value_type.name == LIST_TYPE:
                return value_type.type_args[0]
            elif value_type.name == SET_TYPE:
                return value_type.type_args[0]
            elif value_type.name == DICT_TYPE:
                return value_type.type_args[1]
            elif value_type.name == RANGE_TYPE:
                return ctx.module.global_module.classes[INT_TYPE]
            else:
                raise UnsupportedException(node)
        elif isinstance(node, ast.Str):
            return ctx.module.global_module.classes[STRING_TYPE]
        elif isinstance(node, ast.Compare):
            return ctx.module.global_module.classes[BOOL_TYPE]
        elif isinstance(node, ast.BoolOp):
            return ctx.module.global_module.classes[BOOL_TYPE]
        elif isinstance(node, ast.List):
            if node.elts:
                el_types = [self.get_type(el, ctx) for el in node.elts]
                args = [self.common_supertype(el_types)]
            elif node._parent and isinstance(node._parent, ast.Assign):
                # Empty constructor is assigned to variable;
                # we get the type of the empty list from the type of the
                # variable it's assigned to.
                args = self.get_type(node._parent.targets[0], ctx).type_args
            else:
                args = [ctx.module.global_module.classes[OBJECT_TYPE]]
            return GenericType(ctx.module.global_module.classes[LIST_TYPE],
                               args)
        elif isinstance(node, ast.Set):
            if node.elts:
                el_types = [self.get_type(el, ctx) for el in node.elts]
                args = [self.common_supertype(el_types)]
            elif node._parent and isinstance(node._parent, ast.Assign):
                # Empty constructor is assigned to variable;
                # we get the type of the empty set from the type of the
                # variable it's assigned to.
                args = self.get_type(node._parent.targets[0], ctx).type_args
            else:
                args = [ctx.module.global_module.classes[OBJECT_TYPE]]
            return GenericType(ctx.module.global_module.classes[SET_TYPE],
                               args)
        elif isinstance(node, ast.Dict):
            if node.keys:
                key_types = [self.get_type(key, ctx) for key in node.keys]
                val_types = [self.get_type(val, ctx) for val in node.values]
                args = [self.common_supertype(key_types),
                        self.common_supertype(val_types)]
            elif node._parent and isinstance(node._parent, ast.Assign):
                # Empty constructor is assigned to variable;
                # we get the type of the empty dict from the type of the
                # variable it's assigned to.
                args = self.get_type(node._parent.targets[0], ctx).type_args
            else:
                object_class = ctx.module.global_module.classes[OBJECT_TYPE]
                args = [object_class, object_class]
            return GenericType(ctx.module.global_module.classes[DICT_TYPE],
                               args)
        elif isinstance(node, ast.IfExp):
            body_type = self.get_type(node.body, ctx)
            else_type = self.get_type(node.orelse, ctx)
            return self.pairwise_supertype(body_type, else_type)
        elif isinstance(node, ast.BinOp):
            left_type = self.get_type(node.left, ctx)
            right_type = self.get_type(node.right, ctx)
            if self.is_primitive_operation(node, left_type, right_type):
                return left_type
            else:
                operator_func = OPERATOR_FUNCTIONS[type(node.op)]
                return left_type.get_func_or_method(operator_func).type
        elif isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.Not):
                return ctx.module.global_module.classes[BOOL_TYPE]
            elif isinstance(node.op, ast.USub):
                return ctx.module.global_module.classes[INT_TYPE]
            else:
                raise UnsupportedException(node)
        elif isinstance(node, ast.NameConstant):
            if (node.value is True) or (node.value is False):
                return ctx.module.global_module.classes[BOOL_TYPE]
            elif node.value is None:
                return ctx.module.global_module.classes[OBJECT_TYPE]
            else:
                raise UnsupportedException(node)
        elif isinstance(node, ast.Call):
            if get_func_name(node) == 'super':
                if len(node.args) == 2:
                    if not self.is_valid_super_call(node, ctx):
                        raise InvalidProgramException(node,
                                                      'invalid.super.call')
                    return ctx.module.classes[node.args[0].id].superclass
                elif not node.args:
                    return ctx.current_class.superclass
                else:
                    raise InvalidProgramException(node, 'invalid.super.call')
            if get_func_name(node) == 'len':
                return ctx.module.global_module.classes[INT_TYPE]
            if isinstance(node.func, ast.Name):
                if node.func.id in CONTRACT_FUNCS:
                    if node.func.id == 'Result':
                        return ctx.actual_function.type
                    elif node.func.id == 'RaisedException':
                        assert ctx.current_contract_exception is not None
                        return ctx.current_contract_exception
                    elif node.func.id == 'Acc':
                        return ctx.module.global_module.classes[BOOL_TYPE]
                    elif node.func.id == 'Old':
                        return self.get_type(node.args[0], ctx)
                    elif node.func.id == 'Implies':
                        return ctx.module.global_module.classes[BOOL_TYPE]
                    elif node.func.id == 'Forall':
                        return ctx.module.global_module.classes[BOOL_TYPE]
                    elif node.func.id == 'Exists':
                        return ctx.module.global_module.classes[BOOL_TYPE]
                    elif node.func.id == 'Unfolding':
                        return self.get_type(node.args[1], ctx)
                    elif node.func.id == 'Previous':
                        arg_type = self.get_type(node.args[0], ctx)
                        list_class = ctx.module.global_module.classes[LIST_TYPE]
                        return GenericType(list_class, [arg_type])
                    else:
                        raise UnsupportedException(node)
                elif node.func.id in BUILTINS:
                    if node.func.id == 'isinstance':
                        return ctx.module.global_module.classes[BOOL_TYPE]
                    elif node.func.id == BOOL_TYPE:
                        return ctx.module.global_module.classes[BOOL_TYPE]
                if node.func.id in ctx.module.classes:
                    return ctx.module.global_module.classes[node.func.id]
                elif ctx.module.get_func_or_method(node.func.id) is not None:
                    target = ctx.module.get_func_or_method(node.func.id)
                    return target.type
            elif isinstance(node.func, ast.Attribute):
                rectype = self.get_type(node.func.value, ctx)
                target = rectype.get_func_or_method(node.func.attr)
                if target.generic_type != -1:
                    return rectype.type_args[target.generic_type]
                else:
                    return target.type
        else:
            raise UnsupportedException(node)

    def common_supertype(self, types: List[PythonType]) -> PythonType:
        assert types
        if len(types) == 1:
            return types[0]
        current = types[0]
        for new in types[1:]:
            current = self.pairwise_supertype(current, new)
        return current

    def pairwise_supertype(self, t1: PythonType, t2: PythonType) -> PythonType:
        if self._is_subtype(t1, t2):
            return t2
        if self._is_subtype(t2, t1):
            return t1
        if not t1.superclass:
            return None
        return self.pairwise_supertype(t2, t1.superclass)

    def _is_subtype(self, t1: PythonType, t2: PythonType) -> bool:
        if t1 == t2:
            return True
        if not t1.superclass:
            return False
        return self._is_subtype(t1.superclass, t2)

    def set_type_nargs_and_args(self, lhs: Expr, type: GenericType,
                                prefix: List[Expr], ctx: Context,
                                inhale_exhale: bool) -> Expr:
        true = self.viper.TrueLit(self.no_position(ctx), self.no_info(ctx))
        if type.name == UNION_TYPE:
            result = self.viper.FalseLit(self.no_position(ctx),
                                         self.no_info(ctx))
            for option in type.type_args:
                if option is None:
                    option = ctx.module.global_module.classes['NoneType']
                elif option.name in PRIMITIVES:
                    option = ctx.module.global_module.classes['__boxed_' +
                                                              option.name]
                check = self.type_factory.type_arg_check(lhs, option, prefix,
                                                         ctx)
                if inhale_exhale:
                    check = self.viper.InhaleExhaleExp(check, true,
                                                       self.no_position(ctx),
                                                       self.no_info(ctx))
                if isinstance(option, GenericType):
                    option_args = self.set_type_nargs_and_args(lhs, option,
                                                               prefix, ctx,
                                                               inhale_exhale)
                    check = self.viper.And(check, option_args,
                                           self.no_position(ctx),
                                           self.no_info(ctx))
                result = self.viper.Or(result, check,
                                       self.no_position(ctx),
                                       self.no_info(ctx))
            return result
        args = type.type_args
        if type.exact_length:
            nargs = len(type.type_args)
            result = self.type_factory.type_nargs_check(lhs, nargs,
                                                        prefix, ctx)
        else:
            result = true

        for i, arg in enumerate(args):
            lit = self.viper.IntLit(i, self.no_position(ctx), self.no_info(ctx))
            indices = prefix + [lit]

            if arg.name in PRIMITIVES:
                arg = ctx.module.global_module.classes['__boxed_' + arg.name]
            if arg.name == UNION_TYPE:
                check = true
            else:
                check = self.type_factory.type_arg_check(lhs, arg, indices, ctx)
            if inhale_exhale:
                check = self.viper.InhaleExhaleExp(check, true,
                                                   self.no_position(ctx),
                                                   self.no_info(ctx))
            result = self.viper.And(result, check, self.no_position(ctx),
                                    self.no_info(ctx))

            if isinstance(arg, GenericType):
                arg_nargs = self.set_type_nargs_and_args(lhs, arg, indices, ctx,
                                                         inhale_exhale)
                result = self.viper.And(result, arg_nargs,
                                        self.no_position(ctx),
                                        self.no_info(ctx))
        return result

    def type_check(self, lhs: Expr, type: PythonType,
                   position: 'silver.ast.Position',
                   ctx: Context, inhale_exhale: bool=True) -> Expr:
        """
        Returns a type check expression. This may return a simple isinstance
        for simple types, or include information about type arguments for
        generic types, or things like the lengths for tuples.
        """
        if type is None:
            none_type = ctx.module.global_module.classes['NoneType']
            return self.type_factory.type_check(lhs, none_type, position, ctx)
        elif type.name in PRIMITIVES:
            boxed = ctx.module.global_module.classes['__boxed_' + type.name]
            return self.type_factory.type_check(lhs, boxed, position, ctx)
        elif type.name == 'type':
            return self.viper.TrueLit(position, self.no_info(ctx))
        elif type.name == UNION_TYPE:
            result = self.viper.FalseLit(position, self.no_info(ctx))
            for option in type.type_args:
                option_result = self.type_check(lhs, option, position, ctx,
                                                inhale_exhale)
                result = self.viper.Or(result, option_result, position,
                                       self.no_info(ctx))
            return result
        else:
            result = self.type_factory.type_check(lhs, type, position, ctx)
            # if inhale_exhale:
            #     true = self.viper.TrueLit(position,
            #                               self.no_info(ctx))
            #     result = self.viper.InhaleExhaleExp(result, true,
            #                                         position,
            #                                         self.no_info(ctx))
            if isinstance(type, GenericType):
                args = self.set_type_nargs_and_args(lhs, type, [], ctx,
                                                    inhale_exhale)
                result = self.viper.And(result, args, self.no_position(ctx),
                                        self.no_info(ctx))
            return result
