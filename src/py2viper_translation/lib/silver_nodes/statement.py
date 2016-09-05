"""Silver statements."""


from py2viper_translation.lib.program_nodes import (
    PythonVar,
)
from py2viper_translation.lib.silver_nodes.base import (
    Expression,
    Statement,
)
from py2viper_translation.lib.typedefs import (
    Info,
    Position,
    Stmt,
)


class Inhale(Statement):
    """Inhale statement."""

    def __init__(self, value: Expression) -> None:
        self._value = value

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Stmt:
        value = self._value.translate(translator, ctx, position, info)
        return translator.viper.Inhale(value, position, info)


class Exhale(Statement):
    """Exhale statement."""

    def __init__(self, value: Expression) -> None:
        self._value = value

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Stmt:
        value = self._value.translate(translator, ctx, position, info)
        return translator.viper.Exhale(value, position, info)


class Assert(Statement):
    """Assert statement."""

    def __init__(self, value: Expression) -> None:
        self._value = value

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Stmt:
        value = self._value.translate(translator, ctx, position, info)
        return translator.viper.Assert(value, position, info)


class Assign(Statement):
    """Assign statement."""

    def __init__(self, var: PythonVar, value: Expression) -> None:
        self._var = var
        self._value = value

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Stmt:
        value = self._value.translate(translator, ctx, position, info)
        return translator.viper.LocalVarAssign(
            self._var.ref(), value, position, info)


__all__ = (
    'Inhale',
    'Exhale',
    'Assert',
    'Assign',
)
