import ast

from py2viper_contracts.contracts import CONTRACT_FUNCS
from py2viper_translation.lib.constants import BUILTINS, PRIMITIVES
from py2viper_translation.lib.program_nodes import (
    GenericType,
    PythonClass,
    PythonType,
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
    is_two_arg_super_call,
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
        else:
            return self.viper.Ref

    def get_type(self, node: ast.AST, ctx: Context) -> PythonClass:
        """
        Returns the type of the expression represented by node as a PythonClass
        """
        if isinstance(node, ast.Attribute):
            receiver = self.get_type(node.value, ctx)
            return receiver.get_field(node.attr).type
        elif isinstance(node, ast.Name):
            if node.id in ctx.program.global_vars:
                return ctx.program.global_vars[node.id].type
            else:
                var = ctx.actual_function.get_variable(node.id)
                if node.lineno in var.alt_types:
                    return var.alt_types[node.lineno]
                else:
                    return var.type
        elif isinstance(node, ast.Num):
            return ctx.program.classes['int']
        elif isinstance(node, ast.Tuple):
            args = [self.get_type(arg, ctx) for arg in node.elts]
            type = GenericType('Tuple', ctx.program, args)
            return type
        elif isinstance(node, ast.Subscript):
            value_type = self.get_type(node.value, ctx)
            if value_type.name == 'Tuple':
                return value_type.type_args[node.slice.value.n]
            elif value_type.name == 'list':
                return value_type.type_args[0]
            elif value_type.name == 'set':
                return value_type.type_args[0]
            elif value_type.name == 'dict':
                return value_type.type_args[1]
            else:
                raise UnsupportedException(node)
        elif isinstance(node, ast.Str):
            return ctx.program.classes['str']
        elif isinstance(node, ast.Compare):
            return ctx.program.classes['bool']
        elif isinstance(node, ast.BoolOp):
            return ctx.program.classes['bool']
        elif isinstance(node, ast.List):
            if node.elts:
                el_types = [self.get_type(el, ctx) for el in node.elts]
                args = [self.common_supertype(el_types)]
            elif node._parent and isinstance(node._parent, ast.Assign):
                # oh god this is terrible
                args = self.get_type(node._parent.targets[0], ctx).type_args
            else:
                args = [ctx.program.classes['object']]
            type = GenericType('list', ctx.program, args)
            return type
        elif isinstance(node, ast.Set):
            if node.elts:
                el_types = [self.get_type(el, ctx) for el in node.elts]
                args = [self.common_supertype(el_types)]
            elif node._parent and isinstance(node._parent, ast.Assign):
                # oh god this is terrible
                args = self.get_type(node._parent.targets[0], ctx).type_args
            else:
                args = [ctx.program.classes['object']]
            type = GenericType('set', ctx.program, args)
            return type
        elif isinstance(node, ast.Dict):
            if node.keys:
                key_types = [self.get_type(key, ctx) for key in node.keys]
                val_types = [self.get_type(val, ctx) for val in node.values]
                args = [self.common_supertype(key_types),
                        self.common_supertype(val_types)]
            elif node._parent and isinstance(node._parent, ast.Assign):
                args = self.get_type(node._parent.targets[0], ctx).type_args
            else:
                object_class = ctx.program.classes['object']
                args = [object_class, object_class]
            type = GenericType('dict', ctx.program, args)
            return type
        elif isinstance(node, ast.IfExp):
            body_type = self.get_type(node.body, ctx)
            else_type = self.get_type(node.orelse, ctx)
            return self.pairwise_supertype(body_type, else_type)
        elif isinstance(node, ast.BinOp):
            return self.get_type(node.left, ctx)
        elif isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.Not):
                return ctx.program.classes['bool']
            elif isinstance(node.op, ast.USub):
                return ctx.program.classes['int']
            else:
                raise UnsupportedException(node)
        elif isinstance(node, ast.NameConstant):
            if (node.value is True) or (node.value is False):
                return ctx.program.classes['bool']
            elif node.value is None:
                return ctx.program.classes['object']
            else:
                raise UnsupportedException(node)
        elif isinstance(node, ast.Call):
            if get_func_name(node) == 'super':
                if len(node.args) == 2:
                    if not is_two_arg_super_call(node, ctx):
                        raise InvalidProgramException(node,
                                                      'invalid.super.call')
                    return ctx.program.classes[node.args[0].id].superclass
                elif not node.args:
                    return ctx.current_class.superclass
                else:
                    raise InvalidProgramException(node, 'invalid.super.call')
            if get_func_name(node) == 'len':
                return ctx.program.classes['int']
            if isinstance(node.func, ast.Name):
                if node.func.id in CONTRACT_FUNCS:
                    if node.func.id == 'Result':
                        return ctx.actual_function.type
                    elif node.func.id == 'Acc':
                        return ctx.program.classes['bool']
                    elif node.func.id == 'Old':
                        return self.get_type(node.args[0], ctx)
                    elif node.func.id == 'Implies':
                        return ctx.program.classes['bool']
                    elif node.func.id == 'Forall':
                        return ctx.program.classes['bool']
                    elif node.func.id == 'Exists':
                        return ctx.program.classes['bool']
                    elif node.func.id == 'Unfolding':
                        return self.get_type(node.args[1], ctx)
                    else:
                        raise UnsupportedException(node)
                elif node.func.id in BUILTINS:
                    if node.func.id == 'isinstance':
                        return ctx.program.classes['bool']
                    elif node.func.id == 'bool':
                        return ctx.program.classes['bool']
                if node.func.id in ctx.program.classes:
                    return ctx.program.classes[node.func.id]
                elif ctx.program.get_func_or_method(node.func.id) is not None:
                    return ctx.program.get_func_or_method(node.func.id).type
            elif isinstance(node.func, ast.Attribute):
                rectype = self.get_type(node.func.value, ctx)
                return rectype.get_func_or_method(node.func.attr).type
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

    def type_check(self, lhs: Expr, type: PythonType,
                   ctx: Context) -> Expr:
        """
        Returns a type check expression. This may return a simple isinstance
        for simple types, or include information about type arguments for
        generic types, or things like the lengts for tuples.
        """
        if type.name in PRIMITIVES:
            # TODO: do we need some boxed integer type?
            return self.viper.TrueLit(self.no_position(ctx), self.no_info(ctx))
        result = self.type_factory.type_check(lhs, type, ctx)
        if type.name == 'Tuple':
            # length
            length = self.viper.IntLit(len(type.type_args),
                                       self.no_position(ctx), self.no_info(ctx))
            len_call = self.get_function_call(type, '__len__', [lhs], [None],
                                              None, ctx)
            eq = self.viper.EqCmp(len_call, length, self.no_position(ctx),
                                  self.no_info(ctx))
            result = self.viper.And(result, eq, self.no_position(ctx),
                                    self.no_info(ctx))
            # types of contents
            for index in range(len(type.type_args)):
                # typeof getitem lessorequal type
                item = type.type_args[index]
                index_lit = self.viper.IntLit(index, self.no_position(ctx),
                                              self.no_info(ctx))
                args = [lhs, index_lit]
                arg_types = [None, None]
                item_call = self.get_function_call(type, '__getitem__', args,
                                                   arg_types, None, ctx)
                type_check = self.type_check(item_call, item, ctx)
                result = result = self.viper.And(result, type_check,
                                                 self.no_position(ctx),
                                                 self.no_info(ctx))
        return result
