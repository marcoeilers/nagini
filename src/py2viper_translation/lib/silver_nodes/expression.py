"""Silver expressions."""


from py2viper_translation.lib.program_nodes import (
    PythonVar,
)
from py2viper_translation.lib.silver_nodes.base import Expression as IExpr
from py2viper_translation.lib.typedefs import (
    Expr,
    Info,
    Position,
)


class Expression(IExpr):   # pylint: disable=abstract-method
    """A base class for all expressions."""

    EqCmp = None    # To avoid cyclic imports.
    NeCmp = None

    def __eq__(self, other) -> 'Expression':
        return Expression.EqCmp(self, other)

    def __ne__(self, other) -> 'Expression':
        return Expression.NeCmp(self, other)


class VarDecl(Expression):
    """A variable declaration."""

    def __init__(self, var: PythonVar) -> None:
        self._var = var

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        return self._var.decl


class AnyVar(Expression):
    """A variable of a unknown type."""

    def __init__(self, var: PythonVar) -> None:
        self._var = var

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        return self._var.ref()


__all__ = (
    'AnyVar',
    'Expression',
    'VarDecl',
)
