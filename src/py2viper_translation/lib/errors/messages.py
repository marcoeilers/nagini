"""Conversion of errors to human readable messages."""


from py2viper_translation.lib.util import (
    get_containing_member,
    get_target_name,
    pprint,
)


ERRORS = {
    'assignment.failed':
        lambda n: 'Assignment might fail.',
    'call.failed':
        lambda n: 'Method call might fail.',
    'not.wellformed':
        lambda n: 'Contract might not be well-formed.',
    'call.precondition':
        lambda n: ('The precondition of method {} might not '
                   'hold.').format(get_target_name(n)),
    'application.precondition':
        lambda n: ('Precondition of function {} might not '
                   'hold.').format(get_target_name(n)),
    'exhale.failed':
        lambda n: 'Exhale might fail.',
    'inhale.failed':
        lambda n: 'Inhale might fail.',
    'if.failed':
        lambda n: 'Conditional statement might fail.',
    'while.failed':
        lambda n: 'While statement might fail.',
    'assert.failed':
        lambda n: 'Assert might fail.',
    'postcondition.violated':
        lambda n: ('Postcondition of {} might not '
                   'hold.').format(get_containing_member(n).name),
    'fold.failed':
        lambda n: 'Fold might fail.',
    'unfold.failed':
        lambda n: 'Unfold might fail.',
    'invariant.not.preserved':
        lambda n: 'Loop invariant might not be preserved.',
    'invariant.not.established':
        lambda n: 'Loop invariant might not hold on entry.',
    'function.not.wellformed':
        lambda n: ('Function {} might not be '
                   'well-formed.').format(get_containing_member(n).name),
    'predicate.not.wellformed':
        lambda n: ('Predicate {} might not be '
                   'well-formed.').format(get_containing_member(n).name),
    'termination_check.failed':
        lambda n: 'Operation might not terminate.',
}

REASONS = {
    'assertion.false':
        lambda n: 'Assertion {} might not hold.'.format(pprint(n)),
    'receiver.null':
        lambda n: 'Receiver of {} might be null.'.format(pprint(n)),
    'division.by.zero':
        lambda n: 'Divisor {} might be zero.'.format(pprint(n)),
    'negative.permission':
        lambda n: 'Fraction {} might be negative.'.format(pprint(n)),
    'insufficient.permission':
        lambda n: ('There might be insufficient permission to '
                   'access {}.').format(pprint(n)),
    'measure.non_positive':
        lambda n: ('Termination measure {} might be '
                   'non-positive.').format(pprint(n)),
    'measure.non_decreasing':
        lambda n: ('Termination measure of {} might be not '
                   'smaller.').format(pprint(n)),
    'gap.enabled':
        lambda n: ('Gap {} might be enabled in terminating IO '
                   'operation.').format(pprint(n)),
    'child_termination.not_implied':
        lambda n: ('Parent IO operation termination condition does not '
                   'imply {} termination condition.').format(pprint(n)),
}
