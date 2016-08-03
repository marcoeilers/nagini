"""Utility functions."""


from py2viper_translation.lib.context import Context
from py2viper_translation.lib.typedefs import (
    Predicate,
)
from py2viper_translation.lib.program_nodes import PythonMethod
from py2viper_translation.translators.common import CommonTranslator


def create_obligation_predicate(
        name: str, translator: CommonTranslator) -> Predicate:
    """Create a predicate that represents obligation."""
    viper = translator.viper
    position = viper.NoPosition
    info = viper.NoInfo
    var = viper.LocalVarDecl('r', viper.Ref, position, info)
    predicate = viper.Predicate(name, [var], None, position, info)
    return predicate


def find_method_by_sil_name(ctx: Context, sil_name: str) -> PythonMethod:
    """Find Python method based on its Silver name."""
    for method in ctx.program.methods.values():
        if method.sil_name == sil_name:
            return method
    for cls in ctx.program.classes.values():
        for method in cls.methods.values():
            if method.sil_name == sil_name:
                return method
    return None
