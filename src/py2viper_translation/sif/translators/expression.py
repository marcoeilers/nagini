import ast

from py2viper_translation.sif.lib.context import SIFContext
from py2viper_translation.sif.lib.program_nodes import SIFPythonField
from py2viper_translation.translators.abstract import StmtsAndExpr
from py2viper_translation.translators.expression import ExpressionTranslator
from typing import cast


class SIFExpressionTranslator(ExpressionTranslator):
    """
    SIF version of the ExpressionTranslator.
    """
    def translate_Attribute(self, node: ast.Attribute,
                            ctx: SIFContext) -> StmtsAndExpr:
        stmt, receiver = self.translate_expr(node.value, ctx)
        field = cast(SIFPythonField, self._lookup_field(node, ctx))
        if ctx.use_prime:
            field = field.field_prime
        return (stmt, self.viper.FieldAccess(receiver, field.sil_field,
                                             self.to_position(node, ctx),
                                             self.no_info(ctx)))
