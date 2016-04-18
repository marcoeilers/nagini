import ast

from py2viper_translation.lib.util import UnsupportedException
from py2viper_translation.sif.lib.context import SIFContext
from py2viper_translation.translators.abstract import Expr, StmtsAndExpr
from py2viper_translation.translators.contract import ContractTranslator


class SIFContractTranslator(ContractTranslator):
    """
    SIF version of the ContractTranslator.
    """
    def translate_result(self, node: ast.Call, ctx: SIFContext) -> StmtsAndExpr:
        if ctx.current_function.pure:
            raise UnsupportedException(node)
        if not ctx.use_prime:
            return [], ctx.current_function.result.ref
        else:
            return [], ctx.current_function.result.var_prime.ref
