# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import Requires, Predicate
from nagini_contracts.io_contracts import *


@Predicate
def foo() -> bool:
    #:: ExpectedOutput(invalid.program:invalid.io_operation.misplaced_property)
    Terminates(False)
