from py2viper_contracts.contracts import Requires, Predicate
from py2viper_contracts.io import *
from typing import Tuple


@IOOperation
def read_something_io(
        t_pre: Place,
        result1: int = Result(),
        result2: bool = Result(),
        t_post: Place = Result(),
        ) -> bool:
    Terminates(True)


def read_something(t1: Place) -> Tuple[Place, int, bool]:
    IOExists3(Place, int, bool)(
        lambda t2, value1, value2: (
        Requires(
            token(t1) and
            read_something_io(t1, value1, value2, t2)
        ),
        Ensures(
            token(t2) and
            Result()[0] == t2 and
            Result()[1] == value1 and
            Result()[2] == value2
        ),
        )
    )


@IOOperation
def write_something_io(
        t_pre: Place,
        arg1: int,
        arg2: bool,
        t_post: Place = Result(),
        ) -> bool:
    Terminates(True)


def write_something(t1: Place, value1: int, value2: bool) -> Place:
    IOExists1(Place)(
        lambda t2: (
        Requires(
            token(t1) and
            write_something_io(t1, value1, value2, t2)
        ),
        Ensures(
            token(t2) and
            Result() == t2
        ),
        )
    )


class C1:
    pass
class C2:
    pass
class C3:
    pass
class C4:
    pass
class C5:
    pass
class C6:
    pass
class C7:
    pass
class C8:
    pass
class C9:
    pass
def io_exists(
        a1: C1,
        a2: C2,
        a3: C3,
        a4: C4,
        a5: C5,
        a6: C6,
        a7: C7,
        a8: C8,
        a9: C9) -> None:
    IOExists1(C1)(
        lambda c1:
        Ensures(
            c1 == a1
        )
    )
    IOExists2(C1, C2)(
        lambda c1, c2:
        Ensures(
            c1 == a1 and
            c2 == a2
        )
    )
    IOExists3(C1, C2, C3)(
        lambda c1, c2, c3:
        Ensures(
            c1 == a1 and
            c2 == a2 and
            c3 == a3
        )
    )
    IOExists4(C1, C2, C3, C4)(
        lambda c1, c2, c3, c4:
        Ensures(
            c1 == a1 and
            c2 == a2 and
            c3 == a3 and
            c4 == a4
        )
    )
    IOExists5(C1, C2, C3, C4, C5)(
        lambda c1, c2, c3, c4, c5:
        Ensures(
            c1 == a1 and
            c2 == a2 and
            c3 == a3 and
            c4 == a4 and
            c5 == a5
        )
    )
    IOExists6(C1, C2, C3, C4, C5, C6)(
        lambda c1, c2, c3, c4, c5, c6:
        Ensures(
            c1 == a1 and
            c2 == a2 and
            c3 == a3 and
            c4 == a4 and
            c5 == a5 and
            c6 == a6
        )
    )
    IOExists7(C1, C2, C3, C4, C5, C6, C7)(
        lambda c1, c2, c3, c4, c5, c6, c7:
        Ensures(
            c1 == a1 and
            c2 == a2 and
            c3 == a3 and
            c4 == a4 and
            c5 == a5 and
            c6 == a6 and
            c7 == a7
        )
    )
    IOExists8(C1, C2, C3, C4, C5, C6, C7, C8)(
        lambda c1, c2, c3, c4, c5, c6, c7, c8:
        Ensures(
            c1 == a1 and
            c2 == a2 and
            c3 == a3 and
            c4 == a4 and
            c5 == a5 and
            c6 == a6 and
            c7 == a7 and
            c8 == a8
        )
    )
    IOExists9(C1, C2, C3, C4, C5, C6, C7, C8, C9)(
        lambda c1, c2, c3, c4, c5, c6, c7, c8, c9:
        Ensures(
            c1 == a1 and
            c2 == a2 and
            c3 == a3 and
            c4 == a4 and
            c5 == a5 and
            c6 == a6 and
            c7 == a7 and
            c8 == a8 and
            c9 == a9
        )
    )
