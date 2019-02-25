"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Code for constructing obligation inhales and exhales in contracts."""


import abc

from typing import List, Optional, Tuple

from nagini_translation.lib import silver_nodes as sil
from nagini_translation.lib.context import Context
from nagini_translation.lib.errors import Rules, rules


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
            skip_exhale: bool = False,
            skip_inhale: bool = False,
            credit_only: bool = False) -> None:
        """Constructor.

        :param skip_exhale:
            Indicates that exhale part should be equivalent to ``True``.
        """
        self._bounded = bounded
        self._unbounded = unbounded
        self._credit = credit
        self._skip_exhale = skip_exhale
        self._skip_inhale = skip_inhale
        self._credit_only = credit_only

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

    def _construct_inhale(self, fresh: bool) -> sil.Acc:
        """Construct obligation inhale."""
        if self._skip_inhale:
            return sil.TrueLit()
        if self._credit_only:
            return self._credit_acc
        if fresh:
            return self._unbounded_acc
        else:
            return self._bounded_acc

    def _construct_unbounded_exhale(self) -> sil.BoolExpression:
        """Construct unbounded obligation exhale."""
        if self._unbounded is None:
            return sil.FalseLit()
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
        if self._credit_only:
            exhale = self._credit_acc
        else:
            exhale = self._construct_unbounded_exhale()
        return sil.InhaleExhale(self._construct_inhale(True), exhale)

    def construct_use_method_bounded(
            self, measure_check: sil.BoolExpression,
            is_postconditon: bool) -> sil.BoolExpression:
        """Construct inhale exhale pair for use in method contract.

        Used for bounded obligations.
        """
        if self._skip_exhale:
            exhale = sil.TrueLit()
        elif self._credit_only:
            exhale = self._credit_acc
        else:
            exhale = self._construct_bounded_exhale(
                measure_check if not is_postconditon else None)
        return sil.InhaleExhale(self._construct_inhale(False), exhale)

    def construct_use_loop(
            self, measure_check: Optional[sil.BoolExpression],
            loop_check_before_var: sil.BoolVar) -> sil.BoolExpression:
        """Construct inhale exhale pair for use in loop invariant.

        ``measure_check is None`` indicates that obligation is fresh.
        """
        if self._skip_exhale:
            exhale = sil.TrueLit()
        elif self._credit_only:
            exhale = self._credit_acc
        elif measure_check is None:
            exhale = self._construct_unbounded_exhale()
        else:
            exhale = sil.BoolCondExp(
                loop_check_before_var,
                self._construct_bounded_exhale(None),
                self._construct_bounded_exhale(measure_check))
        inhale = self._construct_inhale(measure_check is None)
        return sil.InhaleExhale(inhale, exhale)

    def construct_obligation_bound(self) -> sil.Statement:
        """Construct statement for bounding obligation."""
        if self._credit_only:
            return sil.Exhale(sil.TrueLit())
        return sil.If(
            self._unbounded_positive,
            [sil.Exhale(self._unbounded_acc), sil.Inhale(self._bounded_acc)],
            [])


class InexhaleObligationInstanceMixin(abc.ABC):
    """Mixin that provides obligation use methods for obligation instances.

    This mix-in should be mixed into ``ObligationInstance`` that desire
    to have default ``get_use_method`` and ``get_use_loop`` behaviour.
    """

    @abc.abstractmethod
    def _get_inexhale(self, ctx: Context) -> ObligationInhaleExhale:
        """Create ``ObligationInhaleExhale`` instance."""

    def get_use_method(
            self, ctx: Context) -> List[Tuple[sil.Expression, Rules]]:
        """Default implementation for obligation use in method contract."""
        inexhale = self._get_inexhale(ctx)
        obligation_info = ctx.actual_function.obligation_info
        if self.is_fresh():
            return [(inexhale.construct_use_method_unbounded(), None)]
        else:
            terms = []

            # Positive measure.
            if not ctx.obligation_context.is_translating_posts:
                positive_measure = self.get_measure() > 0
                if not positive_measure.is_always_true():
                    terms.append((positive_measure,
                                  rules.OBLIGATION_MEASURE_NON_POSITIVE))

            # Actual inhale / exhale.
            measure_check = obligation_info.caller_measure_map.check(
                self.get_target(), self.get_measure())
            inhale_exhale = inexhale.construct_use_method_bounded(
                measure_check,
                ctx.obligation_context.is_translating_posts)
            terms.append((inhale_exhale, None))

            return terms

    def get_use_loop(
            self, ctx: Context) -> List[Tuple[sil.Expression, Rules]]:
        """Default implementation for obligation use in loop invariant."""
        obligation_info = ctx.obligation_context.current_loop_info

        terms = []

        # Positive measure.
        if not self.is_fresh():
            loop_condition = obligation_info.construct_loop_condition()
            positive_measure = sil.Implies(
                loop_condition, self.get_measure() > 0)
            if not positive_measure.is_always_true():
                terms.append((positive_measure,
                              rules.OBLIGATION_LOOP_MEASURE_NON_POSITIVE))

        # Actual inhale / exhale.
        inexhale = self._get_inexhale(ctx)
        if self.is_fresh():
            measure_check = None
        else:
            measure_check = obligation_info.loop_measure_map.check(
                self.get_target(), self.get_measure())
        inhale_exhale = inexhale.construct_use_loop(
            measure_check, sil.BoolVar(obligation_info.loop_check_before_var))
        terms.append((inhale_exhale, None))

        return terms

    def get_obligation_bound(self, ctx: Context) -> sil.Statement:
        """Default implementation for bounding an obligation."""
        assert self.is_fresh()
        inexhale = self._get_inexhale(ctx)
        return inexhale.construct_obligation_bound()
