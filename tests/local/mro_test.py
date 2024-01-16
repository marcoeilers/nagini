
from nagini_contracts.contracts import *
# from typing import *


class Parent:
    x = 100


class Subclass:
    y = 200

    def __init__(self) -> None:
        self.x = 100
        Ensures(Acc(self.x))
        # Ensures(Acc(Subclass.y))
        # Ensures(self.x == 20)
        # Ensures(Subclass.x == 200)


def main() -> None:
    instance = Subclass()
    Assert(instance.y == 200)
    Subclass.y = 300
    Assert(instance.y == 200)
