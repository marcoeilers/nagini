# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from nagini_contracts.io_builtins import *


class A:
    def __init__(self) -> None:
        Ensures(Acc(self.v))  # type: ignore
        self.v = 12


@Pure
def getv(a: A) -> int:
    Requires(Acc(a.v))
    return a.v


@Pure
def getv_2(a: A) -> int:
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
                eval_io(t1, getv, a, result, t2) and
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
    r, t = Eval(t1, getv, a)
    assert r == getv(a)
    unlock_a(a)
    t = write_int(t, r)
    return t, r


def use_ctoken(t1: Place, a: A, b: A) -> Tuple[Place, int]:
    IOExists3(Place, Place, int)(
        lambda t2, t_post, result: (
            Requires(
                ctoken(t1) and
                eval_io(t1, getv, a, result, t2) and
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
    r, t = Eval(t1, getv, a)
    assert r == getv(a)
    unlock_a(a)
    t = write_int(t, r)
    return t, r


def wrong_func(t1: Place, a: A, b: A) -> Tuple[Place, int]:
    IOExists3(Place, Place, int)(
        lambda t2, t_post, result: (
            Requires(
                token(t1, 2) and
                eval_io(t1, getv, a, result, t2) and
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
    #:: ExpectedOutput(call.precondition:insufficient.permission)
    r, t = Eval(t1, getv_2, a)
    unlock_a(a)
    t = write_int(t, r)
    return t, r


def wrong_arg(t1: Place, a: A, b: A) -> Tuple[Place, int]:
    IOExists3(Place, Place, int)(
        lambda t2, t_post, result: (
            Requires(
                token(t1, 2) and
                eval_io(t1, getv, a, result, t2) and
                write_int_io(t2, result, t_post)
            ),
            Ensures(
                token(t_post) and
                t_post == Result()[0] and
                result == Result()[1]
            ),
        )
    )
    lock_a(b)
    #:: ExpectedOutput(call.precondition:insufficient.permission)
    r, t = Eval(t1, getv, b)
    unlock_a(b)
    t = write_int(t, r)
    return t, r


def no_token(t1: Place, a: A, b: A) -> Tuple[Place, int]:
    IOExists3(Place, Place, int)(
        lambda t2, t_post, result: (
            Requires(
                eval_io(t1, getv, a, result, t2) and
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
    #:: ExpectedOutput(call.precondition:insufficient.permission)
    r, t = Eval(t1, getv, a)
    unlock_a(a)
    t = write_int(t, r)
    return t, r


def no_io_perm(t1: Place, a: A, b: A) -> None:
    IOExists3(Place, Place, int)(
        lambda t2, t_post, result: (
            Requires(
                token(t1, 2)
            ),
            Ensures(
                token(t1, 1)
            ),
        )
    )
    lock_a(a)
    #:: ExpectedOutput(call.precondition:insufficient.permission)
    r, t = Eval(t1, getv, a)


def no_func_perm(t1: Place, a: A, b: A) -> Tuple[Place, int]:
    IOExists3(Place, Place, int)(
        lambda t2, t_post, result: (
            Requires(
                token(t1, 2) and
                eval_io(t1, getv, a, result, t2) and
                write_int_io(t2, result, t_post)
            ),
            Ensures(
                #:: ExpectedOutput(carbon)(postcondition.violated:insufficient.permission)
                token(t_post) and
                t_post == Result()[0] and
                result == Result()[1]
            ),
        )
    )
    #:: ExpectedOutput(application.precondition:insufficient.permission)
    r, t = Eval(t1, getv, a)
    return t, r