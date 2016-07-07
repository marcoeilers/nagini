from py2viper_contracts.contracts import Requires
from py2viper_contracts.io import *


@IOOperation
def read_int_io(
        t_pre: Place,
        result: int = Result(),
        t_post: Place = Result(),
        ) -> bool:
    Terminates(True)


def test(t1: Place, value: int) -> None:
    IOExists1(Place)(
        lambda t2: (
        Requires(
            token(t1) and
            #:: ExpectedOutput(invalid.program:invalid.io_operation_use.variable_not_existential)
            read_int_io(t1, value, t2)
        ),
        )
    )
