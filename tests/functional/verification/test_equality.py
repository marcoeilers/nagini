# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

#:: IgnoreFile(70)
from nagini_contracts.contracts import *


class Thing:

    def __init__(self) -> None:
        Ensures(Acc(self.value) and self.value == 44)  # type: ignore
        self.value = 44

    def set_value(self, new_val: int) -> None:
        Requires(Acc(self.value))
        Ensures(Acc(self.value))
        Ensures(self.value == new_val)
        self.value = new_val

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(Acc(self.value, 1/10))
        Requires(Acc(other.value, 1/10) if isinstance(other, Thing) else True)
        if not isinstance(other, Thing):
            return False
        return self.value == other.value


class Other:
    pass


def main() -> None:
    Assert(3 != 2)
    Assert(3 == 3)
    Assert("g" == "g")
    t1 = Thing()
    t2 = Thing()
    o = Other()
    Assert(t1 == t2)
    Assert(not (t1 is t2))
    Assert(t1 is not o)
    Assert(t1 != o)
    Assert(t1 != 44)
    t1.set_value(45)
    Assert(t1 != t2)
    Assert(not (t1 is t2))
    t2.set_value(45)
    Assert(t1 == t2)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(t2 == o)
