from py2viper_translation.lib.constants import BOOL_TYPE
from py2viper_translation.lib.program_nodes import PythonMethod
from py2viper_translation.lib.util import InvalidProgramException
from py2viper_translation.translators.abstract import Context
from py2viper_translation.translators.common import CommonTranslator
from typing import Tuple, List


class IOOperationTranslator(CommonTranslator):

    def translate_io_operation(
            self,
            operation: PythonMethod,
            ctx: Context,
            ) -> Tuple[
                'ast.silver.Predicate',
                List['ast.silver.Function'],
                List['ast.silver.Method'],
                ]:
        """ Translates IO operation to Silver.
        """
        raise NotImplementedError()
