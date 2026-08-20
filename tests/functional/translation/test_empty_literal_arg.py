# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def takes_obj(o: object) -> None:
    pass


def uninferable() -> None:
    # The callee's parameter gives no element type for the empty literal.
    #:: ExpectedOutput(invalid.program:generic.constructor.without.type)
    takes_obj([])
