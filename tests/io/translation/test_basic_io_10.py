# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import Result
from nagini_contracts.io_contracts import *


@IOOperation #:: ExpectedOutput(type.error:Encountered Any type. Type annotation missing?)


def read_int_io(
        t_pre: Place,
        result: int = Result(),
        t_post: Place = Result(),
        ):
    Terminates(False)
