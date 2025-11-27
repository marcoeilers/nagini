# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def client() -> None:
    #:: ExpectedOutput(invalid.program:invalid.reveal.no.function)
    a = Reveal(1 + 2)

