# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import Ensures, Implies
from nagini_contracts.io_contracts import *


class C:

    def __init__(self) -> None:
        self.f = 1
        self.g = 2


def test(b: bool, x: C) -> Place:
    IOExists1(int)(
        lambda value: (
        Ensures(
            #:: ExpectedOutput(invalid.program:io_existential_var.use_of_undefined)
            (value == x.f if b else value == x.g) and
            value == 2
        ),
        )
    )
