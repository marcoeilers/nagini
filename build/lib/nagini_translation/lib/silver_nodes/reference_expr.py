"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Reference typed Silver expressions."""


import ast

from nagini_translation.lib.constants import PRIMITIVES
from nagini_translation.lib.program_nodes import (
    PythonVar,
)
from nagini_translation.lib.silver_nodes.expression import Expression
from nagini_translation.lib.typedefs import (
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


class RefExpr(RefExpression):
    """A wrapper around an already-translated Silver expression of type Ref."""

    def __init__(self, e: Expr) -> None:
        self.e = e

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        return self.e


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
            self._node, ctx, impure=False)
        assert not stmt
        typ = translator.get_type(self._node, ctx)
        assert typ.name not in PRIMITIVES
        return expr
