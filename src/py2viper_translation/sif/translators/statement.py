import ast

from py2viper_translation.lib.util import UnsupportedException
from py2viper_translation.sif.lib.context import SIFContext
from py2viper_translation.translators.abstract import Stmt
from py2viper_translation.translators.statement import StatementTranslator
from typing import List


class SIFStatementTranslator(StatementTranslator):
    """
    Secure Information Flow version of the StatementTranslator.
    """
    def translate_stmt_Assign(self, node: ast.Assign,
                              ctx: SIFContext) -> List[Stmt]:
        if len(node.targets) != 1:
            raise UnsupportedException(node)
        if (isinstance(node.value, ast.Call) or
            isinstance(node.targets[0], ast.Subscript)):
            raise UnsupportedException(node)
        
        # First translate assignment for normal variables.
        stmts = super().translate_stmt_Assign(node, ctx)
        # Create aliases dict.
        all_vars = ctx.get_all_vars()
        ctx.var_aliases = {k: v.var_prime for (k, v) in all_vars}
        ctx.use_prime = True
        # Translate assignment for prime variables.
        stmts += super().translate_stmt_Assign(node, ctx)
        # Reset alias dict.
        ctx.var_aliases = {}
        ctx.use_prime = False

        return stmts



