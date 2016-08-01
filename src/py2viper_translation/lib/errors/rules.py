"""Conversion rules from Silver level errors to py2viper errors."""


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
    ('assert.failed', 'assertion.false'):
        ('call.precondition', 'obligation_measure.non_positive')
}
OBLIGATION_MUST_TERMINATE_NOT_TAKEN = {
    ('assert.failed', 'assertion.false'):
        ('leak_check.failed', 'must_terminate.not_taken')
}
OBLIGATION_LOOP_TERMINATION_PROMISE_MISSING = {
    ('assert.failed', 'assertion.false'):
        ('leak_check.failed', 'must_terminate.loop_not_promised')
}
OBLIGATION_LOOP_TERMINATION_PROMISE_FAIL = {
    ('assert.failed', 'assertion.false'):
        ('leak_check.failed', 'must_terminate.loop_promise_not_kept')
}


__all__ = (
    'Rules',
    'TERMINATION_CHECK_MEASURE_NON_POSITIVE',
    'TERMINATION_CHECK_MEASURE_NON_DECREASING',
    'TERMINATION_CHECK_GAP_ENABLED',
    'TERMINATION_CHECK_CHILD_TERMINATION_NOT_IMPLIED',
    'OBLIGATION_MEASURE_NON_POSITIVE',
)
