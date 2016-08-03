"""Code for working with obligation measures."""


from typing import List

from py2viper_translation.lib.context import Context
from py2viper_translation.lib import expressions as expr
from py2viper_translation.lib.program_nodes import (
    PythonVar,
)
from py2viper_translation.lib.typedefs import (
    Info,
    Expr,
    Position,
    Stmt,
)
from py2viper_translation.translators.obligation.types.base import (
    ObligationInstance,
)


class MeasureMap:
    """Abstraction over map from obligation references to their measures."""

    def __init__(self, measure_map_var: PythonVar,
                 contents_var: PythonVar = None) -> None:
        self._map_var = measure_map_var
        self._contents_var = contents_var

    def check(self, reference: expr.RefExpression,
              value: expr.IntExpression) -> expr.BoolExpression:
        """Generate a check if current value is smaller than in map."""
        args = [
            expr.CallArg('self', expr.REF, expr.VarRef(self._map_var)),
            expr.CallArg('key', expr.REF, reference),
            expr.CallArg('value', expr.INT, value),
        ]
        return expr.BoolCall('Measure$check', args)

    def get_var(self) -> PythonVar:
        """Return a variable representing the measure map."""
        return self._map_var

    def get_contents_var(self) -> PythonVar:
        """Return a variable representing this measure map contents.

        This variable is used in loop invariants to show that measure
        map has not changed.
        """
        return self._contents_var

    def get_contents_access(self) -> expr.Acc:
        """Return access to measure map contents field."""
        return expr.Acc(self._contents_access, expr.WildcardPerm())

    def initialize(
            self, obligation_instances: List['GuardedObligationInstance'],
            translator: 'AbstractTranslator', ctx: Context,
            overriding: bool = False) -> List[Stmt]:
        """Construct a list of statements that initialize measure map.

        If ``overriding`` is ``True``, then adds to measures ``1`` to
        allow overridden method to have the same measure.
        """
        position = translator.no_position(ctx)
        info = translator.no_info(ctx)
        statements = []
        init_call = translator.viper.MethodCall(
            'Measure$topInit', [], [self._map_var.ref()], position, info)
        statements.append(init_call)
        for instance in obligation_instances:
            guard_expression = instance.create_guard_expression()
            call = self._create_measure_set_call(
                instance.obligation_instance, position, info,
                translator, ctx, overriding)
            if guard_expression.is_empty():
                statement = call
            else:
                condition = guard_expression.translate(
                    translator, ctx, position, info)
                statement = translator.viper.If(
                    condition, call,
                    translator.translate_block([], position, info),
                    position, info)
            statements.append(statement)
        if self._contents_var is not None:
            assign = expr.Assign(self._contents_var, self._contents_access)
            statement = assign.translate(translator, ctx, position, info)
            statements.append(statement)
        return statements

    def get_contents_preserved_assertion(self) -> expr.BoolExpression:
        """Construct an assertion that contents has not changed.

        This assertion is used in loop invariants.
        """
        assert self._contents_var is not None
        return expr.VarRef(self._contents_var) == self._contents_access

    @property
    def _contents_access(self) -> expr.FieldAccess:
        return expr.FieldAccess(
            self._map_var, 'Measure$acc', expr.SeqType(expr.REF))

    def _create_measure_set_call(
            self, obligation_instance: ObligationInstance,
            position: Position, info: Info,
            translator: 'AbstractTranslator', ctx: Context,
            overriding: bool) -> Expr:
        reference = obligation_instance.get_target()
        reference_expr = reference.translate(translator, ctx, position, info)
        measure = obligation_instance.get_measure()
        if overriding:
            measure = expr.Inc(measure)
        measure_expr = measure.translate(translator, ctx, position, info)
        args = [self._map_var.ref(), reference_expr, measure_expr]
        return translator.viper.MethodCall(
            'Measure$set', args, [], position, info)
