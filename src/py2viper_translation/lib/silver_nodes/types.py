"""Silver built-in types."""


import abc

from typing import List

from py2viper_translation.lib.typedefs import (
    Expr,
    Position,
    Info,
)


class Type:
    """A class for types."""

    @abc.abstractmethod
    def translate(self, translator: 'AbstractTranslator') -> Expr:
        """Translate type to its Silver representation."""


class BoolType(Type):
    """A boolean type."""

    def translate(self, translator: 'AbstractTranslator') -> Expr:
        return translator.viper.Bool


BOOL = BoolType()


class IntType(Type):
    """An integer type."""

    def translate(self, translator: 'AbstractTranslator') -> Expr:
        return translator.viper.Int


INT = IntType()


class RefType(Type):
    """A reference type."""

    def translate(self, translator: 'AbstractTranslator') -> Expr:
        return translator.viper.Ref


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
            self._name, args, {}, domain, args, position, info,
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


class Sequence:
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
