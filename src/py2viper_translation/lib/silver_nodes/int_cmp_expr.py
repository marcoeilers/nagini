"""Comparisons of integer typed Silver expressions."""


import abc

from py2viper_translation.lib.silver_nodes.bool_expr import BoolExpression
from py2viper_translation.lib.typedefs import (
    Expr,
    Info,
    Position,
)


class IntComparison(BoolExpression):   # pylint: disable=abstract-method
    """A base class for all integer comparison operators."""

    def __init__(self, left: 'IntExpression', right: 'IntExpression') -> None:
        self._left = left
        self._right = right

    @abc.abstractmethod
    def _compare(self, left: int, right: int) -> bool:
        """Compare ``left`` to ``right``."""

    def is_always_true(self) -> bool:
        left_value = self._left.get_value()
        if left_value is None:
            return False
        right_value = self._right.get_value()
        if right_value is None:
            return False
        return self._compare(left_value, right_value)

    def is_always_false(self) -> bool:
        left_value = self._left.get_value()
        if left_value is None:
            return False
        right_value = self._right.get_value()
        if right_value is None:
            return False
        return not self._compare(left_value, right_value)


class GtCmp(IntComparison):
    """Greater than comparison."""

    def _compare(self, left: int, right: int) -> bool:
        return left > right

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        left = self._left.translate(translator, ctx, position, info)
        right = self._right.translate(translator, ctx, position, info)
        return translator.viper.GtCmp(
            left, right, position, info)


class GeCmp(IntComparison):
    """Greater equal comparison."""

    def _compare(self, left: int, right: int) -> bool:
        return left >= right

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        left = self._left.translate(translator, ctx, position, info)
        right = self._right.translate(translator, ctx, position, info)
        return translator.viper.GeCmp(
            left, right, position, info)


class LtCmp(IntComparison):
    """Less than comparison."""

    def _compare(self, left: int, right: int) -> bool:
        return left < right

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        left = self._left.translate(translator, ctx, position, info)
        right = self._right.translate(translator, ctx, position, info)
        return translator.viper.LtCmp(
            left, right, position, info)


class LeCmp(IntComparison):
    """Less equal comparison."""

    def _compare(self, left: int, right: int) -> bool:
        return left <= right

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        left = self._left.translate(translator, ctx, position, info)
        right = self._right.translate(translator, ctx, position, info)
        return translator.viper.LeCmp(
            left, right, position, info)
