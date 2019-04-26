# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from nagini_contracts.io_builtins import *


class A:
    def __init__(self) -> None:
        Ensures(Acc(self.v))  # type: ignore
        self.v = 12

    def getv(self, a: A) -> int:
        Requires(Acc(a.v))
        return a.v


@ContractOnly
def lock_a(a: A) -> None:
    Requires(MustTerminate(1))
    Ensures(Acc(a.v))


@ContractOnly
def unlock_a(a: A) -> None:
    Requires(MustTerminate(1))
    Requires(Acc(a.v))


@IOOperation
def write_int_io(
        t_pre: Place,
        value: int,
        t_post: Place = Result(),
        ) -> bool:
    Terminates(True)


@ContractOnly
def write_int(t1: Place, value: int) -> Place:
    IOExists1(Place)(
        lambda t2: (
        Requires(
            token(t1, 1) and
            write_int_io(t1, value, t2)
        ),
        Ensures(
            token(t2) and
            t2 == Result()
        ),
        )
    )


def use(t1: Place, a: A, b: A) -> Tuple[Place, int]:
    IOExists3(Place, Place, int)(
        lambda t2, t_post, result: (
            Requires(
                token(t1, 2) and
                #:: ExpectedOutput(invalid.program:invalid.eval.function)
                eval_io(t1, a.getv, a, result, t2) and
                write_int_io(t2, result, t_post)
            ),
            Ensures(
                token(t_post) and
                t_post == Result()[0] and
                result == Result()[1]
            ),
        )
    )
    lock_a(a)
    r, t = Eval(t1, a.getv, a)
    assert r == a.getv(a)
    unlock_a(a)
    t = write_int(t, r)
    return t, r

