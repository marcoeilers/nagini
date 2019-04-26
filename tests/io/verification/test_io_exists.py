# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import Requires, Ensures, Pure
from nagini_contracts.io_contracts import *
from typing import Tuple


class C1:
    pass


@Pure
def is_c1(x: C1, y: C1) -> bool:
    return True


class C2:
    pass


@Pure
def is_c2(x: C2, y: C2) -> bool:
    return True


class C3:
    pass


@Pure
def is_c3(x: C3, y: C3) -> bool:
    return True


class C4:
    pass


@Pure
def is_c4(x: C4, y: C4) -> bool:
    return True


class C5:
    pass


@Pure
def is_c5(x: C5, y: C5) -> bool:
    return True


class C6:
    pass


@Pure
def is_c6(x: C6, y: C6) -> bool:
    return True


class C7:
    pass


@Pure
def is_c7(x: C7, y: C7) -> bool:
    return True


class C8:
    pass


@Pure
def is_c8(x: C8, y: C8) -> bool:
    return True


class C9:
    pass


@Pure
def is_c9(x: C9, y: C9) -> bool:
    return True


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
            c1 == a1 and is_c1(c1, a1)
        )
    )
    IOExists2(C1, C2)(
        lambda c1, c2:
        Ensures(
            c1 == a1 and is_c1(c1, a1) and
            c2 == a2 and is_c2(c2, a2)
        )
    )
    IOExists3(C1, C2, C3)(
        lambda c1, c2, c3:
        Ensures(
            c1 == a1 and is_c1(c1, a1) and
            c2 == a2 and is_c2(c2, a2) and
            c3 == a3 and is_c3(c3, a3)
        )
    )
    IOExists4(C1, C2, C3, C4)(
        lambda c1, c2, c3, c4:
        Ensures(
            c1 == a1 and is_c1(c1, a1) and
            c2 == a2 and is_c2(c2, a2) and
            c3 == a3 and is_c3(c3, a3) and
            c4 == a4 and is_c4(c4, a4)
        )
    )
    IOExists5(C1, C2, C3, C4, C5)(
        lambda c1, c2, c3, c4, c5:
        Ensures(
            c1 == a1 and is_c1(c1, a1) and
            c2 == a2 and is_c2(c2, a2) and
            c3 == a3 and is_c3(c3, a3) and
            c4 == a4 and is_c4(c4, a4) and
            c5 == a5 and is_c5(c5, a5)
        )
    )
    IOExists6(C1, C2, C3, C4, C5, C6)(
        lambda c1, c2, c3, c4, c5, c6:
        Ensures(
            c1 == a1 and is_c1(c1, a1) and
            c2 == a2 and is_c2(c2, a2) and
            c3 == a3 and is_c3(c3, a3) and
            c4 == a4 and is_c4(c4, a4) and
            c5 == a5 and is_c5(c5, a5) and
            c6 == a6 and is_c6(c6, a6)
        )
    )
    IOExists7(C1, C2, C3, C4, C5, C6, C7)(
        lambda c1, c2, c3, c4, c5, c6, c7:
        Ensures(
            c1 == a1 and is_c1(c1, a1) and
            c2 == a2 and is_c2(c2, a2) and
            c3 == a3 and is_c3(c3, a3) and
            c4 == a4 and is_c4(c4, a4) and
            c5 == a5 and is_c5(c5, a5) and
            c6 == a6 and is_c6(c6, a6) and
            c7 == a7 and is_c7(c7, a7)
        )
    )
    IOExists8(C1, C2, C3, C4, C5, C6, C7, C8)(
        lambda c1, c2, c3, c4, c5, c6, c7, c8:
        Ensures(
            c1 == a1 and is_c1(c1, a1) and
            c2 == a2 and is_c2(c2, a2) and
            c3 == a3 and is_c3(c3, a3) and
            c4 == a4 and is_c4(c4, a4) and
            c5 == a5 and is_c5(c5, a5) and
            c6 == a6 and is_c6(c6, a6) and
            c7 == a7 and is_c7(c7, a7) and
            c8 == a8 and is_c8(c8, a8)
        )
    )
    IOExists9(C1, C2, C3, C4, C5, C6, C7, C8, C9)(
        lambda c1, c2, c3, c4, c5, c6, c7, c8, c9:
        Ensures(
            c1 == a1 and is_c1(c1, a1) and
            c2 == a2 and is_c2(c2, a2) and
            c3 == a3 and is_c3(c3, a3) and
            c4 == a4 and is_c4(c4, a4) and
            c5 == a5 and is_c5(c5, a5) and
            c6 == a6 and is_c6(c6, a6) and
            c7 == a7 and is_c7(c7, a7) and
            c8 == a8 and is_c8(c8, a8) and
            c9 == a9 and is_c9(c9, a9)
        )
    )
