# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.thread import getMethod, Thread
from nagini_contracts.contracts import *


@Pure
def get_two(o: object) -> bool:
    return True


def test(o: Thread) -> None:
    #:: ExpectedOutput(invalid.program:invalid.get.method.use)
    Requires(get_two(getMethod(o)))
    pass