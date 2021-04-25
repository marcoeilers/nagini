"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Conversion of errors to human readable messages."""

import ast
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
                   'hold.'.format(get_target_name(n))
                   if isinstance(n, (ast.Call, ast.FunctionDef)) else
                   'The precondition of {} might not hold.'.format(pprint(n))),
    'application.precondition':
        lambda n: ('The precondition of function {} might not '
                   'hold.'.format(get_target_name(n))
                   if isinstance(n, (ast.Call, ast.FunctionDef)) else
                   'The precondition of {} might not hold.'.format(pprint(n))),
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
    'thread.creation.failed':
        lambda n: 'Thread creation may fail.',
    'thread.start.failed':
        lambda n: 'Thread start may fail.',
    'thread.join.failed':
        lambda n: 'Thread join may fail.',
    'termination_channel_check.failed':
        lambda n: 'Termination channel might exist.',
    'lock.invariant.not.established':
        lambda n: 'Lock invariant might not hold.',
    'probabilistic.sif.violated':
        lambda n: 'Probabilistic non-interference might not be satisfied.',
    'possibilistic.sif.violated':
        lambda n: 'Possibilistic non-interference might not be satisfied.'
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
        lambda n: ('Body of method {} might leak '
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
        lambda n: 'Global dependencies may not be defined.',
    'internal':
        lambda n: 'Internal Viper error.',
    'receiver.not.injective':
        lambda n: 'Receiver expression of quantified permission is not injective.',
    'wait.level.invalid':
        lambda n: 'Thread level may not be lower than current thread.',
    'thread.not.joinable':
        lambda n: 'Thread may not be joinable.',
    'invalid.argument.type':
        lambda n: 'Thread argument may not fit target method parameter type.',
    'method.not.listed':
        lambda n: "Thread's target method may not be listed in start statement.",
    'missing.start.permission':
        lambda n: 'May not have permission to start thread.',
    'sif.fold':
        lambda n: 'The low parts of predicate {} might not hold.'.format(
            get_target_name(n.args[0]) if n.args else 'lock invariant'),
    'sif.unfold':
        lambda n: 'The low parts of predicate {} might not hold.'.format(
            get_target_name(n.args[0])),
    'sif_termination.condition_not_low':
        lambda n: 'Termination condition {} might not be low.'.format(pprint(n.args[0])),
    'sif_termination.not_lowevent':
        lambda n: ('Termination condition {} evaluating to false might not imply that '
                   'both executions don\'t terminate.').format(pprint(n.args[0])),
    'sif_termination.condition_not_tight':
        lambda n: 'Termination condition {} might not be tight.'.format(pprint(n.args[0])),
    'concurrency.in.sif':
        lambda n: 'Concurrency (thread and lock operations) is not allowed in noninterference mode.',
    'missing.termination.annotation':
        lambda n: 'Function and loop termination must be proved to be low in possibilistic noninterference mode. '
                  'Use TerminatesSif(...) as the last precondition/loop invariant.',
    'high.branch':
        lambda n: 'Branch condition {} might not be low or reaching the loop might not be a low event.'.format(pprint(n)),
    'high.receiver.type':
        lambda n: 'Type of call receiver {} might not be low.'.format(pprint(n)),
    'high.exception.type':
        lambda n: 'Type of raised exception {} might not be low.'.format(pprint(n)),
    'high.short.circuit':
        lambda n: 'Short-circuiting behavior of expression {} might not be low.'.format(pprint(n)),
    'high.comprehension':
        lambda n: 'Comprehension {} might introduce high control flow'.format(pprint(n)),
}

VAGUE_REASONS = {
    'assertion.false': '',
    'receiver.null': 'Receiver might be null.',
    'division.by.zero': 'Divisor might be zero.',
    'negative.permission': 'Fraction might be negative.',
    'insufficient.permission': 'There might be insufficient permission.',
    'termination_measure.non_positive': 'Termination measure might be non-positive.',
    'measure.non_decreasing': 'Termination measure might not be smaller.',
    'gap.enabled': 'Gap might be enabled in terminating IO operation.',
    'child_termination.not_implied': ('Parent IO operation termination condition does '
                                      'not imply termination condition.'),
    'obligation_measure.non_positive': 'Obligation measure might be non-positive.',
    'must_terminate.not_taken': 'Callee might not take MustTerminate obligation.',
    'caller.has_unsatisfied_obligations': ('Callee might not take all unsatisfied '
                                           'obligations from the caller.'),
    'method_body.leaks_obligations': 'Method body might leak obligations.',
    'loop_condition.not_framed_for_obligation_use': ('Loop condition part is not framed '
                                                     'at the point where obligation is '
                                                     'used.'),
}
