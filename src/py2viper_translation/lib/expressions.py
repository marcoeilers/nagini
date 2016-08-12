"""Helper classes for constructing Silver AST."""

# pragma pylint: disable=abstract-method


import abc
import ast

from typing import List, Optional, Union

from py2viper_translation.lib.program_nodes import (
    PythonVar,
)
from py2viper_translation.lib.typedefs import (
    Expr,
    Info,
    Position,
    Stmt,
)
from py2viper_translation.lib.util import (
    join_expressions,
)


class Node(abc.ABC):
    """A base class for all nodes."""

    @abc.abstractmethod
    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        """Translate to Silver."""


class Expression(Node):
    """A base class for all expressions."""

    @abc.abstractmethod
    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        """Translate to Silver expression."""

    def __eq__(self, other) -> 'Expression':
        if other is None:
            other = Null()
        return EqCmp(self, other)

    def __ne__(self, other) -> 'Expression':
        if other is None:
            other = Null()
        return NeCmp(self, other)


class Statement(Node):
    """A base class for all statements."""

    @abc.abstractmethod
    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Stmt:
        """Translate to Silver Statement."""


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


class RefExpression(Expression):
    """A base class for all reference expressions."""


class Null(RefExpression):
    """A null reference."""

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        return translator.viper.NullLit(position, info)


class VarRef(RefExpression):
    """A variable reference."""

    def __init__(self, var: PythonVar) -> None:
        self._var = var

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        return self._var.ref()


class VarDecl(Expression):
    """A variable declaration."""

    def __init__(self, var: PythonVar) -> None:
        self._var = var

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        return self._var.decl


class PythonRefExpression(RefExpression):
    """An reference expression represented by Python reference expression."""

    def __init__(self, node: ast.expr) -> None:
        self._node = node

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        stmt, expr = translator.translate_expr(
            self._node, ctx, expression=True)
        assert not stmt
        return expr


class IntExpression(Expression):
    """A base class for all integer expressions."""

    def get_value(self) -> Optional[int]:
        """Try to extract Python integer representing this expression.

        Otherwise, return ``None``.
        """
        return None

    def __gt__(self, other: Union['IntExpression', int]) -> 'BoolExpression':
        if isinstance(other, int):
            other = RawIntExpression(other)
        return GtCmp(self, other)

    def __ge__(self, other: Union['IntExpression', int]) -> 'BoolExpression':
        if isinstance(other, int):
            other = RawIntExpression(other)
        return GeCmp(self, other)

    def __lt__(self, other: Union['IntExpression', int]) -> 'BoolExpression':
        if isinstance(other, int):
            other = RawIntExpression(other)
        return LtCmp(self, other)

    def __le__(self, other: Union['IntExpression', int]) -> 'BoolExpression':
        if isinstance(other, int):
            other = RawIntExpression(other)
        return LeCmp(self, other)

    def __add__(self, other: Union['IntExpression', int]) -> 'IntExpression':
        if isinstance(other, int):
            other = RawIntExpression(other)
        return Add(self, other)

    def __sub__(self, other: Union['IntExpression', int]) -> 'IntExpression':
        if isinstance(other, int):
            other = RawIntExpression(other)
        return Sub(self, other)


class Add(IntExpression):
    """Add to integers."""

    def __init__(self, left: IntExpression, right: IntExpression) -> None:
        self._left = left
        self._right = right

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        left = self._left.translate(translator, ctx, position, info)
        right = self._right.translate(translator, ctx, position, info)
        return translator.viper.Add(left, right, position, info)


class Sub(IntExpression):
    """Subtract to integers."""

    def __init__(self, left: IntExpression, right: IntExpression) -> None:
        self._left = left
        self._right = right

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        left = self._left.translate(translator, ctx, position, info)
        right = self._right.translate(translator, ctx, position, info)
        return translator.viper.Sub(left, right, position, info)


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
        int_class = ctx.program.classes['int']
        assert translator.get_type(self._node, ctx) is int_class
        stmt, expr = translator.translate_expr(
            self._node, ctx, expression=True)
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


class Sum(IntExpression):
    """A sum of 0 or more elements."""

    def __init__(self, elements) -> None:
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


class BoolExpression(Expression):
    """A base class for all boolean expressions."""

    def is_always_true(self) -> bool:
        """Return if this expression translation would always yield True."""
        return False

    def is_always_false(self) -> bool:
        """Return if this expression translation would always yield False."""
        return False


class TrueLit(BoolExpression):
    """``True`` literal."""

    def is_always_true(self) -> bool:
        """Return if this expression translation would always yield True."""
        return True

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        return translator.viper.TrueLit(position, info)


class FalseLit(BoolExpression):
    """``False`` literal."""

    def is_always_false(self) -> bool:
        """Return if this expression translation would always yield False."""
        return True

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        return translator.viper.FalseLit(position, info)


class Not(BoolExpression):
    """Negation of other expression."""

    def __init__(self, value: BoolExpression) -> None:
        self._value = value

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        value = self._value.translate(translator, ctx, position, info)
        return translator.viper.Not(value, position, info)


class ForPerm(BoolExpression):
    """ForPerm expression."""

    def __init__(
            self, var_name: str, targets: List['Predicate'],
            body: BoolExpression) -> None:
        self._var_name = var_name
        self._targets = targets
        self._body = body

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        var = translator.viper.LocalVarDecl(
            self._var_name, translator.viper.Ref, position, info)
        targets = [
            target.translate(translator, ctx, position, info)
            for target in self._targets]
        body = self._body.translate(translator, ctx, position, info)
        return translator.viper.ForPerm(
            var, targets, body, position, info)


class PythonBoolExpression(BoolExpression):
    """An boolean expression represented by Python bool expression."""

    def __init__(self, node: ast.expr) -> None:
        self._node = node

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        stmt, expr = translator.translate_to_bool(
            self._node, ctx, expression=True)
        assert not stmt
        return expr


class BoolVar(BoolExpression):
    """A boolean variable reference."""

    def __init__(self, var: PythonVar) -> None:
        self._var = var

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        bool_class = ctx.program.classes['bool']
        assert self._var.type is bool_class
        return self._var.ref()


class InhaleExhale(BoolExpression):
    """Inhale exhale expression."""

    def __init__(self, inhale: BoolExpression, exhale: BoolExpression) -> None:
        self._inhale = inhale
        self._exhale = exhale

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        inhale = self._inhale.translate(translator, ctx, position, info)
        exhale = self._exhale.translate(translator, ctx, position, info)
        return translator.viper.InhaleExhaleExp(
            inhale, exhale, position, info)


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

    def is_always_true(self) -> bool:
        return self.is_empty()

    def is_always_false(self) -> bool:
        return any(
            conjunct.is_always_false()
            for conjunct in self._conjuncts)

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        if self.is_always_false():
            return translator.viper.FalseLit(position, info)
        conjuncts = [
            conjunct.translate(translator, ctx, position, info)
            for conjunct in self._conjuncts
            if not conjunct.is_always_true()]
        if not conjuncts:
            return translator.viper.TrueLit(position, info)
        else:
            and_operator = (
                lambda left, right:
                translator.viper.And(left, right, position, info))
            return join_expressions(and_operator, conjuncts)


class BigOr(BoolExpression):
    """A disjunction of 0 or more elements.

    If it has zero elements, then it is equivalent to ``False``.
    """

    def __init__(self, disjuncts) -> None:
        self._disjuncts = disjuncts

    def is_empty(self) -> None:
        """Check if have any elements."""
        return not self._disjuncts

    def is_always_true(self) -> bool:
        return any(
            disjunct.is_always_true()
            for disjunct in self._disjuncts)

    def is_always_false(self) -> bool:
        return self.is_empty()

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        if self.is_always_true():
            return translator.viper.TrueLit(position, info)
        disjuncts = [
            disjunct.translate(translator, ctx, position, info)
            for disjunct in self._disjuncts
            if not disjunct.is_always_false()]
        if not disjuncts:
            return translator.viper.FalseLit(position, info)
        else:
            or_operator = (
                lambda left, right:
                translator.viper.Or(left, right, position, info))
            return join_expressions(or_operator, disjuncts)


class BoolCondExp(BoolExpression):
    """A ternary operator with boolean result."""

    def __init__(self, condition: BoolExpression, then: BoolExpression,
                 els: BoolExpression) -> None:
        self._condition = condition
        self._then = then
        self._els = els

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        condition = self._condition.translate(translator, ctx, position, info)
        then = self._then.translate(translator, ctx, position, info)
        els = self._els.translate(translator, ctx, position, info)
        return translator.viper.CondExp(
            condition, then, els, position, info)


class CmpOp(BoolOp):
    """A base class for all comparison operators."""


class Implies(BoolOp):
    """Implication."""

    def __init__(self, condition: BoolExpression, value: Expression) -> None:
        self._condition = condition
        self._value = value

    def is_always_true(self) -> bool:
        return (self._condition.is_always_false() or
                self._value.is_always_true())

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        value = self._value.translate(translator, ctx, position, info)
        if self._condition.is_always_true():
            return value
        else:
            condition = self._condition.translate(
                translator, ctx, position, info)
            return translator.viper.Implies(
                condition, value, position, info)


class EqCmp(BoolExpression):
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


class NeCmp(BoolExpression):
    """Inequality comparison."""

    def __init__(self, left: Expression, right: Expression) -> None:
        self._left = left
        self._right = right

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        left = self._left.translate(translator, ctx, position, info)
        right = self._right.translate(translator, ctx, position, info)
        return translator.viper.NeCmp(
            left, right, position, info)


class IntComparison(BoolExpression):
    """A base class for all integer comparison operators."""

    def __init__(self, left: IntExpression, right: IntExpression) -> None:
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


class PermExpression(Expression):
    """A base class for all perm typed expressions."""

    def __sub__(self, other: 'PermExpression') -> 'PermExpression':
        return PermSub(self, other)

    def __gt__(self, other: 'PermExpression') -> 'PermExpression':
        return PermGtCmp(self, other)

    def __ge__(self, other: 'PermExpression') -> 'PermExpression':
        return PermGeCmp(self, other)

    def __lt__(self, other: 'PermExpression') -> 'PermExpression':
        return PermLtCmp(self, other)

    def __le__(self, other: 'PermExpression') -> 'PermExpression':
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


class PermGtCmp(BoolExpression):
    """Greater than permission comparison."""

    def __init__(self, left: PermExpression, right: PermExpression) -> None:
        self._left = left
        self._right = right

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        left = self._left.translate(translator, ctx, position, info)
        right = self._right.translate(translator, ctx, position, info)
        return translator.viper.PermGtCmp(
            left, right, position, info)


class PermGeCmp(BoolExpression):
    """Greater equal permission comparison."""

    def __init__(self, left: PermExpression, right: PermExpression) -> None:
        self._left = left
        self._right = right

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        left = self._left.translate(translator, ctx, position, info)
        right = self._right.translate(translator, ctx, position, info)
        return translator.viper.PermGeCmp(
            left, right, position, info)


class PermLtCmp(BoolExpression):
    """Less than permission comparison."""

    def __init__(self, left: PermExpression, right: PermExpression) -> None:
        self._left = left
        self._right = right

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        left = self._left.translate(translator, ctx, position, info)
        right = self._right.translate(translator, ctx, position, info)
        return translator.viper.PermLtCmp(
            left, right, position, info)


class PermLeCmp(BoolExpression):
    """Less equal permission comparison."""

    def __init__(self, left: PermExpression, right: PermExpression) -> None:
        self._left = left
        self._right = right

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        left = self._left.translate(translator, ctx, position, info)
        right = self._right.translate(translator, ctx, position, info)
        return translator.viper.PermLeCmp(
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

    def __init__(self, location: Location) -> None:
        self._location = location

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        location = self._location.translate(translator, ctx, position, info)
        return translator.viper.CurrentPerm(
            location, position, info)


class IntegerPerm(PermExpression):
    """A multiplication of full permission."""

    def __init__(self, value: IntExpression) -> None:
        self._value = value

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        value = self._value.translate(translator, ctx, position, info)
        full_perm = translator.viper.FullPerm(position, info)
        return translator.viper.IntPermMul(
            value, full_perm, position, info)


class Inhale(Statement):
    """Inhale statement."""

    def __init__(self, value: Expression) -> None:
        self._value = value

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        value = self._value.translate(translator, ctx, position, info)
        return translator.viper.Inhale(value, position, info)


class Exhale(Statement):
    """Exhale statement."""

    def __init__(self, value: Expression) -> None:
        self._value = value

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        value = self._value.translate(translator, ctx, position, info)
        return translator.viper.Exhale(value, position, info)


class Assert(Statement):
    """Assert statement."""

    def __init__(self, value: Expression) -> None:
        self._value = value

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        value = self._value.translate(translator, ctx, position, info)
        return translator.viper.Assert(value, position, info)


class Assign(Statement):
    """Assign statement."""

    def __init__(self, var: PythonVar, value: Expression) -> None:
        self._var = var
        self._value = value

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        value = self._value.translate(translator, ctx, position, info)
        return translator.viper.LocalVarAssign(
            self._var.ref(), value, position, info)


class Predicate(Node):
    """Bodyless predicate with one ``Ref`` argument definition."""

    def __init__(self, name: str, var_name: str) -> None:
        self._name = name
        self._var_name = var_name

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        var = translator.viper.LocalVarDecl(
            self._var_name, translator.viper.Ref, position, info)
        return translator.viper.Predicate(
            self._name, [var], None, position, info)


class Field(Node):
    """Field definition."""

    def __init__(self, name: str, typ: Type) -> None:
        self._name = name
        self._type = typ

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        typ = self._type.translate(translator)
        return translator.viper.Field(
            self._name, typ, position, info)
