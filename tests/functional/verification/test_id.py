# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class A:
    pass


def test_id_consistent_with_is(x: A, y: A) -> None:
    assert id(x) == id(x)
    if x is y:
        assert id(x) == id(y)
    if id(x) == id(y):
        assert x is y
    if x is not y:
        assert id(x) != id(y)


def test_id_in_postcondition(x: A, y: A) -> bool:
    Ensures(Result() == (x is y))
    return id(x) == id(y)


def test_id_in_precondition(x: A, y: A) -> None:
    Requires(id(x) != id(y))
    assert x is not y


@Pure
def get_id(x: A) -> int:
    return id(x)


def test_id_in_pure_function(x: A, y: A) -> None:
    if get_id(x) != get_id(y):
        assert x is not y


def test_id_stored_in_locals(x: A, y: A) -> None:
    a = id(x)
    b = id(y)
    if a == b:
        assert x is y


def test_id_of_literals() -> None:
    assert id(None) == id(None)
    b = id(True)
    n = id(5)
    assert b == id(True)


def test_id_of_fresh_object(x: A) -> None:
    y = A()
    assert id(y) != id(x)


def test_id_unaffected_by_heap_changes(x: A) -> None:
    a = id(x)
    y = A()
    assert a == id(x)
    assert Old(id(x)) == id(x)


def test_id_in_invariant(x: A) -> None:
    i = 0
    while i < 5:
        Invariant(id(x) == id(x))
        i += 1


def test_id_not_equal(x: A, y: A) -> None:
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert id(x) == id(y)
