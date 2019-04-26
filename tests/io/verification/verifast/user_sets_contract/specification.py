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
    stdout,
    write_char_io,
)


@IOOperation
def example_io(
        t_pre: Place,
        t_post: Place = Result()) -> bool:
    Terminates(True)
    TerminationMeasure(2)
    return IOExists3(Place, bool, bool)(
        lambda t2, success1, success2: (
            write_char_io(t_pre, stdout, 'h', success1, t2) and
            write_char_io(t2, stdout, 'i', success2, t_post)
        )
    )


class Interface:

    # TODO This method should be abstract, but currently we do not
    # support abstract classes.
    @ContractOnly
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
