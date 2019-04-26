# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    ContractOnly,
    Ensures,
    Requires,
    Result,
)
from nagini_contracts.io_contracts import *
from nagini_contracts.obligations import (
    MustTerminate,
)
from verifast.stdio_simple import (
    putchar,
)

from verifast.user_sets_contract.specification import (
    example_io,
    Interface,
)


class Implementation(Interface):

    def main(self, t1: Place) -> Place:
        IOExists1(Place)(
            lambda t2: (
                Requires(
                    token(t1, 2) and
                    example_io(t1, t2) and
                    MustTerminate(2)
                ),
                Ensures(
                    token(t2) and
                    t2 == Result()
                ),
            )
        )
        Open(example_io(t1))
        success, t2 = putchar('h', t1)
        success, t3 = putchar('i', t2)
        return t3
