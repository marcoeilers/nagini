"""Silver built-in types."""


import abc

from py2viper_translation.lib.typedefs import (
    Expr,
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
        self._name = name

    def translate(self, translator: 'AbstractTranslator') -> Expr:
        return translator.viper.DomainType(self._name, {}, [])
