"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Integer typed Silver expressions."""


import ast

from typing import List, Optional, Union

from nagini_translation.lib.silver_nodes.expression import Expression
from nagini_translation.lib.silver_nodes.int_cmp_expr import (
    GtCmp,
    GeCmp,
    LtCmp,
    LeCmp,
)
from nagini_translation.lib.typedefs import (
    Expr,
    Info,
    Position,
)
from nagini_translation.lib.util import (
    join_expressions,
)


def _auto_box(value: Union['IntExpression', int]) -> 'IntExpression':
    """If ``value`` is Python ``int``, wrap it."""
    if isinstance(value, int):
        return RawIntExpression(value)
    else:
        return value


class IntExpression(Expression):   # pylint: disable=abstract-method
    """A base class for all integer expressions."""

    def get_value(self) -> Optional[int]:
        """Try to extract Python integer representing this expression.

        Otherwise, return ``None``.
        """
        return None

    def __gt__(self, other: Union['IntExpression', int]) -> 'BoolExpression':
        return GtCmp(self, _auto_box(other))

    def __ge__(self, other: Union['IntExpression', int]) -> 'BoolExpression':
        return GeCmp(self, _auto_box(other))

    def __lt__(self, other: Union['IntExpression', int]) -> 'BoolExpression':
        return LtCmp(self, _auto_box(other))

    def __le__(self, other: Union['IntExpression', int]) -> 'BoolExpression':
        return LeCmp(self, _auto_box(other))

    def __add__(self, other: Union['IntExpression', int]) -> 'IntExpression':
        return Add(self, _auto_box(other))

    def __sub__(self, other: Union['IntExpression', int]) -> 'IntExpression':
        return Sub(self, _auto_box(other))


class PythonIntExpression(IntExpression):
    """An integer expression represented by Python int expression."""

    def __init__(self, node: ast.expr) -> None:
        self._node = node

    def get_value(self) -> int:
        if isinstance(self._node, ast.Num):
            return self._node.n
        else:
            return None

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        int_class = ctx.module.global_module.classes['int']
        assert translator.get_type(self._node, ctx) is int_class
        stmt, expr = translator.translate_expr(
            self._node, ctx, target_type=translator.viper.Int)
        assert not stmt
        return expr


class RawIntExpression(IntExpression):
    """Just a raw integer."""

    def __init__(self, value: int) -> None:
        self._value = value

    def get_value(self) -> int:
        return self._value

    def __add__(self, other: Union['IntExpression', int]) -> 'IntExpression':
        if isinstance(other, int):
            return RawIntExpression(self._value + other)
        return Add(self, other)

    def __sub__(self, other: Union['IntExpression', int]) -> 'IntExpression':
        if isinstance(other, int):
            return RawIntExpression(self._value - other)
        return Sub(self, other)

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        return translator.viper.IntLit(self._value, position, info)


class Add(IntExpression):
    """Add two integers."""

    def __init__(self, left: IntExpression, right: IntExpression) -> None:
        self._left = left
        self._right = right

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        left = self._left.translate(translator, ctx, position, info)
        right = self._right.translate(translator, ctx, position, info)
        return translator.viper.Add(left, right, position, info)


class Sub(IntExpression):
    """Subtract two integers."""

    def __init__(self, left: IntExpression, right: IntExpression) -> None:
        self._left = left
        self._right = right

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        left = self._left.translate(translator, ctx, position, info)
        right = self._right.translate(translator, ctx, position, info)
        return translator.viper.Sub(left, right, position, info)


class Sum(IntExpression):
    """A sum of 0 or more elements."""

    def __init__(self, elements: List[IntExpression]) -> None:
        self._elements = elements

    def is_empty(self) -> None:
        """Check if have any elements."""
        return not self._elements

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        if not self._elements:
            return translator.viper.IntLit(0, position, info)
        else:
            elements = [
                element.translate(translator, ctx, position, info)
                for element in self._elements]
            plus_operator = (
                lambda left, right:
                translator.viper.Add(left, right, position, info))
            return join_expressions(plus_operator, elements)


class Inc(IntExpression):
    """Some expression + 1."""

    def __init__(self, value: IntExpression) -> None:
        self._value = value

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        value = self._value.translate(translator, ctx, position, info)
        return translator.viper.Add(
            value, translator.viper.IntLit(1, position, info), position,
            info)


class CondInc(IntExpression):
    """Some expression + 1 if condition holds."""

    def __init__(
            self, condition: 'BoolExpression', value: IntExpression) -> None:
        self._condition = condition
        self._value = value
        self._increased_value = value + 1

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        condition = self._condition.translate(translator, ctx, position, info)
        value = self._value.translate(translator, ctx, position, info)
        increased_value = self._increased_value.translate(
            translator, ctx, position, info)
        return translator.viper.CondExp(
            condition, increased_value, value, position, info)
