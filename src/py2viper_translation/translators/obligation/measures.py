"""Code for working with obligation measures."""


from typing import List

from py2viper_translation.lib import silver_nodes as sil
from py2viper_translation.lib.context import Context
from py2viper_translation.lib.config import obligation_config
from py2viper_translation.lib.program_nodes import (
    PythonVar,
)
from py2viper_translation.lib.typedefs import (
    Stmt,
)


class MeasureMap:
    """Abstraction over map from obligation references to their measures."""

    def __init__(self, measure_map_var: PythonVar) -> None:
        self._map_var = measure_map_var
        self._measure_domain = sil.Domain('Measure$')
        self._measure_domain.declare_function('Measure$create')

    @property
    def _measure_var_type(self) -> sil.Type:
        return sil.SeqType(self._measure_domain.get_type())

    def _create_measure(
            self, guard: sil.BoolExpression, key: sil.RefExpression,
            value: sil.IntExpression) -> sil.DomainFuncApp:
        return self._measure_domain.call_function(
            'Measure$create', [guard, key, value])

    def check(self, reference: sil.RefExpression,
              value: sil.IntExpression) -> sil.BoolExpression:
        """Generate a check if current value is smaller than in map."""
        if (obligation_config.disable_measures or
                obligation_config.disable_measure_check):
            return sil.TrueLit()
        args = [
            sil.CallArg('map', self._measure_var_type,
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
        measures = []
        for instance in obligation_instances:
            guard_expression = instance.create_guard_expression()
            value = instance.obligation_instance.get_measure()
            if overriding:
                value = sil.Inc(value)
            measure = self._create_measure(
                guard_expression,
                instance.obligation_instance.get_target(), value)
            measures.append(measure)
        assign = sil.Assign(
            self._map_var,
            sil.Sequence(self._measure_domain.get_type(), measures))
        statement = assign.translate(translator, ctx, position, info)
        return [statement]
