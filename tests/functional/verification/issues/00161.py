# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

class Parent:
    x = 100


class Subclass:
    y = 200

    def __init__(self) -> None:
        self.x = 100
        Ensures(Acc(self.x))


def main() -> None:
    instance = Subclass()
    #:: ExpectedOutput(assert.failed:insufficient.permission)
    Assert(instance.y == 200)
    Subclass.y = 300
    Assert(instance.y == 200)
