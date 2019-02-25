"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Silver built-in types."""


import abc

from typing import List

from nagini_translation.lib.typedefs import (
    Expr,
    Position,
    Info,
)


class Type:
    """A class for types."""

    @abc.abstractmethod
    def translate(self, translator: 'AbstractTranslator') -> Expr:
        """Translate type to its Silver representation."""

    def adjust_type(self, translator: 'AbstractTranslator', e: Expr,
                    ctx: 'Context') -> Expr:
        """Convert the expression e to this Silver type if possible."""
        return e


class BoolType(Type):
    """A boolean type."""

    def translate(self, translator: 'AbstractTranslator') -> Expr:
        return translator.viper.Bool

    def adjust_type(self, translator: 'AbstractTranslator', e: Expr,
                    ctx: 'Context') -> Expr:
        return translator.to_bool(e, ctx)


BOOL = BoolType()


class IntType(Type):
    """An integer type."""

    def translate(self, translator: 'AbstractTranslator') -> Expr:
        return translator.viper.Int

    def adjust_type(self, translator: 'AbstractTranslator', e: Expr,
                    ctx: 'Context') -> Expr:
        return translator.to_int(e, ctx)

INT = IntType()


class RefType(Type):
    """A reference type."""

    def translate(self, translator: 'AbstractTranslator') -> Expr:
        return translator.viper.Ref

    def adjust_type(self, translator: 'AbstractTranslator', e: Expr,
                    ctx: 'Context') -> Expr:
        return translator.to_ref(e, ctx)


REF = RefType()


class PermType(Type):
    """The Viper permission type."""

    def translate(self, translator: 'AbstractTranslator') -> Expr:
        return translator.viper.Perm


PERM = PermType()


class SeqType(Type):
    """A sequence type."""

    def __init__(self, element_type: Type) -> None:
        self._element_type = element_type

    def translate(self, translator: 'AbstractTranslator') -> Expr:
        element_type = self._element_type.translate(translator)
        return translator.viper.SeqType(element_type)


class DomainType(Type):
    """A domain type."""

    def __init__(self, name: str) -> None:
        self.name = name

    def translate(self, translator: 'AbstractTranslator') -> Expr:
        return translator.viper.DomainType(self.name, {}, [])


class DomainFuncApp:
    """A domain function call."""

    def __init__(
            self, name: str, args: List['Expression'],
            domain: DomainType) -> None:
        self._name = name
        self._args = args
        self._domain = domain

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        """Translate to Silver DomainFuncApp."""
        args = [arg.translate(translator, ctx, position, info)
                for arg in self._args]
        domain = self._domain.translate(translator)
        return translator.viper.DomainFuncApp(
            self._name, args, domain, position, info,
            self._domain.name)


class Domain:
    """A helper class for using a domain defined in Silver."""

    def __init__(self, name: str) -> None:
        self._name = name
        self._functions = set()

    def get_type(self) -> DomainType:
        """Return the Domain Type."""
        return DomainType(self._name)

    def declare_function(self, name: str) -> None:
        """Declare new function in domain."""
        self._functions.add(name)

    def call_function(
            self, name: str, args: List['Expression']) -> DomainFuncApp:
        """Call a domain function."""
        assert name in self._functions
        return DomainFuncApp(name, args, self.get_type())


class PSeq:
    """A helper class for generating Silver sequences."""

    def __init__(self, typ: Type, elements: List['Expression']) -> None:
        self._type = typ
        self._elements = elements

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        """Translate to Silver sequence."""
        if not self._elements:
            typ = self._type.translate(translator)
            return translator.viper.EmptySeq(typ, position, info)
        else:
            elements = [element.translate(translator, ctx, position, info)
                        for element in self._elements]
            return translator.viper.ExplicitSeq(elements, position, info)
