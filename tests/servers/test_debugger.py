"""
Copyright (c) 2026 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""


"""Integration tests for the verification debugger.

They drive a session through the same commands the IDE sends, and check that
what comes back is phrased in Python: the expressions the user wrote, not the
Viper encoding they were translated to.

A session keeps a prover and the symbolic state of a failed verification alive,
so each test closes the one it started. Run them with::

    pytest tests/servers/test_debugger.py
"""


import pytest


# `b` is never constrained, so the postcondition does not follow. Both branches
# assign to `c`, which gives the debugger something to show for either path.
DEBUG_SRC = (
    "from nagini_contracts.contracts import *\n\n"
    "def bar(a: int, b: int) -> int:\n"
    "    Requires(a >= 0)\n"
    "    Ensures(Result() > b)\n"
    "    if b < 0:\n"
    "        c = a - b\n"
    "    else:\n"
    "        c = a + b\n"
    "    return c\n"
)


@pytest.fixture
def debug_file(tmp_path):
    path = tmp_path / "debug_example.py"
    path.write_text(DEBUG_SRC)
    return str(path)


@pytest.fixture
def session(service, debug_file):
    """A debug session opened on the only failure of ``debug_file``."""
    started = service.debug('start', file=debug_file)
    if not started['ok']:
        pytest.skip("Debug session unavailable: {}".format(started.get('error')))
    assert started['failures'], started
    assert service.debug('selectFailure', index=0)['ok']
    yield service
    service.debug('stop')


def test_start_reports_the_python_level_failure(service, debug_file):
    started = service.debug('start', file=debug_file)
    if not started['ok']:
        pytest.skip("Debug session unavailable: {}".format(started.get('error')))
    try:
        failures = started['failures']
        assert len(failures) == 1, failures
        assert failures[0]['message'] == 'Result() > b'
        assert failures[0]['member'] == 'bar'
        assert failures[0]['debuggable']
    finally:
        service.debug('stop')


def test_obligation_has_the_shape_clients_expect(session):
    """Every key a client reads must be present on every node.

    The proof goal and the assumptions are rendered by the same code and are
    treated identically by clients, so they have to have the same shape; a node
    missing its (possibly empty) list of children breaks a client that walks the
    tree without checking.
    """
    obligation = session.debug('selectFailure', index=0)['obligation']
    for key in ('error', 'member', 'assertion', 'store', 'branchConditions',
                'assumptions'):
        assert key in obligation, key
    for key in ('store', 'branchConditions', 'assumptions'):
        assert isinstance(obligation[key], list), key

    def check(node):
        for key in ('id', 'python', 'kind', 'position', 'description', 'viper',
                    'internal', 'children'):
            assert key in node, (key, node)
        assert isinstance(node['children'], list), node
        for child in node['children']:
            check(child)

    check(obligation['assertion'])
    for assumption in obligation['assumptions']:
        check(assumption)


def test_obligation_is_phrased_in_python(session):
    result = session.debug('prove')
    assert result['ok'] and result['proved'] is False
    obligation = result['obligation']

    assert obligation['member'] == 'bar'
    assert obligation['assertion']['python'] == 'Result() > b'

    # The else branch was taken, so the condition must be reported negated;
    # Silicon builds that negation with the position of the condition itself,
    # which would otherwise make it read as the then branch.
    conditions = [bc['condition'] for bc in obligation['branchConditions']]
    assert conditions == ['not (b < 0)'], conditions

    # The precondition and the assignment, as written.
    assumptions = [a['python'] for a in obligation['assumptions']]
    assert 'a >= 0' in assumptions, assumptions
    assert 'c == a + b' in assumptions, assumptions

    # Nothing built purely from the encoding may surface.
    for assumption in obligation['assumptions']:
        text = assumption['python'] or ''
        assert '_isDefined' not in text
        assert 'issubtype' not in text
        assert '__prim__' not in text


def test_store_uses_python_names(session):
    obligation = session.debug('prove')['obligation']
    store = {e['variable']: e for e in obligation['store'] if not e['internal']}

    assert 'Result()' in store, store
    assert 'c' in store, store
    # A parameter appears twice: the value it was called with, and the local
    # copy the body may assign to.
    assert 'a' in store and 'a (on entry)' in store, store
    # The error variable is part of the encoding, not of the program.
    assert '_err' not in store

    # The store maps variables to symbolic values, which have no Python form of
    # their own; what a variable was assigned is a fact about it, and appears
    # among the assumptions. (Silicon does give the symbol it introduces for an
    # assignment the source position of the right-hand side, so reading the
    # value off the position would look like it works -- and would be wrong as
    # soon as a symbol borrows a position from something unrelated.)
    assert all(e['value'] is None for e in store.values()), store
    assert 'c == a + b' in [a['python'] for a in obligation['assumptions']]


def test_assert_evaluates_python_expressions(session):
    # Follows from the branch condition.
    assert session.debug('assert', expression='b >= 0')['proved'] is True
    # Does not: the precondition only says `a >= 0`.
    assert session.debug('assert', expression='a > 0')['proved'] is False


def test_assumption_makes_the_obligation_provable(session):
    assert session.debug('prove')['proved'] is False
    assert session.debug('addAssumption', expression='a > 0', free=True)['ok']
    assert session.debug('prove')['proved'] is True
    assert session.debug('reset')['ok']
    assert session.debug('prove')['proved'] is False


def test_bad_input_is_reported_not_raised(session):
    unknown = session.debug('assert', expression='no_such_name')
    assert not unknown['ok']
    assert 'no_such_name' in unknown['error']

    invalid = session.debug('assert', expression='a +')
    assert not invalid['ok']
    assert 'valid Python expression' in invalid['error']

    unknown_command = session.debug('nonsense')
    assert not unknown_command['ok']


# A method that assigns to its parameter: the same Python name then stands for
# several values, which is what forces them to be told apart when shown.
REASSIGNING_SRC = (
    "from nagini_contracts.contracts import *\n\n"
    "def incr(x: int) -> int:\n"
    "    Requires(x >= 0)\n"
    "    Ensures(Result() > x + 5)\n"
    "    x += 2\n"
    "    x += 3\n"
    "    return x\n"
)


@pytest.fixture
def reassigning_session(service, tmp_path):
    path = tmp_path / "reassigning.py"
    path.write_text(REASSIGNING_SRC)
    started = service.debug('start', file=str(path))
    if not started['ok']:
        pytest.skip("Debug session unavailable: {}".format(started.get('error')))
    assert service.debug('selectFailure', index=0)['ok']
    yield service
    service.debug('stop')


def test_values_from_different_points_are_distinguished(reassigning_session):
    """`x += 2` must not be reported as `x == x + 2`, which is unsatisfiable.

    The recorded assumption is phrased over the variables of the program, where
    both sides are called `x`; only the evaluated form distinguishes the value
    before the assignment from the value after it.
    """
    obligation = reassigning_session.debug('prove')['obligation']
    assumptions = [a['python'] for a in obligation['assumptions']]
    assert not any(a == 'x == x + 2' for a in assumptions), assumptions

    # Every variable in an expression that spans two points is marked, so that
    # no name in it looks more current than the others.
    increments = [a for a in assumptions if a and '+ 2' in a]
    assert increments, assumptions
    assert increments[0].count('@') == 2, increments

    # The store says which value the plain name stands for now, which is what
    # makes the marks readable.
    store = {e['variable']: e for e in obligation['store'] if not e['internal']}
    assert store['x']['holds'] != store['x (on entry)']['holds'], store


def test_no_version_marks_when_nothing_was_reassigned(session):
    """The common case must not be cluttered with them."""
    assumptions = [a['python'] for a in
                   session.debug('prove')['obligation']['assumptions']]
    assert 'a >= 0' in assumptions, assumptions
    assert all('@' not in (a or '') for a in assumptions), assumptions


def test_added_assumption_is_shown_and_uses_the_current_value(reassigning_session):
    """A user's assumption must appear, and be about `x` as it is now.

    Nagini copies a parameter into a local that the body assigns to; without
    that alias an expression about `x` would constrain the value on entry.
    """
    added = reassigning_session.debug('addAssumption', expression='x > 100', free=True)
    assert added['ok'], added
    obligation = added['obligation']

    assumptions = [a['python'] for a in obligation['assumptions']]
    assert 'x > 100' in assumptions, assumptions

    # It has to be the value `x` stands for now, not the one on entry.
    store = {e['variable']: e for e in obligation['store'] if not e['internal']}
    added_node = next(a for a in obligation['assumptions'] if a['python'] == 'x > 100')
    assert store['x']['holds'] in added_node['viper'], added_node
    assert store['x (on entry)']['holds'] not in added_node['viper'], added_node


def test_an_equality_between_declared_variables_is_not_internal(session):
    """`Result() == c` is a fact about two variables the user declared.

    Nagini guards every read of a local with a definedness check, and that
    wrapper must not make the assumption look like pure encoding.
    """
    assumptions = [a['python'] for a in
                   session.debug('prove')['obligation']['assumptions']]
    assert 'Result() == c' in assumptions, assumptions


# Indexing, `len`, a field read and a reassigned parameter in one method: the
# encoding of all of these has to be recognisable again as what was written.
OPERATORS_SRC = (
    "from nagini_contracts.contracts import *\n"
    "from typing import List\n\n"
    "class Cell:\n"
    "    def __init__(self, value: int) -> None:\n"
    "        self.value = value\n\n"
    "def foo(i1: int, i2: int, c: Cell, l: List[int]) -> int:\n"
    "    Requires(Acc(c.value) and list_pred(l))\n"
    "    Ensures(Result() > 18)\n"
    "    Assume(len(l) > 0 and l[0] > 0)\n"
    "    i2 += 2\n"
    "    if i1 == i2 and c.value > 0:\n"
    "        Assert(i1 is i2)\n"
    "    return 4\n"
)


@pytest.fixture
def operators_session(service, tmp_path):
    path = tmp_path / "operators.py"
    path.write_text(OPERATORS_SRC)
    started = service.debug('start', file=str(path))
    if not started['ok']:
        pytest.skip("Debug session unavailable: {}".format(started.get('error')))
    debuggable = [f for f in started['failures'] if f['debuggable']]
    if not debuggable:
        pytest.skip("Nothing debuggable in this program.")
    assert service.debug('selectFailure', index=debuggable[0]['index'])['ok']
    yield service
    service.debug('stop')


def test_python_operators_are_written_as_python(operators_session):
    """Nagini encodes operators as functions; they have to read as operators.

    `len(l)` becomes `list___len__(l)` and `l[0]` becomes
    `list___getitem__(l, 0)`, and an expression the verifier composed is not
    matched verbatim, so these are rebuilt from their parts.
    """
    assumptions = [a['python'] for a in
                   operators_session.debug('prove')['obligation']['assumptions']]
    joined = ' | '.join(a or '' for a in assumptions)
    assert 'len(l) > 0' in joined, assumptions
    assert 'l[0] > 0' in joined, assumptions
    assert 'c.value' in joined, assumptions
    # None of the generated names may reach the user.
    for name in ('__len__', '__getitem__', 'len__(', 'getitem__(', '__prim__'):
        assert name not in joined, (name, assumptions)


def test_only_the_parts_that_moved_are_marked(operators_session):
    """A version mark on a variable that did not change would be noise.

    Only `i2` is reassigned, so only the assumption about `i2` carries marks;
    the branch condition mentions `i1`, `i2` and `c.value` and is the user's own
    words, which stay untouched.
    """
    assumptions = [a['python'] for a in
                   operators_session.debug('prove')['obligation']['assumptions']]
    assert 'i1 == i2 and c.value > 0' in assumptions, assumptions
    marked = [a for a in assumptions if a and '@' in a]
    assert marked, assumptions
    assert all('i2' in a for a in marked), marked


def test_a_type_assumption_the_user_asked_for_is_shown(operators_session):
    """Facts about the encoding are hidden -- unless the user asked for one.

    `type(i1) == int` is a fact about Nagini's type domain, which is exactly
    what the filter removes; suppressing it here would look as though the
    request had been ignored.
    """
    added = operators_session.debug('addAssumption', expression='type(i1) == int',
                                    free=True)
    assert added['ok'], added
    mine = [a for a in added['obligation']['assumptions'] if a.get('added')]
    assert len(mine) == 1, added['obligation']['assumptions']
    assert 'type(i1)' in mine[0]['python'], mine
    assert 'int' in mine[0]['python'], mine


def test_added_assumptions_are_marked_and_forgotten_on_reset(session):
    added = session.debug('addAssumption', expression='a > 0', free=True)
    assert added['ok'], added
    assert [a['python'] for a in added['obligation']['assumptions'] if a.get('added')] \
        == ['a > 0']
    after_reset = session.debug('reset')
    assert not any(a.get('added') for a in after_reset['obligation']['assumptions'])


FIELD_SRC = (
    "from nagini_contracts.contracts import *\n\n"
    "class Cell:\n"
    "    def __init__(self, value: int) -> None:\n"
    "        self.value = value\n\n"
    "def bump(c: Cell) -> int:\n"
    "    Requires(Acc(c.value) and c.value > 0)\n"
    "    Ensures(Result() > 18)\n"
    "    c.value -= 8\n"
    "    Assert(c.value > 0)\n"
    "    return 4\n"
)


@pytest.fixture
def field_session(service, tmp_path):
    path = tmp_path / "field.py"
    path.write_text(FIELD_SRC)
    started = service.debug('start', file=str(path))
    if not started['ok']:
        pytest.skip("Debug session unavailable: {}".format(started.get('error')))
    debuggable = [f for f in started['failures'] if f['debuggable']]
    if not debuggable:
        pytest.skip("Nothing debuggable in this program.")
    assert service.debug('selectFailure', index=debuggable[0]['index'])['ok']
    yield service
    service.debug('stop')


def test_the_heap_says_which_permissions_are_held(field_session):
    heap = [e for e in field_session.debug('prove')['obligation']['heap']
            if not e['internal']]
    locations = [e['location'] for e in heap]
    assert 'c.value' in locations, heap
    entry = next(e for e in heap if e['location'] == 'c.value')
    assert entry['permission'] == 'write', entry
    # A field holds a value, and naming it is what makes an assumption about
    # the field readable; a predicate's snapshot is not worth showing.
    assert entry['holds'], entry


def test_a_field_value_is_named_after_the_object_it_belongs_to(field_session):
    """The verifier calls it `Cell_value@k`, which says nothing about whose.

    Only the heap relates that symbol to `c`, so an assumption about it can
    only be phrased once the heap has been consulted.
    """
    assumptions = [a['python'] for a in
                   field_session.debug('prove')['obligation']['assumptions']]
    joined = ' | '.join(a or '' for a in assumptions)
    assert 'Cell_value' not in joined, assumptions
    # Not a bare `.value` either, which is what it used to render as.
    assert '.value' not in joined.replace('c.value', ''), assumptions


def test_two_values_of_one_field_are_told_apart(field_session):
    """`c.value -= 8` refers to the value before and after on the same line.

    Saying which line the state was taken at is the only thing that
    distinguishes them, so it cannot be left out here -- even though on most
    expressions that label says nothing and is left out.
    """
    assumptions = [a['python'] for a in
                   field_session.debug('prove')['obligation']['assumptions']]
    decrement = [a for a in assumptions if a and '- 8' in a]
    assert decrement, assumptions
    # Unmarked it would read `c.value == c.value - 8`, which is unsatisfiable.
    assert decrement[0] != 'c.value == c.value - 8', decrement
    left, _, right = decrement[0].partition(' == ')
    assert left != right.replace(' - 8', ''), decrement
    assert '@line' in right, decrement


IDENTITY_SRC = (
    "from nagini_contracts.contracts import *\n\n"
    "class Cell:\n"
    "    def __init__(self, value: int) -> None:\n"
    "        self.value = value\n\n"
    "def same(a: Cell, b: Cell) -> int:\n"
    "    Requires(Acc(a.value) and Acc(b.value))\n"
    "    Ensures(Result() > 18)\n"
    "    Assert(a is b)\n"
    "    return 4\n"
)


def test_the_goal_keeps_the_words_it_was_written_with(service, tmp_path):
    """`a is b` must not be reported as `a == b`.

    Nagini translates both to the same Viper node, so the distinction survives
    only in what the program says. The verifier records the failed goal in both
    its original and its evaluated form, and it is the original that still
    matches what Nagini built -- so the goal is recognised rather than rebuilt,
    and comes back in the user's own words.
    """
    path = tmp_path / "identity.py"
    path.write_text(IDENTITY_SRC)
    started = service.debug('start', file=str(path))
    if not started['ok']:
        pytest.skip("Debug session unavailable: {}".format(started.get('error')))
    try:
        assertion = None
        for failure in started['failures']:
            if not failure['debuggable']:
                continue
            obligation = service.debug('selectFailure', index=failure['index'])['obligation']
            if 'is' in (obligation['assertion']['python'] or ''):
                assertion = obligation['assertion']
                break
        assert assertion is not None, started['failures']
        assert assertion['python'] == 'a is b', assertion
        # Recognised, not reconstructed.
        assert assertion['kind'] == 'source', assertion
    finally:
        service.debug('stop')


def test_commands_need_a_session(service):
    service.debug('stop')
    result = service.debug('prove')
    assert not result['ok']
    assert 'no debug session' in result['error']
