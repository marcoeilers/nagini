"""Common code for obligation translators."""


from py2viper_translation.lib.jvmaccess import JVM
from py2viper_translation.lib.typeinfo import TypeInfo
from py2viper_translation.lib.viper_ast import ViperAST
from py2viper_translation.translators.abstract import TranslatorConfig
from py2viper_translation.translators.common import CommonTranslator
from py2viper_translation.translators.obligation.manager import (
    ObligationManager,
)


class CommonObligationTranslator(CommonTranslator):
    """Base class for obligation translators."""

    def __init__(self, config: TranslatorConfig, jvm: JVM, source_file: str,
                 type_info: TypeInfo, viper_ast: ViperAST,
                 obligation_manager: ObligationManager) -> None:
        super().__init__(config, jvm, source_file, type_info, viper_ast)
        self._obligation_manager = obligation_manager
