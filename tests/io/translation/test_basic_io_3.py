# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import Requires, Predicate
from nagini_contracts.io_contracts import *


@IOOperation        #:: ExpectedOutput(invalid.program:invalid.io_operation.kwarg)
def read_int_io(**kwarg) -> bool:
    Terminates(False)
