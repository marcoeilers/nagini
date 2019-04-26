# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import Result
from nagini_contracts.io_contracts import *


def foo(x: None) -> None:
    pass


@IOOperation
def read_int_io(
        t_pre: Place,
        result: int = Result(),
        t_post: Place = Result(),
        ) -> bool:
    #:: ExpectedOutput(type.error:"Terminates" does not return a value)
    foo(Terminates(result > 0))
