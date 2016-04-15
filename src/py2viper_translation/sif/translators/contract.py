import ast

from py2viper_translation.sif.lib.context import SIFContext
from py2viper_translation.translators.abstract import Expr, StmtsAndExpr
from py2viper_translation.translators.contract import ContractTranslator


class SIFContractTranslator(ContractTranslator):
    """
    SIF version of the ContractTranslator.
    """
    def translate_result(self, node: ast.Call, ctx: SIFContext) -> StmtsAndExpr:
        _, expr = super().translate_result(node, ctx)

        return [], expr

    def translate_acc_field(self, node: ast.Call, perm: Expr,
                            ctx: SIFContext) -> StmtsAndExpr:
        """
        Translates Acc(o.f) to Acc(o.f) && Acc(o'.f').
        """
        _, pred = super().translate_acc_field(node, perm, ctx)
        # Create aliases dict.
        all_vars = ctx.get_all_vars()
        ctx.var_aliases = {k: v.var_prime for (k, v) in all_vars}
        ctx.use_prime = True
        _, pred_prime = super().translate_acc_field(node, perm, ctx)
        ctx.var_aliases = {}
        ctx.use_prime = False

        return [], self.viper.And(pred, pred_prime, pred.pos(), pred.info())
