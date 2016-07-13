from py2viper_translation.lib.util import (
    get_containing_member,
    get_target_name,
    pprint,
)


ERRORS = {
    'assignment.failed': lambda n: 'Assignment might fail.',
    'call.failed': lambda n: 'Method call might fail.',
    'not.wellformed': lambda n: 'Contract might not be well-formed.',
    'call.precondition':
        lambda n: 'The precondition of method ' + get_target_name(n) +
                  ' might not hold.',
    'application.precondition':
        lambda n: 'Precondition of function ' + get_target_name(n) +
                  ' might not hold.',
    'exhale.failed': lambda n: 'Exhale might fail.',
    'inhale.failed': lambda n: 'Inhale might fail.',
    'if.failed': lambda n: 'Conditional statement might fail.',
    'while.failed': lambda n: 'While statement might fail.',
    'assert.failed': lambda n: 'Assert might fail.',
    'postcondition.violated':
        lambda n: 'Postcondition of ' + get_containing_member(n).name +
                  ' might not hold.',
    'fold.failed': lambda n: 'Fold might fail.',
    'unfold.failed': lambda n: 'Unfold might fail.',
    'invariant.not.preserved':
        lambda n: 'Loop invariant might not be preserved.',
    'invariant.not.established':
        lambda n: 'Loop invariant might not hold on entry.',
    'function.not.wellformed':
        lambda n: 'Function ' + get_containing_member(n).name +
                  ' might not be well-formed.',
    'predicate.not.wellformed':
        lambda n: 'Predicate ' + get_containing_member(n).name +
                  ' might not be well-formed.',
    'termination_check.failed':
        lambda n: 'Operation might not terminate.',
}

REASONS = {
    'assertion.false': lambda n: 'Assertion ' + pprint(n) + ' might not hold.',
    'receiver.null': lambda n: 'Receiver of ' + pprint(n) + ' might be null.',
    'division.by.zero': lambda n: 'Divisor ' + pprint(n) + ' might be zero.',
    'negative.permission':
        lambda n: 'Fraction ' + pprint(n) + ' might be negative.',
    'insufficient.permission':
        lambda n: 'There might be insufficient permission to access ' +
                  pprint(n) + '.',
    'measure.non_positive':
        lambda n: 'Termination measure {} might be non-positive.'.format(
            pprint(n)),
    'measure.non_decreasing':
        lambda n: 'Termination measure of {} might be not smaller.'.format(
            pprint(n)),
    'gap.enabled':
        lambda n: 'Gap {} might be enabled in terminating IO operation.'.format(
            pprint(n)),
    'child_termination.not_implied':
        lambda n: ('Parent IO operation termination condition does not '
                   'imply {} termination condition.').format(
            pprint(n)),
}
