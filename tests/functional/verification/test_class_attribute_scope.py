# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from typing import List

from nagini_contracts.contracts import *

limit = 5


def helper() -> int:
    Ensures(Result() == 1)
    return 1


class Table:
    limit = 20
    size = 7
    name = 0
    items = 0

    @staticmethod
    def helper() -> int:
        Ensures(Result() == 2)
        return 2

    def local(self) -> int:
        Ensures(Result() == 4)
        size = 3
        return size + 1

    def parameter(self, size: int) -> int:
        Ensures(Result() == size + 1)
        return size + 1

    def module_global(self) -> int:
        Ensures(Result() == 5)
        return limit

    def module_global_fail(self) -> int:
        #:: ExpectedOutput(postcondition.violated:assertion.false)
        Ensures(Result() == 20)
        return limit

    def module_function(self) -> int:
        Ensures(Result() == 1)
        return helper()

    def module_function_fail(self) -> int:
        #:: ExpectedOutput(postcondition.violated:assertion.false)
        Ensures(Result() == 2)
        return helper()

    def qualified(self) -> int:
        Ensures(Result() == 20 + 7 + 2)
        return Table.limit + self.size + Table.helper()

    def local_of_other_type(self) -> int:
        Ensures(Result() == 3)
        name = [1, 2, 3]
        return len(name)

    def parameter_of_other_type(self, name: List[int]) -> int:
        Requires(Acc(list_pred(name), 1/2))
        Ensures(Acc(list_pred(name), 1/2) and Result() == len(name))
        return len(name)

    def ghost_local(self) -> None:
        items = PSeq(1, 2)
        Assert(len(items) == 2)


def local() -> int:
    Ensures(Result() == 4)
    size = 3
    return size + 1


def parameter(size: int) -> int:
    Ensures(Result() == size + 1)
    return size + 1


def module_global() -> int:
    Ensures(Result() == 5)
    return limit


def module_global_fail() -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 20)
    return limit


def local_of_other_type() -> int:
    Ensures(Result() == 3)
    name = [1, 2, 3]
    return len(name)


def ghost_local() -> None:
    items = PSeq(1, 2)
    Assert(len(items) == 2)
