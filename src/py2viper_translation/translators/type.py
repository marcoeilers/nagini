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
    PRIMITIVE_INT_TYPE,
    PRIMITIVE_PREFIX,
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
    PythonIOOperation,
    PythonMethod,
    PythonModule,
    PythonNode,
    PythonType,
    PythonVar,
    PythonVarBase,
)
from py2viper_translation.lib.jvmaccess import JVM
from py2viper_translation.lib.resolver import get_type as do_get_type
from py2viper_translation.lib.typedefs import (
    Expr,
    Position,
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
from typing import List, Optional


class TypeTranslator(CommonTranslator):

    def __init__(self, config: TranslatorConfig, jvm: JVM, source_file: str,
                 type_info: TypeInfo, viper_ast: ViperAST) -> None:
        super().__init__(config, jvm, source_file, type_info, viper_ast)
        self.builtins = {'builtins.int': viper_ast.Int,
                         'builtins.bool': viper_ast.Bool,
                         'builtins.Sequence': viper_ast.SeqType(viper_ast.Ref)}

    def translate_type(self, cls: PythonClass,
                       ctx: Context) -> 'silver.ast.Type':
        """
        Translates the given type to the corresponding Viper type (Int, Ref, ..)
        """
        if cls.name in PRIMITIVES:
            cls = cls.try_box()
            return self.builtins['builtins.' + cls.name]
        elif cls.name == 'type':
            return self.type_factory.type_type()
        else:
            return self.viper.Ref

    def get_type(self, node: ast.AST, ctx: Context) -> Optional[PythonType]:
        """
        Returns the type of the expression represented by node as a PythonType,
        or None if the type is void.
        """
        container = ctx.actual_function if ctx.actual_function else ctx.module
        containers = [ctx]
        if isinstance(container, (PythonMethod, PythonIOOperation)):
            containers.append(container)
            containers.extend(container.get_module().get_included_modules())
        else:
            # Assume module
            containers.extend(container.get_included_modules())
        result = do_get_type(node, containers, container).try_box()
        return result

    def type_check(self, lhs: Expr, type: PythonType,
                   position: 'silver.ast.Position',
                   ctx: Context, inhale_exhale: bool=True) -> Expr:
        """
        Returns a type check expression. This may return a simple isinstance
        for simple types, or include information about type arguments for
        generic types, or things like the lengths for tuples.
        """
        inhale_exhale = False
        if type is None:
            none_type = ctx.module.global_module.classes['NoneType']
            return self.type_factory.type_check(lhs, none_type, position, ctx)
        elif type.name == 'type':
            return self.viper.TrueLit(position, self.no_info(ctx))
        # elif type.name == UNION_TYPE:
        #     # Union type should not directly show up on Silver level, instead
        #     # say the type is either type option 1 or type option 2 etc.
        #     result = self.viper.FalseLit(position, self.no_info(ctx))
        #     for type_option in type.type_args:
        #         option_result = self.type_check(lhs, type_option, position, ctx,
        #                                         inhale_exhale)
        #         result = self.viper.Or(result, option_result, position,
        #                                self.no_info(ctx))
        #     return result
        else:
            result = self.type_factory.type_check(lhs, type, position, ctx)
            # if isinstance(type, GenericType):
            #     # Add information about type arguments.
            #     args = self.set_type_nargs_and_args(lhs, type, [], position,
            #                                         ctx, inhale_exhale)
            #     result = self.viper.And(result, args, position,
            #                             self.no_info(ctx))
            return result
