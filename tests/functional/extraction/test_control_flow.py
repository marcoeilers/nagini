# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Optional


@Ghost
def gvalue() -> int:
    pass


class NoLock:
    def __init__(self) -> None:
        Ensures(Acc(self.value))  # type: ignore
        self.value = 4

    def __enter__(self) -> int:
        Requires(Acc(self.value))
        Ensures(Acc(self.value))
        return 9

    def __exit__(self, t: type, e: Optional[Exception],
                 tb: Optional[object]) -> int:
        Requires(Acc(self.value))
        Ensures(Acc(self.value))
        return 7


def with_and_try(l: NoLock, x: int) -> int:
    gi: GInt = 0
    with l:
        gi = gvalue()
        x = x + 1
    try:
        gi = gvalue()
        x = x + 1
    except Exception:
        gi = gvalue()
        x = 2
    finally:
        gi = gvalue()
    if gi > 0:
        gi = gi + 1
    else:
        gi = 0
    while gi > 0:
        gi = gi - 1
    return x
