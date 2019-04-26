# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class Positive:

    def __init__(self) -> None:
        Ensures(self.valid())
        self.int_field = 14
        Fold(self.valid())

    @Predicate
    def valid(self) -> bool:
        return Acc(self.int_field) and self.int_field > 0

    def increase(self) -> None:
        Requires(self.valid())
        Ensures(self.valid())

        Unfold(self.valid())
        self.int_field = self.int_field + 1
        Fold(self.valid())


class SubPositive(Positive):

    def increase(self) -> None:
        Requires(self.valid())
        Ensures(self.valid())

        Unfold(self.valid())
        self.int_field = self.int_field + 2
        Fold(self.valid())
