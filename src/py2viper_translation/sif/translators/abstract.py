from py2viper_translation.translators.abstract import TranslatorConfig


class SIFTranslatorConfig(TranslatorConfig):
    """
    SIF version of the TranslatorConfig.
    """
    def __init__(self, translator: 'Translator'):
        super().__init__(translator)
        self.func_triple_factory = None
