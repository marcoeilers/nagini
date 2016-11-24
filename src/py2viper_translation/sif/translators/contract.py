import ast

from py2viper_translation.lib.typedefs import Expr
from py2viper_translation.lib.util import (
    InvalidProgramException,
    UnsupportedException,
)
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
                result = ctx.current_function.result.ref()
            else:
                result = ctx.current_function.result.var_prime.ref()

        return [], result

    def translate_acc_predicate(self, node: ast.Call, perm: Expr,
                                ctx: SIFContext) -> StmtsAndExpr:
        raise UnsupportedException(node, "Acc predicates not yet supported.")

    def translate_acc_field(self, node: ast.Call, perm: Expr,
                            ctx: SIFContext):
        """
        Translates a Acc(field). Needs to generate Acc(field_p) as well.
        """
        stmt, acc = super().translate_acc_field(node, perm, ctx)
        with ctx.prime_ctx():
            stmt_p, acc_p = super().translate_acc_field(node, perm, ctx)
        # Acc(field) && Acc(field_p)
        and_accs = self.viper.And(acc, acc_p, self.to_position(node, ctx),
                                  self.no_info(ctx))

        return [], and_accs

    def translate_low(self, node: ast.Call, ctx: SIFContext) -> StmtsAndExpr:
        if len(node.args) > 1:
            raise UnsupportedException(node, "Only 0 or 1 arguments are "
                                             "supported for Low().")
        pos = self.to_position(node, ctx)
        info = self.no_info(ctx)

        if ctx.use_prime:
            return [], self.viper.TrueLit(pos, info)

        not_tl = self.viper.Not(ctx.current_tl_var_expr, pos, info)
        if node.args:
            stmts, expr = self.translate_expr(node.args[0], ctx)
            with ctx.prime_ctx():
                stmts_p, expr_p = self.translate_expr(node.args[0], ctx)

            if stmts or stmts_p:
                raise InvalidProgramException(node, 'purity.violated')

            expr_cmp = self.viper.EqCmp(expr, expr_p, pos, info)
            return [], self.viper.And(not_tl, expr_cmp, pos, info)
        else:
            return [], not_tl
