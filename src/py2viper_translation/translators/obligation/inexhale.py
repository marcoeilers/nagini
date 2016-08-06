"""Code for constructing obligation inhales and exhales in contracts."""


import abc

from typing import List, Optional, Tuple

from py2viper_translation.lib import expressions as expr
from py2viper_translation.lib.context import Context
from py2viper_translation.lib.errors import Rules, rules


class ObligationInhaleExhale:
    """Class for constructing obligation inhales and exhales in contracts.

    .. note::

        Credit here has a different meaning than in the original paper
        about obligations. It is used for encoding ``ctoken``.
    """

    def __init__(
            self, bounded: expr.Location,
            unbounded: Optional[expr.Location] = None,
            credit: Optional[expr.Location] = None,
            max_one_inhale: bool = False) -> None:
        """Constructor.

        :param max_one_inhale:
            Indicates that at most one write permission to this
            obligation can be inhaled.
        """
        self._bounded = bounded
        self._unbounded = unbounded
        self._credit = credit
        self._max_one_inhale = max_one_inhale

    @property
    def _unbounded_positive(self) -> expr.BoolExpression:
        assert self._unbounded is not None
        return expr.CurrentPerm(self._unbounded) > expr.NoPerm()

    @property
    def _unbounded_acc(self) -> expr.Acc:
        assert self._unbounded is not None
        return expr.Acc(self._unbounded)

    @property
    def _bounded_positive(self) -> expr.BoolExpression:
        return expr.CurrentPerm(self._bounded) > expr.NoPerm()

    @property
    def _bounded_acc(self) -> expr.Acc:
        return expr.Acc(self._bounded)

    @property
    def _credit_acc(self) -> expr.Acc:
        assert self._credit is not None
        return expr.Acc(self._credit)

    def _construct_inhale(
            self, fresh: bool,
            measure_positive_check: Optional[expr.BoolExpression]) -> expr.Acc:
        """Construct obligation inhale."""
        if fresh:
            return self._unbounded_acc
        if self._max_one_inhale:
            acc = expr.Implies(
                expr.CurrentPerm(self._bounded) == expr.NoPerm(),
                expr.Acc(self._bounded))
        else:
            acc = self._bounded_acc
        if measure_positive_check is None:
            return acc
        else:
            return expr.BigAnd([acc, measure_positive_check])

    def _construct_unbounded_exhale(self) -> expr.BoolExpression:
        """Construct unbounded obligation exhale."""
        if self._unbounded is None:
            return expr.TrueLit()
        if self._credit is None:
            return self._unbounded_acc
        else:
            return expr.BoolCondExp(
                self._unbounded_positive,
                self._unbounded_acc,
                self._credit_acc)

    def _construct_bounded_exhale(
            self,
            check: Optional[expr.BoolExpression]) -> expr.BoolExpression:
        """Construct bounded obligation exhale.

        :param check: check if measure is positive
        """
        checks = [self._bounded_positive]
        if check is not None:
            checks.append(check)
        return expr.BoolCondExp(
            expr.BigAnd(checks),
            self._bounded_acc,
            self._construct_unbounded_exhale())

    def construct_use_method_unbounded(self) -> expr.BoolExpression:
        """Construct inhale exhale pair for use in method contract.

        Used for fresh obligations.
        """
        return expr.InhaleExhale(
            self._construct_inhale(True, None),
            self._construct_unbounded_exhale())

    def construct_use_method_bounded(
            self, measure_check: expr.BoolExpression,
            measure_positive_check: expr.BoolExpression,
            is_postconditon: bool) -> expr.BoolExpression:
        """Construct inhale exhale pair for use in method contract.

        Used for bounded obligations.
        """
        return expr.InhaleExhale(
            self._construct_inhale(False, measure_positive_check),
            self._construct_bounded_exhale(
                measure_check if not is_postconditon else None))

    def construct_use_loop(
            self, measure_check: expr.BoolExpression,
            loop_check_before_var: expr.BoolVar) -> expr.BoolExpression:
        """Construct inhale exhale pair for use in loop invariant."""
        return expr.InhaleExhale(
            self._construct_inhale(False, None),
            expr.BoolCondExp(
                loop_check_before_var,
                self._construct_bounded_exhale(None),
                self._construct_bounded_exhale(measure_check)))


class InexhaleObligationInstanceMixin(abc.ABC):
    """Mixin that provides obligation use methods for obligation instances."""

    @abc.abstractmethod
    def _get_inexhale(self) -> ObligationInhaleExhale:
        """Create ``ObligationInhaleExhale`` instance."""

    def get_use_method(
            self, ctx: Context) -> List[Tuple[expr.Expression, Rules]]:
        """Default implementation for obligation use in method contract."""
        inexhale = self._get_inexhale()
        obligation_info = ctx.actual_function.obligation_info
        if self.is_fresh():
            return [(inexhale.construct_use_method_unbounded(), None)]
        else:
            measure_check = obligation_info.caller_measure_map.check(
                self.get_target(), self.get_measure())
            return [(inexhale.construct_use_method_bounded(
                measure_check, self.get_measure() > 0,
                ctx.obligation_context.is_translating_posts), None)]

    def get_use_loop(
            self, ctx: Context) -> List[Tuple[expr.Expression, Rules]]:
        """Default implementation for obligation use in loop invariant."""
        obligation_info = ctx.obligation_context.current_loop_info

        # Positive measure.
        loop_condition = obligation_info.construct_loop_condition()
        positive_measure = expr.Implies(loop_condition, self.get_measure() > 0)

        # Actual inhale / exhale.
        inexhale = self._get_inexhale()
        measure_check = obligation_info.loop_measure_map.check(
            self.get_target(), self.get_measure())
        inhale_exhale = inexhale.construct_use_loop(
            measure_check, expr.BoolVar(obligation_info.loop_check_before_var))

        return [
            (positive_measure, rules.OBLIGATION_LOOP_MEASURE_NON_POSITIVE),
            (inhale_exhale, None)]
