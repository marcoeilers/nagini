"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Silver statements."""


from typing import List

from nagini_translation.lib.program_nodes import (
    PythonVar,
)
from nagini_translation.lib.silver_nodes.base import (
    Expression,
    Statement,
)
from nagini_translation.lib.typedefs import (
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


class If(Statement):
    """If statement."""

    def __init__(
            self, condition: 'BoolExpression', thn: List[Statement],
            els: List[Statement]) -> None:
        self._condition = condition
        self._then = thn
        self._else = els

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Stmt:
        condition = self._condition.translate(translator, ctx, position, info)
        then_body = translator.translate_block(
            [statement.translate(translator, ctx, position, info)
             for statement in self._then],
            position, info)
        else_body = translator.translate_block(
            [statement.translate(translator, ctx, position, info)
             for statement in self._else],
            position, info)
        return translator.viper.If(
            condition, then_body, else_body, position, info)


__all__ = (
    'Inhale',
    'Exhale',
    'Assert',
    'Assign',
    'If',
)
