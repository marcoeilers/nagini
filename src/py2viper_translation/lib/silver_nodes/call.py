"""Function call Silver expression."""

from typing import List

from py2viper_translation.lib.silver_nodes.expression import Expression
from py2viper_translation.lib.typedefs import (
    Expr,
    Info,
    Position,
)


class CallArg:
    """A call argument."""

    def __init__(
            self, parameter_name: str, parameter_type: 'Type',
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
        result = self._argument.translate(translator, ctx, position, info)
        if self._parameter_type.__class__.__name__ == 'IntType':
            result = translator.to_int(result, ctx)
        return result


class CallMixin(Expression):
    """Generic function call mix-in.

    This mix-in should be mixed with an expression type to get a call to
    a function of that type.
    """

    def __init__(self, function: str, args: List[CallArg],
                 typ: 'Type') -> None:
        self._function = function
        self._args = args
        self._type = typ

    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> Expr:
        formal_args = [
            arg.construct_definition(translator, position, info)
            for arg in self._args]
        args = [
            arg.translate_argument(translator, ctx, position, info)
            for arg in self._args]
        typ = self._type.translate(translator)
        return translator.viper.FuncApp(
            self._function, args, position, info, typ, formal_args)


__all__ = ('CallArg',)
