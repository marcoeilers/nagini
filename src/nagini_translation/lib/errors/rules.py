"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Conversion rules from Silver level errors to Nagini errors."""


from typing import Dict, Tuple


class Rules(Dict[Tuple[str, str], Tuple[str, str]]):
    """Error conversion rules."""


TERMINATION_CHECK_MEASURE_NON_POSITIVE = {
    ('assert.failed', 'assertion.false'):
        ('termination_check.failed', 'termination_measure.non_positive')
}
TERMINATION_CHECK_MEASURE_NON_DECREASING = {
    ('assert.failed', 'assertion.false'):
        ('termination_check.failed', 'measure.non_decreasing')
}
TERMINATION_CHECK_GAP_ENABLED = {
    ('assert.failed', 'assertion.false'):
        ('termination_check.failed', 'gap.enabled')
}
TERMINATION_CHECK_CHILD_TERMINATION_NOT_IMPLIED = {
    ('assert.failed', 'assertion.false'):
        ('termination_check.failed', 'child_termination.not_implied')
}

OBLIGATION_MEASURE_NON_POSITIVE = {
    ('call.precondition', 'assertion.false'):
        ('call.precondition', 'obligation_measure.non_positive')
}
OBLIGATION_LOOP_TERMINATION_PROMISE_FAIL = {
    ('assert.failed', 'assertion.false'):
        ('leak_check.failed', 'must_terminate.loop_promise_not_kept')
}
OBLIGATION_CALL_LEAK_CHECK_FAIL = {
    ('call.precondition', 'assertion.false'):
        ('leak_check.failed', 'caller.has_unsatisfied_obligations')
}
OBLIGATION_BODY_LEAK_CHECK_FAIL = {
    ('postcondition.violated', 'assertion.false'):
        ('leak_check.failed', 'method_body.leaks_obligations')
}
OBLIGATION_LOOP_CONTEXT_LEAK_CHECK_FAIL = {
    ('invariant.not.established', 'assertion.false'):
        ('leak_check.failed', 'loop_context.has_unsatisfied_obligations')
}
OBLIGATION_LOOP_BODY_LEAK_CHECK_FAIL = {
    ('invariant.not.preserved', 'assertion.false'):
        ('leak_check.failed', 'loop_body.leaks_obligations')
}
OBLIGATION_LOOP_MEASURE_NON_POSITIVE = {
    ('invariant.not.established', 'assertion.false'):
        ('invariant.not.established', 'obligation_measure.non_positive'),
    ('invariant.not.preserved', 'assertion.false'):
        ('invariant.not.preserved', 'obligation_measure.non_positive'),
    ('not.wellformed', 'insufficient.permission'):
        ('not.wellformed', 'loop_condition.not_framed_for_obligation_use'),
}
LOCAL_VARIABLE_NOT_DEFINED = {
    ('application.precondition', 'assertion.false'):
        ('expression.undefined', 'undefined.local.variable')
}
GLOBAL_NAME_NOT_DEFINED = {
    ('application.precondition', 'assertion.false'):
        ('expression.undefined', 'undefined.global.name')
}
DEPENDENCIES_NOT_DEFINED = {
    ('application.precondition', 'assertion.false'):
        ('expression.undefined', 'missing.dependencies')
}
THREAD_CREATION_ARG_TYPE = {
    ('assert.failed', 'assertion.false'):
        ('thread.creation.failed', 'invalid.argument.type')
}
THREAD_CREATION_GROUP_NONE = {
    ('assert.failed', 'assertion.false'):
        ('thread.creation.failed', 'assertion.false')
}
THREAD_START_METHOD_UNLISTED = {
    ('assert.failed', 'assertion.false'):
        ('thread.start.failed', 'method.not.listed')
}
THREAD_START_PERMISSION = {
    ('exhale.failed', 'insufficient.permission'):
        ('thread.start.failed', 'missing.start.permission')
}
THREAD_START_PRECONDITION = {
    ('exhale.failed', 'insufficient.permission'):
        ('thread.start.failed', 'insufficient.permission'),
    ('inhale.failed', 'insufficient.permission'):
        ('thread.start.failed', 'insufficient.permission'),
    ('exhale.failed', 'assertion.false'):
        ('thread.start.failed', 'assertion.false')
}
THREAD_JOIN_WAITLEVEL = {
    ('assert.failed', 'assertion.false'):
        ('thread.join.failed', 'wait.level.invalid')
}
THREAD_JOIN_JOINABLE = {
    ('assert.failed', 'assertion.false'):
        ('thread.join.failed', 'thread.not.joinable')
}
INHALE_TO_CALL = {
    ('inhale.failed', 'insufficient.permission'):
        ('call.precondition', 'insufficient.permission')
}
LOCK_RELEASE_INVARIANT = {
    ('fold.failed', 'insufficient.permission'):
        ('lock.invariant.not.established', 'insufficient.permission'),
    ('fold.failed', 'assertion.false'):
        ('lock.invariant.not.established', 'assertion.false')
}
BRANCH_CONDITION_ASSERT = {
    ('assert.failed', 'assertion.false'):
        ('probabilistic.sif.violated', 'high.branch')
}
POSS_BRANCH_CONDITION_ASSERT = {
    ('assert.failed', 'assertion.false'):
        ('possibilistic.sif.violated', 'high.branch')
}
BRANCH_RECEIVER_LOW = {
    ('assert.failed', 'assertion.false'):
        ('probabilistic.sif.violated', 'high.receiver.type')
}
EXCEPTION_TYPE_LOW = {
    ('assert.failed', 'assertion.false'):
        ('probabilistic.sif.violated', 'high.exception.type')
}
SHORT_CIRCUIT_LOW = {
    ('assert.failed', 'assertion.false'):
        ('probabilistic.sif.violated', 'high.short.circuit')
}
COMPREHENSION_LOW = {
    ('assert.failed', 'assertion.false'):
        ('probabilistic.sif.violated', 'high.comprehension')
}

__all__ = (
    'Rules',
    'TERMINATION_CHECK_MEASURE_NON_POSITIVE',
    'TERMINATION_CHECK_MEASURE_NON_DECREASING',
    'TERMINATION_CHECK_GAP_ENABLED',
    'TERMINATION_CHECK_CHILD_TERMINATION_NOT_IMPLIED',
    'OBLIGATION_MEASURE_NON_POSITIVE',
    'OBLIGATION_LOOP_TERMINATION_PROMISE_FAIL',
    'OBLIGATION_CALL_LEAK_CHECK_FAIL',
    'OBLIGATION_BODY_LEAK_CHECK_FAIL',
    'OBLIGATION_LOOP_CONTEXT_LEAK_CHECK_FAIL',
    'OBLIGATION_LOOP_BODY_LEAK_CHECK_FAIL',
    'OBLIGATION_LOOP_MEASURE_NON_POSITIVE',
    'LOCAL_VARIABLE_NOT_DEFINED',
    'GLOBAL_NAME_NOT_DEFINED',
    'DEPENDENCIES_NOT_DEFINED',
    'BRANCH_CONDITION_ASSERT',
    'BRANCH_RECEIVER_LOW',
    'EXCEPTION_TYPE_LOW',
    'SHORT_CIRCUIT_LOW',
    'COMPREHENSION_LOW',
)
