"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Comparisons of permission typed Silver expressions."""


from nagini_translation.lib.silver_nodes.bool_expr import BoolExpression
from nagini_translation.lib.typedefs import (
    Expr,
    Info,
    Position,
)


class PermComparison(BoolExpression):   # pylint: disable=abstract-method
    """A base class for all permission comparison operators."""


class PermGtCmp(PermComparison):
    """Greater than permission comparison."""

    def __init__(self, left: 'PermExpression', right: 'PermExpression') -> None:
        self._left = left
        self._right = right

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        left = self._left.translate(translator, ctx, position, info)
        right = self._right.translate(translator, ctx, position, info)
        return translator.viper.PermGtCmp(
            left, right, position, info)


class PermGeCmp(PermComparison):
    """Greater equal permission comparison."""

    def __init__(self, left: 'PermExpression', right: 'PermExpression') -> None:
        self._left = left
        self._right = right

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        left = self._left.translate(translator, ctx, position, info)
        right = self._right.translate(translator, ctx, position, info)
        return translator.viper.PermGeCmp(
            left, right, position, info)


class PermLtCmp(PermComparison):
    """Less than permission comparison."""

    def __init__(self, left: 'PermExpression', right: 'PermExpression') -> None:
        self._left = left
        self._right = right

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        left = self._left.translate(translator, ctx, position, info)
        right = self._right.translate(translator, ctx, position, info)
        return translator.viper.PermLtCmp(
            left, right, position, info)


class PermLeCmp(PermComparison):
    """Less equal permission comparison."""

    def __init__(self, left: 'PermExpression', right: 'PermExpression') -> None:
        self._left = left
        self._right = right

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        left = self._left.translate(translator, ctx, position, info)
        right = self._right.translate(translator, ctx, position, info)
        return translator.viper.PermLeCmp(
            left, right, position, info)
