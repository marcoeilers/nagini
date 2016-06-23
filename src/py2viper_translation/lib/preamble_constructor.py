"""
Classes for constructing preambles for cases when it is more convenient
than having static Silver files.
"""


from py2viper_translation.translators.abstract import Context
from py2viper_translation.lib.viper_ast import ViperAST
from typing import List, Tuple

# Just to make mypy happy.
if False:         # pylint: disable=using-constant-test
    import py2viper_translation     # pylint: disable=unused-import,ungrouped-imports
    import viper  # pylint: disable=import-error,unused-import


class IOPreambleConstructor:
    """
    Class for constructing IO preamble.

    Currently the following constructs are supported:

    +   ``token(place)``.
    """

    def __init__(self,
                 translator: 'py2viper_translation.translator.Translator',
                 viper_ast: ViperAST) -> None:
        self._translator = translator
        self._viper = viper_ast

    def construct_io_preamble(
            self, ctx: Context) -> Tuple[
                List['viper.silver.ast.Predicate'],
                List['viper.silver.ast.Function'],
                List['viper.silver.ast.Method']]:
        """
        Main method that constructs IO preamble.
        """

        position = self._translator.no_position(ctx)
        info = self._translator.no_info(ctx)

        place = self._viper.LocalVarDecl(
            'place', self._viper.Ref, position, info)
        token = self._viper.Predicate('token', [place], None, position, info)

        return [token], [], []
