import ast

from py2viper_translation.sif.lib.context import SIFContext
from py2viper_translation.sif.translators.func_triple_domain_factory import (
    FuncTripleDomainFactory as FTDF,
)
from py2viper_translation.translators.abstract import StmtsAndExpr
from py2viper_translation.translators.contract import ContractTranslator


class SIFContractTranslator(ContractTranslator):
    """
    SIF version of the ContractTranslator.
    """
    def translate_result(self, node: ast.Call, ctx: SIFContext) -> StmtsAndExpr:
        pos = self.to_position(node, ctx)
        info = self.no_info(ctx)
        if ctx.current_function.pure:
            type_ = self.config.func_triple_factory.get_type(
                ctx.current_function.type, ctx)
            result = self.viper.Result(type_, pos, info)
            if not ctx.use_prime:
                result = self.config.func_triple_factory.get_call(FTDF.GET,
                    [result], ctx.current_function.type, pos, info, ctx)
            else:
                result = self.config.func_triple_factory.get_call(
                    FTDF.GET_PRIME, [result], ctx.current_function.type, pos,
                    info, ctx)
        else:
            if not ctx.use_prime:
                result = ctx.current_function.result.ref
            else:
                result = ctx.current_function.result.var_prime.ref

        return [], result

    def translate_assert(self, node: ast.Call, ctx: SIFContext) -> StmtsAndExpr:
        stmts, _ = super().translate_assert(node, ctx)
        ctx.set_prime_ctx()
        stmts_p, _ = super().translate_assert(node, ctx)
        ctx.set_normal_ctx()

        return stmts + stmts_p, None

