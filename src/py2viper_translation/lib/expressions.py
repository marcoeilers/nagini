"""Helper classes for constructing Silver AST."""

# pragma pylint: disable=abstract-method


import abc
import ast

from typing import List

from py2viper_translation.lib.program_nodes import (
    PythonVar,
)
from py2viper_translation.lib.typedefs import (
    Expr,
    Info,
    Position,
)
from py2viper_translation.lib.util import (
    join_expressions,
)


class Expression(abc.ABC):
    """A base class for all expressions."""

    @abc.abstractmethod
    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        """Translate to Silver expression."""

    def __eq__(self, other) -> 'Expression':
        return EqCmp(self, other)


class Location(Expression):
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


class Acc(Expression):
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
        return translator.viper.PredicateAccessPredicate(
            location, perm, position, info)


class InhaleExhale(Expression):
    """Inhale exhale expression."""

    def __init__(self, inhale, exhale) -> None:
        self._inhale = inhale
        self._exhale = exhale

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        inhale = self._inhale.translate(translator, ctx, position, info)
        exhale = self._exhale.translate(translator, ctx, position, info)
        return translator.viper.InhaleExhaleExp(
            inhale, exhale, position, info)


class RefExpression(Expression):
    """A base class for all reference expressions."""


class VarRef(RefExpression):
    """A variable reference."""

    def __init__(self, var: PythonVar) -> None:
        self._var = var

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        return self._var.ref()


class IntExpression(Expression):
    """A base class for all integer expressions."""


class PythonIntExpression(IntExpression):
    """An integer expression represented by Python int expression."""

    def __init__(self, node: ast.expr) -> None:
        self._node = node

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        int_class = ctx.program.classes['int']
        assert translator.get_type(self._node, ctx) is int_class
        stmt, expr = translator.translate_expr(
            self._node, ctx, expression=True)
        assert not stmt
        return expr


class BoolExpression(Expression):
    """A base class for all boolean expressions."""


class PythonBoolExpression(BoolExpression):
    """An boolean expression represented by Python bool expression."""

    def __init__(self, node: ast.expr) -> None:
        self._node = node

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        stmt, expr = translator.translate_expr(
            self._node, ctx, expression=True)
        assert not stmt
        return expr


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


class CallArg:
    """A call argument."""

    def __init__(
            self, parameter_name: str, parameter_type: Type,
            argument: Expression) -> None:
        self._parameter_name = parameter_name
        self._parameter_type = parameter_type
        self._argument = argument

    def construct_definition(
            self, translator: 'Translator', position: Position,
            info: Info) -> Expr:
        """Construct formal argument definition."""
        typ = self._parameter_type.translate(translator)
        return translator.viper.LocalVarDecl(
            self._parameter_name, typ, position, info)

    def translate_argument(
            self, translator: 'AbstractTranslator', ctx: 'Context',
            position: Position, info: Info) -> Expr:
        """Translate the argument passed to the function."""
        return self._argument.translate(translator, ctx, position, info)


class BoolCall(BoolExpression):
    """A call to a boolean function."""

    def __init__(self, function: str, args: List[CallArg]) -> None:
        self._function = function
        self._args = args

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        formal_args = [
            arg.construct_definition(translator, position, info)
            for arg in self._args]
        args = [
            arg.translate_argument(translator, ctx, position, info)
            for arg in self._args]
        return translator.viper.FuncApp(
            self._function, args, position, info, translator.viper.Bool,
            formal_args)


class BoolOp(BoolExpression):
    """A base class for all boolean operators."""


class BigAnd(BoolExpression):
    """A conjunction of 0 or more elements.

    If it has zero elements, then it is equivalent to ``True``.
    """

    def __init__(self, conjuncts) -> None:
        self._conjuncts = conjuncts

    def is_empty(self) -> None:
        """Check if have any conjuncts."""
        return not self._conjuncts

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        if not self._conjuncts:
            return translator.viper.TrueLit(position, info)
        else:
            conjuncts = [
                conjunct.translate(translator, ctx, position, info)
                for conjunct in self._conjuncts]
            and_operator = (
                lambda left, right:
                translator.viper.And(left, right, position, info))
            return join_expressions(and_operator, conjuncts)


class CmpOp(BoolOp):
    """A base class for all comparison operators."""


class Implies(BoolOp):
    """Implication."""

    def __init__(self, condition: BoolExpression, value: Expression) -> None:
        self._condition = condition
        self._value = value

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        condition = self._condition.translate(translator, ctx, position, info)
        value = self._value.translate(translator, ctx, position, info)
        return translator.viper.Implies(
            condition, value, position, info)


class EqCmp(Expression):
    """Equality comparison."""

    def __init__(self, left: Expression, right: Expression) -> None:
        self._left = left
        self._right = right

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        left = self._left.translate(translator, ctx, position, info)
        right = self._right.translate(translator, ctx, position, info)
        return translator.viper.EqCmp(
            left, right, position, info)


class PermExpression(Expression):
    """A base class for all perm typed expressions."""


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


class CurrentPerm(PermExpression):
    """The current permission amount to a predicate."""

    def __init__(self, location: Location) -> None:
        self._location = location

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        location = self._location.translate(translator, ctx, position, info)
        return translator.viper.CurrentPerm(
            location, position, info)
