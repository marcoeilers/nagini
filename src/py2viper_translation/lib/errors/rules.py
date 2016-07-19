"""Conversion rules from Silver level errors to py2viper errors."""


from typing import Dict, Tuple


class Rules(Dict[Tuple[str, str], Tuple[str, str]]):
    """Error conversion rules."""


TERMINATION_CHECK_MEASURE_NON_POSITIVE = {
    ('assert.failed', 'assertion.false'):
        ('termination_check.failed', 'measure.non_positive')
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


__all__ = (
    'Rules',
    'TERMINATION_CHECK_MEASURE_NON_POSITIVE',
    'TERMINATION_CHECK_MEASURE_NON_DECREASING',
    'TERMINATION_CHECK_GAP_ENABLED',
    'TERMINATION_CHECK_CHILD_TERMINATION_NOT_IMPLIED',
)
