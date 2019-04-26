# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class A:
    def __init__(self, a: int) -> None:
        Ensures(Acc(self.a))  # type: ignore
        Ensures(self.a == a)  # type: ignore
        self.a = a

    def m1(self, x: int) -> int:
        Ensures(Result() == x)
        return x

def main() -> None:
    c = A(2).m1(5)