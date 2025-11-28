# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def test() -> None:
    r = [1, 2]
    #:: ExpectedOutput(type.error:Name "foo" is not defined)
    Requires(Forall(r, lambda x: (foo(x), [])))
