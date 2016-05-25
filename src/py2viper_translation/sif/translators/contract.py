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
            raise UnsupportedException(node, "Pure functions not supported.")
        if not ctx.use_prime:
            return [], ctx.current_function.result.ref
        else:
            return [], ctx.current_function.result.var_prime.ref

    def translate_assert(self, node: ast.Call, ctx: SIFContext) -> StmtsAndExpr:
        stmts, _ = super().translate_assert(node, ctx)
        ctx.set_prime_ctx()
        stmts_p, _ = super().translate_assert(node, ctx)
        ctx.set_normal_ctx()

        return stmts + stmts_p, None

