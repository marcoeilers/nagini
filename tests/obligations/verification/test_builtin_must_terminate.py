from py2viper_contracts.contracts import (
    Assert,
    Requires,
    Invariant,
    Implies,
)
from py2viper_contracts.obligations import *


def test_list() -> None:
    Requires(MustTerminate(2))
    a = [1, 2, 3]
    a.append(4)
    a[3] = 2


def test_list2() -> None:
    Requires(MustTerminate(1))
    # TODO: Figure out how to have normal errors like
    # leak_check.failed:caller.has_unsatisfied_obligations for axiomatized methods
    # that have no position.
    #:: ExpectedOutput(call.precondition:assertion.false)
    a = [1, 2, 3]


def test_set() -> None:
    Requires(MustTerminate(2))
    a = {1, 2, 3}
    a.add(4)
    a.clear()


def test_dict() -> None:
    Requires(MustTerminate(2))
    a = {'a': 1, 'b': 2, 'c': 3}
    keys = a.keys()
    a['d'] = 4
    values = a.values()
