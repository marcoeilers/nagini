"""Reference typed Silver expressions."""


import ast

from py2viper_translation.lib.constants import PRIMITIVES
from py2viper_translation.lib.program_nodes import (
    PythonVar,
)
from py2viper_translation.lib.silver_nodes.expression import Expression
from py2viper_translation.lib.typedefs import (
    Expr,
    Info,
    Position,
)


class RefExpression(Expression):   # pylint: disable=abstract-method
    """A base class for all reference expressions."""

    def __eq__(self, other) -> 'Expression':
        if other is None:
            other = Null()
        return super().__eq__(other)

    def __ne__(self, other) -> 'Expression':
        if other is None:
            other = Null()
        return super().__ne__(other)


class Null(RefExpression):
    """A null reference."""

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        return translator.viper.NullLit(position, info)


class RefVar(RefExpression):
    """A reference to a Ref-typed variable."""

    def __init__(self, var: PythonVar) -> None:
        self._var = var

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        assert self._var.decl.typ() == translator.viper.Ref
        return self._var.ref()


class PythonRefExpression(RefExpression):
    """An reference expression represented by Python reference expression."""

    def __init__(self, node: ast.expr) -> None:
        self._node = node

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        stmt, expr = translator.translate_expr(
            self._node, ctx, expression=True)
        assert not stmt
        typ = translator.get_type(self._node, ctx)
        for primitive in PRIMITIVES:
            assert typ is not ctx.module.global_mod.classes[primitive]
        return expr
