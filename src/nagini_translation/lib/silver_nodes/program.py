"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Top level Silver constructs."""


from nagini_translation.lib.silver_nodes.base import Node
from nagini_translation.lib.typedefs import Info
from nagini_translation.lib.typedefs import Field as FieldType
from nagini_translation.lib.typedefs import Position
from nagini_translation.lib.typedefs import Predicate as PredicateType


class Predicate(Node):
    """Bodyless predicate with one ``Ref`` argument definition."""

    def __init__(self, name: str, var_name: str) -> None:
        self._name = name
        self._var_name = var_name

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> PredicateType:
        var = translator.viper.LocalVarDecl(
            self._var_name, translator.viper.Ref, position, info)
        return translator.viper.Predicate(
            self._name, [var], None, position, info)


class Field(Node):
    """Field definition."""

    def __init__(self, name: str, typ: 'Type') -> None:
        self._name = name
        self._type = typ

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> FieldType:
        typ = self._type.translate(translator)
        return translator.viper.Field(
            self._name, typ, position, info)
