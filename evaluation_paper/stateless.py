# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Tuple


def client_tuple(x: Tuple[Tuple[int, str], bool], y: Tuple[Tuple[int, str], bool]) -> str:
    Requires(Stateless(x))
    Requires(Stateless(y))
    Requires(x[0][0] == y[0][0])
    Requires(x[0][1] == y[0][1])
    Requires(Stateless(x[0]))
    Requires(Stateless(y[0]))
    Requires(x[0] == y[0])
    Requires(x[1] == y[1])
    Ensures(Result() == x[0][1])
    assert x == y
    return x[0][1]


if __name__ == '__main__':
    x: Tuple[Tuple[int, str], bool] = ((42, "hello"), True)
    y: Tuple[Tuple[int, str], bool] = ((42, "hello"), True)
    Assert(client_tuple(x, y) == "hello")