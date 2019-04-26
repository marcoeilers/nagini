# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class SuperClass:
    def construct(self) -> None:
        Requires(self != None)
        Requires(Acc(self.super_field))  # type: ignore
        Requires(Acc(self.__private_field))  # type: ignore
        Requires(Acc(self.typed_field))  # type: ignore
        Ensures(Acc(self.super_field) and self.super_field == 12)  # type: ignore
        Ensures(Acc(
            self.__private_field) and self.__private_field == 15)  # type: ignore
        Ensures(Acc(self.typed_field)  # type: ignore
                and isinstance(self.typed_field, SuperClass))  # type: ignore
        self.super_field = 12
        self.__private_field = 15
        self.typed_field = SuperClass()

    @Pure
    def get_private(self) -> int:
        Requires(self != None)
        Requires(Acc(self.__private_field))
        return self.__private_field

    @Pure
    def get_public(self) -> int:
        Requires(self != None)
        Requires(Acc(self.super_field))
        return self.super_field


class SubClass(SuperClass):
    def construct_sub(self) -> None:
        Requires(self != None)
        Requires(Acc(self.__private_field))  # type: ignore
        Requires(Acc(self.super_field))  # type: ignore
        Ensures(Acc(
            self.__private_field) and self.__private_field == 35)  # type: ignore
        Ensures(Acc(self.super_field) and self.super_field == 45)  # type: ignore
        self.__private_field = 35
        self.super_field = 45

    def set_private(self, i: int) -> None:
        Requires(self != None)
        Requires(Acc(self.__private_field))
        Ensures(Acc(self.__private_field) and self.__private_field == i)
        self.__private_field = i

    @Pure
    def get_private_sub(self) -> int:
        Requires(self != None)
        Requires(Acc(self.__private_field))
        return self.__private_field

    @Pure
    def get_public_sub(self) -> int:
        Requires(self != None)
        Requires(Acc(self.super_field))
        return self.super_field


def main() -> None:
    sub = SubClass()
    sub.construct()
    sub.construct_sub()
    #:: ExpectedOutput(invalid.program:private.field.access)
    Assert(sub.__private_field == 35)
