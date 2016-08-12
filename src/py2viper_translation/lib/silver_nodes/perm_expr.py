"""Permission typed Silver expressions."""


from py2viper_translation.lib.silver_nodes.expression import Expression
from py2viper_translation.lib.silver_nodes.perm_cmp_expr import (
    PermGtCmp,
    PermGeCmp,
    PermLtCmp,
    PermLeCmp,
)
from py2viper_translation.lib.typedefs import (
    Expr,
    Info,
    Position,
)


class PermExpression(Expression):   # pylint: disable=abstract-method
    """A base class for all perm typed expressions."""

    def __sub__(self, other: 'PermExpression') -> 'PermExpression':
        return PermSub(self, other)

    def __gt__(self, other: 'PermExpression') -> 'BoolExpression':
        return PermGtCmp(self, other)

    def __ge__(self, other: 'PermExpression') -> 'BoolExpression':
        return PermGeCmp(self, other)

    def __lt__(self, other: 'PermExpression') -> 'BoolExpression':
        return PermLtCmp(self, other)

    def __le__(self, other: 'PermExpression') -> 'BoolExpression':
        return PermLeCmp(self, other)


class PermSub(PermExpression):
    """A subtraction of two permission values."""

    def __init__(self, left: PermExpression, right: PermExpression) -> None:
        self._left = left
        self._right = right

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        left = self._left.translate(translator, ctx, position, info)
        right = self._right.translate(translator, ctx, position, info)
        return translator.viper.PermSub(
            left, right, position, info)


class NoPerm(PermExpression):
    """No permission."""

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        return translator.viper.NoPerm(position, info)


class FullPerm(PermExpression):
    """Full permission."""

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        return translator.viper.FullPerm(position, info)


class WildcardPerm(PermExpression):
    """Full permission."""

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        return translator.viper.WildcardPerm(position, info)


class CurrentPerm(PermExpression):
    """The current permission amount to a predicate."""

    def __init__(self, location: 'Location') -> None:
        self._location = location

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        location = self._location.translate(translator, ctx, position, info)
        return translator.viper.CurrentPerm(
            location, position, info)


class IntegerPerm(PermExpression):
    """A multiplication of full permission."""

    def __init__(self, value: 'IntExpression') -> None:
        self._value = value

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        value = self._value.translate(translator, ctx, position, info)
        full_perm = translator.viper.FullPerm(position, info)
        return translator.viper.IntPermMul(
            value, full_perm, position, info)
