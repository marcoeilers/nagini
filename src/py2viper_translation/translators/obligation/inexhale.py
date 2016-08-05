"""Code for constructing obligation inhales and exhales in contracts."""


import abc

from typing import Optional

from py2viper_translation.lib import expressions as expr
from py2viper_translation.lib.context import Context


class ObligationInhaleExhale:
    """Class for constructing obligation inhales and exhales in contracts.

    .. note::

        Credit here has a different meaning than in the original paper
        about obligations. It is used for encoding ``ctoken``.
    """

    def __init__(
            self, bounded: expr.Location, unbounded: expr.Location,
            credit: Optional[expr.Location] = None) -> None:
        self._bounded = bounded
        self._unbounded = unbounded
        self._credit = credit

    @property
    def _unbounded_positive(self) -> expr.BoolExpression:
        return expr.CurrentPerm(self._unbounded) > expr.NoPerm()

    @property
    def _unbounded_acc(self) -> expr.Acc:
        return expr.Acc(self._unbounded)

    @property
    def _bounded_positive(self) -> expr.BoolExpression:
        return expr.CurrentPerm(self._bounded) > expr.NoPerm()

    @property
    def _bounded_acc(self) -> expr.Acc:
        return expr.Acc(self._bounded)

    @property
    def _credit_acc(self) -> expr.Acc:
        return expr.Acc(self._credit)

    def _construct_inhale(self, fresh: bool) -> expr.Acc:
        """Construct obligation inhale."""
        if fresh:
            return self._unbounded_acc
        else:
            return self._bounded_acc

    def _construct_unbounded_exhale(self) -> expr.BoolExpression:
        """Construct unbounded obligation exhale."""
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

    def construct_use_method(
            self, measure_check: Optional[expr.BoolExpression],
            fresh: bool, is_postconditon: bool) -> expr.BoolExpression:
        """Construct inhale exhale pair for use in method contract."""
        if fresh:
            exhale = self._construct_unbounded_exhale()
        else:
            exhale = self._construct_bounded_exhale(
                measure_check if not is_postconditon else None)
        return expr.InhaleExhale(self._construct_inhale(fresh), exhale)

    def construct_use_loop(
            self, measure_check: expr.BoolExpression,
            loop_check_before_var: expr.BoolVar) -> expr.BoolExpression:
        """Construct inhale exhale pair for use in loop invariant."""
        return expr.InhaleExhale(
            self._construct_inhale(False),
            expr.BoolCondExp(
                loop_check_before_var,
                self._construct_bounded_exhale(None),
                self._construct_bounded_exhale(measure_check)))


class InexhaleObligationInstanceMixin(abc.ABC):
    """Mixin that provides obligation use methods for obligation instances."""

    @abc.abstractmethod
    def _get_inexhale(self) -> ObligationInhaleExhale:
        """Create ``ObligationInhaleExhale`` instance."""

    def get_use_method(self, ctx: Context) -> expr.Expression:
        """Default implementation for obligation use in method contract."""
        inexhale = self._get_inexhale()
        obligation_info = ctx.actual_function.obligation_info
        if self.is_fresh():
            measure_check = None
        else:
            measure_check = obligation_info.caller_measure_map.check(
                self.get_target(), self.get_measure())
        return inexhale.construct_use_method(
            measure_check,
            self.is_fresh(),
            ctx.obligation_context.is_translating_posts)

    def get_use_loop(self, ctx: Context) -> expr.Expression:
        """Default implementation for obligation use in loop invariant."""
        inexhale = self._get_inexhale()
        obligation_info = ctx.obligation_context.current_loop_info
        measure_check = obligation_info.loop_measure_map.check(
            self.get_target(), self.get_measure())
        return inexhale.construct_use_loop(
            measure_check,
            expr.BoolVar(obligation_info.loop_check_before_var))
