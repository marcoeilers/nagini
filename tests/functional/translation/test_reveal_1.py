# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

def foo() -> int:
    return 34


def client() -> None:
    #:: ExpectedOutput(invalid.program:invalid.reveal.no.pure.function)
    a = Reveal(foo())

