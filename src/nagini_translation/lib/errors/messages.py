"""Conversion of errors to human readable messages."""


from nagini_translation.lib.util import (
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
    'leak_check.failed':
        lambda n: 'Obligation leak check failed.',
    'internal':
        lambda n: 'An internal error occurred.',
    'expression.undefined':
        lambda n: 'Expression {} may not be defined.'.format(pprint(n)),
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
    'termination_measure.non_positive':
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
    'obligation_measure.non_positive':
        lambda n: ('Obligation {} measure might be '
                   'non-positive.').format(pprint(n)),
    'must_terminate.not_taken':
        lambda n: ('Callee {} might not take MustTerminate '
                   'obligation.').format(get_target_name(n)),
    'must_terminate.loop_not_promised':
        lambda n: ('Loop might not promise to terminate.'),
    'must_terminate.loop_promise_not_kept':
        lambda n: ('Loop might not keep promise to terminate.'),
    'caller.has_unsatisfied_obligations':
        lambda n: ('Callee {} might not take all unsatisfied obligations '
                   'from the caller.'.format(get_target_name(n))),
    'method_body.leaks_obligations':
        lambda n: ('Method {} body might leak '
                   'obligations.'.format(get_target_name(n))),
    'loop_context.has_unsatisfied_obligations':
        lambda n: ('Loop might not take all unsatisfied obligations '
                   'from the context.'),
    'loop_body.leaks_obligations':
        lambda n: ('Loop body might leak obligations.'),
    'loop_condition.not_framed_for_obligation_use':
        lambda n: ('Loop condition part {} is not framed at the point where '
                   'obligation is used.'.format(pprint(n))),
    'undefined.local.variable':
        lambda n: 'Local variable may not have been defined.',
    'undefined.global.name':
        lambda n: 'Global name may not have been defined.',
    'missing.dependencies':
        lambda n: 'Global dependencies may not be defined.'
}
