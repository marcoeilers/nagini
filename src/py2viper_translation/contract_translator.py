import ast

from py2viper_contracts.contracts import CONTRACT_WRAPPER_FUNCS
from py2viper_translation.abstract_translator import (
    CommonTranslator,
    TranslatorConfig,
    Expr,
    StmtAndExpr
)
from py2viper_translation.analyzer import PythonClass, PythonMethod, PythonVar
from py2viper_translation.util import get_func_name
from typing import List, Tuple, Optional, Union, Dict

class ContractTranslator(CommonTranslator):

    def translate_contract(self, node: ast.AST, ctx) -> Expr:
        """
        Generic visitor function for translating contracts (i.e. calls to
        contract functions)
        """
        method = 'translate_contract_' + node.__class__.__name__
        visitor = getattr(self, method, self.translate_generic)
        return visitor(node, ctx)

    def translate_contract_Call(self,
                                node: ast.Call, ctx) -> Expr:
        if get_func_name(node) in CONTRACT_WRAPPER_FUNCS:
            stmt, res = self.translate_expr(node.args[0], ctx)
            if stmt:
                raise InvalidProgramException(node, 'purity.violated')
            return res
        else:
            raise UnsupportedException(node)

    def translate_contract_Expr(self,
                                node: ast.Expr, ctx) -> Expr:
        if isinstance(node.value, ast.Call):
            return self.translate_contract(node.value, ctx)
        else:
            raise UnsupportedException(node)