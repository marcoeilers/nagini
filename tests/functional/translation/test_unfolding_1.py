# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import Unfolding


def client() -> None:
    #:: ExpectedOutput(invalid.program:invalid.contract.call)
    a = Unfolding(True, 45)