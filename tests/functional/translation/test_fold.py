# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import Fold


def client() -> None:
    #:: ExpectedOutput(invalid.program:invalid.contract.call)
    Fold(True)