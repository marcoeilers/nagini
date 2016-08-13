"""Code for working with obligation measures."""


from typing import List

from py2viper_translation.lib import silver_nodes as sil
from py2viper_translation.lib.context import Context
from py2viper_translation.lib.config import obligation_config
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

    def __init__(self, measure_map_var: PythonVar) -> None:
        self._map_var = measure_map_var

    def check(self, reference: sil.RefExpression,
              value: sil.IntExpression) -> sil.BoolExpression:
        """Generate a check if current value is smaller than in map."""
        if (obligation_config.disable_measures or
                obligation_config.disable_measure_check):
            return sil.TrueLit()
        args = [
            sil.CallArg(
                'map', sil.SeqType(sil.DomainType('Measure$')),
                sil.VarRef(self._map_var)),
            sil.CallArg('key', sil.REF, reference),
            sil.CallArg('value', sil.INT, value),
        ]
        return sil.BoolCall('Measure$check', args)

    def get_var(self) -> PythonVar:
        """Return a variable representing the measure map."""
        return self._map_var

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
        typ = translator.viper.DomainType('Measure$', {}, [])
        init = translator.viper.LocalVarAssign(
            self._map_var.ref(),
            translator.viper.EmptySeq(typ, position, info),
            position, info)
        statements.append(init)
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
        return statements

    def _create_measure_set_call(
            self, obligation_instance: ObligationInstance,
            position: Position, info: Info,
            translator: 'AbstractTranslator', ctx: Context,
            overriding: bool) -> Expr:
        reference = obligation_instance.get_target()
        reference_expr = reference.translate(translator, ctx, position, info)
        measure = obligation_instance.get_measure()
        if overriding:
            measure = sil.Inc(measure)
        measure_expr = measure.translate(translator, ctx, position, info)

        typ = translator.viper.DomainType('Measure$', {}, [])
        args = [reference_expr, measure_expr]
        elems = [
            translator.viper.DomainFuncApp(
                'Measure$create', args, {}, typ, args, position, info,
                'Measure$')
        ]
        seq = translator.viper.ExplicitSeq(elems, position, info)

        return translator.viper.LocalVarAssign(
            self._map_var.ref(),
            translator.viper.SeqAppend(
                self._map_var.ref(), seq, position, info),
            position, info)
