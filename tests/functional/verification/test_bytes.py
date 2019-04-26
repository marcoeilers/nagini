# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def m() -> None:
    a = b"0aA"
    b = a + b'qwe'
    assert b == b'0aAqwe'
    assert b[3] == 113
    if not a:
        assert False
    c = b'as' * 2
    assert b'as' * 1 == b'as'
    assert len(c) == 4
    assert c == b'asas'
    ds = [b'asd', b'ASD', b'asdASD007']
    d = b''.join(ds)
    assert len(d) == 15
    d2 = b'well'.join(ds)
    assert len(d2) == 23
    assert d2[2] == 100
    assert d2[3] == 119
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False