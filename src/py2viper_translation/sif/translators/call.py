import ast

from typing import List, Tuple

from py2viper_translation.sif.lib.context import SIFContext
from py2viper_translation.translators.abstract import Expr, Stmt
from py2viper_translation.translators.call import CallTranslator


class SIFCallTranslator(CallTranslator):
    """
    SIF version of the CallTranslator.
    """
    def _translate_args(self, node: ast.Call,
                        ctx: SIFContext) -> Tuple[List[Stmt], List[Expr]]:
        pass