from nagini_contracts.contracts import (
    Assert,
)


class Exc1(Exception):
    pass


class Exc2(Exception):
    pass


def test() -> None:
    try:
        x = 5
    except Exc1 as ex1:
        x = 6
        try:
            x = 7
        except Exc2 as ex2:
            Assert(isinstance(ex1, Exc2))
