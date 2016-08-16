"""Code for constructing obligation inhales and exhales in contracts."""


import abc

from typing import List, Optional, Tuple

from py2viper_translation.lib import silver_nodes as sil
from py2viper_translation.lib.context import Context
from py2viper_translation.lib.errors import Rules, rules


class ObligationInhaleExhale:
    """Class for constructing obligation inhales and exhales in contracts.

    .. note::

        Credit here has a different meaning than in the original paper
        about obligations. It is used for encoding ``ctoken``.
    """

    def __init__(
            self, bounded: sil.Location,
            unbounded: Optional[sil.Location] = None,
            credit: Optional[sil.Location] = None,
            max_one_inhale: bool = False,
            exhale_only_check_measure: bool = False) -> None:
        """Constructor.

        :param max_one_inhale:
            Indicates that at most one write permission to this
            obligation can be inhaled.
        :param exhale_only_check_measure:
            Indicates that it should only be checked that the measure
            decreases (instead of trying to exhale access).
        """
        self._bounded = bounded
        self._unbounded = unbounded
        self._credit = credit
        self._max_one_inhale = max_one_inhale
        self._exhale_only_check_measure = exhale_only_check_measure

    @property
    def _unbounded_positive(self) -> sil.BoolExpression:
        assert self._unbounded is not None
        return sil.CurrentPerm(self._unbounded) > sil.NoPerm()

    @property
    def _unbounded_acc(self) -> sil.Acc:
        assert self._unbounded is not None
        return sil.Acc(self._unbounded)

    @property
    def _bounded_positive(self) -> sil.BoolExpression:
        return sil.CurrentPerm(self._bounded) > sil.NoPerm()

    @property
    def _bounded_acc(self) -> sil.Acc:
        return sil.Acc(self._bounded)

    @property
    def _credit_acc(self) -> sil.Acc:
        assert self._credit is not None
        return sil.Acc(self._credit)

    def _construct_inhale(
            self, fresh: bool,
            measure_positive_check: Optional[sil.BoolExpression]) -> sil.Acc:
        """Construct obligation inhale."""
        if fresh:
            return self._unbounded_acc
        if self._max_one_inhale:
            acc = sil.Implies(
                sil.CurrentPerm(self._bounded) == sil.NoPerm(),
                sil.Acc(self._bounded))
        else:
            acc = self._bounded_acc
        if measure_positive_check is None:
            return acc
        else:
            return sil.BigAnd([acc, measure_positive_check])

    def _construct_unbounded_exhale(self) -> sil.BoolExpression:
        """Construct unbounded obligation exhale."""
        if self._unbounded is None:
            return sil.TrueLit()
        if self._credit is None:
            return self._unbounded_acc
        else:
            return sil.BoolCondExp(
                self._unbounded_positive,
                self._unbounded_acc,
                self._credit_acc)

    def _construct_bounded_exhale(
            self,
            check: Optional[sil.BoolExpression]) -> sil.BoolExpression:
        """Construct bounded obligation exhale.

        :param check: check if measure is positive
        """
        checks = [self._bounded_positive]
        if check is not None:
            checks.append(check)
        return sil.BoolCondExp(
            sil.BigAnd(checks),
            self._bounded_acc,
            self._construct_unbounded_exhale())

    def construct_use_method_unbounded(self) -> sil.BoolExpression:
        """Construct inhale exhale pair for use in method contract.

        Used for fresh obligations.
        """
        return sil.InhaleExhale(
            self._construct_inhale(True, None),
            self._construct_unbounded_exhale())

    def construct_use_method_bounded(
            self, measure_check: sil.BoolExpression,
            measure_positive_check: sil.BoolExpression,
            is_postconditon: bool) -> sil.BoolExpression:
        """Construct inhale exhale pair for use in method contract.

        Used for bounded obligations.
        """
        if self._exhale_only_check_measure:
            exhale = measure_check
        else:
            exhale = self._construct_bounded_exhale(
                measure_check if not is_postconditon else None)
        return sil.InhaleExhale(
            self._construct_inhale(False, measure_positive_check),
            exhale)

    def construct_use_loop(
            self, measure_check: sil.BoolExpression,
            loop_check_before_var: sil.BoolVar) -> sil.BoolExpression:
        """Construct inhale exhale pair for use in loop invariant."""
        return sil.InhaleExhale(
            self._construct_inhale(False, None),
            sil.BoolCondExp(
                loop_check_before_var,
                self._construct_bounded_exhale(None),
                self._construct_bounded_exhale(measure_check)))


class InexhaleObligationInstanceMixin(abc.ABC):
    """Mixin that provides obligation use methods for obligation instances."""

    @abc.abstractmethod
    def _get_inexhale(
            self, is_method: bool, ctx: Context) -> ObligationInhaleExhale:
        """Create ``ObligationInhaleExhale`` instance.

        :param is_method: ``True`` if translating method contract.
        """

    def get_use_method(
            self, ctx: Context) -> List[Tuple[sil.Expression, Rules]]:
        """Default implementation for obligation use in method contract."""
        inexhale = self._get_inexhale(True, ctx)
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
            self, ctx: Context) -> List[Tuple[sil.Expression, Rules]]:
        """Default implementation for obligation use in loop invariant."""
        obligation_info = ctx.obligation_context.current_loop_info

        terms = []

        # Positive measure.
        loop_condition = obligation_info.construct_loop_condition()
        positive_measure = sil.Implies(loop_condition, self.get_measure() > 0)
        if not positive_measure.is_always_true():
            terms.append((positive_measure,
                          rules.OBLIGATION_LOOP_MEASURE_NON_POSITIVE))

        # Actual inhale / exhale.
        inexhale = self._get_inexhale(False, ctx)
        measure_check = obligation_info.loop_measure_map.check(
            self.get_target(), self.get_measure())
        inhale_exhale = inexhale.construct_use_loop(
            measure_check, sil.BoolVar(obligation_info.loop_check_before_var))
        terms.append((inhale_exhale, None))

        return terms
