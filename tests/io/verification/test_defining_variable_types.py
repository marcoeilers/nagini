# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

#:: IgnoreFile(23)
from nagini_contracts.contracts import Ensures, Requires, ContractOnly
from nagini_contracts.io_contracts import *


@IOOperation
def do_io1(
        t1_pre: Place,
        value: bool = Result(),
        ) -> bool:
    Terminates(False)


@ContractOnly
def test1(t1: Place) -> int:
    IOExists1(bool)(
        lambda value: (
        Requires(
            do_io1(t1, value)
        ),
        Ensures(
            value == Result()
        ),
        )
    )


class C1:
    pass


class C2(C1):
    pass


@IOOperation
def do_io2(
        t1_pre: Place,
        value: C2 = Result(),
        ) -> bool:
    Terminates(False)


@ContractOnly
def test2(t1: Place) -> C1:
    IOExists1(C2)(
        lambda value: (
        Requires(
            do_io2(t1, value)
        ),
        Ensures(
            value == Result()
        ),
        )
    )
