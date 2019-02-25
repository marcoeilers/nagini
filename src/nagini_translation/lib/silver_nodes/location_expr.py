"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Silver expressions for denoting memory locations."""


from nagini_translation.lib.silver_nodes.expression import Expression
from nagini_translation.lib.silver_nodes.bool_expr import BoolExpression
from nagini_translation.lib.silver_nodes.perm_expr import (
    FullPerm,
)
from nagini_translation.lib.typedefs import (
    Expr,
    Info,
    Position,
)


class Location(Expression):   # pylint: disable=abstract-method
    """Denotes an access to specific location."""


class PredicateAccess(Location):
    """A predicate with one ``Ref`` argument access."""

    def __init__(self, name: str, reference: 'RefExpression') -> None:
        self._name = name
        self._reference = reference

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        reference = self._reference.translate(translator, ctx, position, info)
        return translator.viper.PredicateAccess(
            [reference], self._name, position, info)


class FieldAccess(Location):
    """Field access."""

    def __init__(self, target: 'RefExpression', field_name: str,
                 field_type: 'Type') -> None:
        self._target = target
        self._field_name = field_name
        self._field_type = field_type

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        target = self._target.translate(translator, ctx, position, info)
        field = translator.viper.Field(
            self._field_name, self._field_type.translate(translator),
            position, info)
        return translator.viper.FieldAccess(
            target, field, position, info)


class Acc(BoolExpression):
    """Access to specific location."""

    def __init__(
            self, location: Location,
            perm: 'PermExpression' = None) -> None:
        self._location = location
        self._perm = perm or FullPerm()

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        location = self._location.translate(translator, ctx, position, info)
        perm = self._perm.translate(translator, ctx, position, info)
        if isinstance(self._location, PredicateAccess):
            return translator.viper.PredicateAccessPredicate(
                location, perm, position, info)
        else:
            return translator.viper.FieldAccessPredicate(
                location, perm, position, info)


__all__ = (
    'Acc',
    'FieldAccess',
    'Location',
    'PredicateAccess',
)
