# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class Dock:

    def __init__(self, value: int) -> None:
        Ensures(Acc(self.n) and self.n == value)
        self.n = value  # type: int


class Cell:

    def __init__(self) -> None:
        Ensures(Acc(self.x))
        Ensures(Acc(self.dock))
        self.x = 0  # type: int
        self.dock = Dock(1)  # type: Dock

    @Pure
    def docker(self) -> Dock:
        Requires(Rd(self.dock))
        return self.dock

    def test(self) -> None:
        Requires(Rd(self.dock) and Rd(self.docker().n) and self.docker().n > 0 and Acc(self.x, self.docker().n * ARP()))
        Ensures(Rd(self.dock) and Rd(self.docker().n) and self.docker().n > 0 and Acc(self.x, self.docker().n * ARP()))

    def test2(self) -> None:
        Requires(Acc(self.dock, ARP() * 1/2))
        Ensures(Acc(self.dock, ARP() * 1/2))
