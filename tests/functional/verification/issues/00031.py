# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


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


def io_exists2(
        c1: C1,
        c2: C2,
        c3: C3,
        c4: C4,
        c5: C5,
        c6: C6,
        c7: C7,
        c8: C8,
        c9: C9) -> None:
    Requires(False)
    Ensures(
            True and is_c1(c1, c1)       and
            True and is_c2(c2, c2)       and
            True and is_c3(c3, c3)       and
            True and is_c4(c4, c4)       and
            True and is_c5(c5, c5)       and
            True and is_c6(c6, c6)       and
            True and is_c7(c7, c7)       and
            True and is_c8(c8, c8)       and
            True and is_c9(c9, c9)
    )
