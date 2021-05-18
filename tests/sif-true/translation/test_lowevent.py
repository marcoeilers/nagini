# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

def precond_ok() -> None:
    Requires(LowEvent())

def postcond_not_ok() -> None:
    #:: ExpectedOutput(invalid.program:invalid.contract.position)
    Ensures(LowEvent())
