# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.io_contracts import *


def read_int_io(t_pre: Place) -> bool:
    return True


def test(t1: Place) -> None:

    #:: ExpectedOutput(invalid.program:invalid.get_ghost_output.argument_not_io_operation)
    t3 = GetGhostOutput(read_int_io(t1), 't_post')  # type: Place
