from py2viper_contracts.contracts import (
    ContractOnly,
    Ensures,
    Import,
    Requires,
    Result,
)
from py2viper_contracts.io import *
from verifast.stdio_simple import (
    stdout,
    write_char_io,
)
Import('../stdio_simple.py')


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
                    example_io(t1, t2)
                ),
                Ensures(
                    token(t2) and
                    t2 == Result()
                ),
            )
        )
