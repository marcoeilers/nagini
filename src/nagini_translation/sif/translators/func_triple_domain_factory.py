from typing import Dict, List

from nagini_translation.lib.program_nodes import PythonClass
from nagini_translation.lib.typedefs import (
    Expr,
    Info,
    Position,
    Type,
    TypeVar,
)
from nagini_translation.lib.viper_ast import ViperAST
from nagini_translation.sif.lib.context import SIFContext
from nagini_translation.sif.translators.abstract import SIFTranslatorConfig
from typing import Tuple


class FuncTripleDomainFactory:
    """
    Factory for the FuncTriple Domain.
    """
    GET = 'ft_get1'
    GET_PRIME = 'ft_get2'
    GET_TL = 'ft_get3'
    CREATE = 'ft_create'

    def __init__(self, viper: ViperAST, config: SIFTranslatorConfig):
        self.viper = viper
        self.config = config
        self.domain_name = 'FuncTriple'
        self.type_vars = [self.viper.TypeVar('T'),
                          self.viper.TypeVar('S'),
                          self.viper.TypeVar('R')]

    def _create_var_map(self, ret_type: PythonClass,
                        ctx: SIFContext) -> Dict[TypeVar, Type]:
        ret_type = self.config.type_translator.translate_type(
            ret_type, ctx)
        types = [ret_type, ret_type, self.viper.Bool]

        return dict(zip(self.type_vars, types))

    def get_type(self, ret_type: PythonClass,
                 ctx: SIFContext) -> 'silver.ast.DomainType':
        var_map = self._create_var_map(ret_type, ctx)

        return self.viper.DomainType(self.domain_name, var_map, self.type_vars)

    def get_call(
            self, name: str, args: List[Expr], ret_type: PythonClass,
            pos: Position, info: Info, ctx: SIFContext,
            var_map: Dict[TypeVar, Type] = None) -> 'silver.ast.DomainFuncApp':
        """
        Creates a DomainFuncApp for the function 'name' of the FuncTriple
        Domain.
        """
        if not var_map:
            var_map = self._create_var_map(ret_type, ctx)
        if name == self.CREATE:
            type_passed = self.get_type(ret_type, ctx)
        elif name == self.GET_TL:
            type_passed = self.viper.Bool
        else:
            type_passed = self.config.type_translator.translate_type(
                ret_type, ctx)

        return self.viper.DomainFuncApp(name, args, type_passed, pos, info,
                                        self.domain_name, type_var_map=var_map)

    def extract_results(self, func_app: Expr, ret_type: PythonClass,
                        pos: Position, info: Info,
                        ctx: SIFContext) -> Tuple['silver.ast.DomainFuncApp',
                                                  'silver.ast.DomainFuncApp',
                                                  'silver.ast.DomainFuncApp']:
        var_map = self._create_var_map(ret_type, ctx)
        func_app1 = self.get_call(
            self.GET, [func_app], ret_type, pos, info, ctx, var_map)
        func_app2 = self.get_call(
            self.GET_PRIME, [func_app], ret_type, pos, info, ctx, var_map)
        func_app3 = self.get_call(
            self.GET_TL, [func_app], None, pos, info, ctx, var_map)

        return func_app1, func_app2, func_app3

