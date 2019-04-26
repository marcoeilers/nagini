# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Sized


class Helper(Sized):
    @Pure
    def __str__(self) -> str:
        return 'asd'

    @Pure
    @ContractOnly
    def something(self) -> bool:
        pass

    @Pure
    @ContractOnly
    def something_else(self) -> int:
        pass

    @Pure
    def __len__(self) -> int:
        return self.something_else()

    @Pure
    def __bool__(self) -> bool:
        return self.something()


class Helper2:
    pass


def bool_object() -> None:
    h = Helper2()
    b = bool(h)
    b2 = bool(None)
    assert not b2
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False


def bool_override() -> None:
    h = Helper()
    b = bool(h)
    if h.something():
        assert b
    else:
        assert not b
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False


def str_object_override() -> None:
    h = Helper()
    h2 = Helper2()
    assert str(h) == 'asd'
    s2 = str(h2)
    assert isinstance(s2, str)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert s2 == 'Hello'


def len_override() -> None:
    h = Helper()
    l = len(h)
    assert l == h.something_else()
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False
