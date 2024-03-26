# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Any

@Complex
class Foobar:
    def __init__(self) -> None:
        self.x = 10
        Ensures(Acc(self.x))
        Ensures(self.x == 10)

    def __getattr__(self, name: str) -> object:
        pass

@Complex
class WrapsFoobar:
    def __init__(self, wraps: Foobar) -> None:
        self.f = wraps
        Ensures(Acc(self.f))
        Ensures(self.f is wraps)
        Ensures(MayCreate(self, 'x'))

    def __getattr__(self, name: str) -> object:
        pass

    @Pure
    def __getattr__real(self, item: str) -> object:
        Requires(Acc(self.__dict__['f']))
        Requires(Acc(self.__dict__['f'].__dict__[item]))
        return self.f.__dict__[item]


def wrap_example() -> None:
    f = Foobar()
    wf = WrapsFoobar(f)
    Assert(wf.x == 10)



@Complex
class Parent:
    def __init__(self) -> None:
        self.x = "15"
        self.y = 20
        self.__dict__['qwe'] = 0
        Ensures(Acc(self.x))
        Ensures(self.x == "15")
        Ensures(Acc(self.y))
        Ensures(self.y == 20)
        Ensures(MaySet(self, 'z'))
        Ensures(MayCreate(self, 'a'))
        
        Ensures('qw' + 'e' == 'qwe')
        Ensures('q' + 'we' == 'qwe')
        Ensures(Acc(self.__dict__['qw' + 'e']))
        Ensures(self.__dict__['q' + 'we'] == 0)

    def __getattr__(self, name: str) -> object:
        pass

    @Pure
    def __getattr__real(self, name: str) -> object:
        return 99

    def __setattr__(self, name: str, value: object) -> None:
        Requires(Acc(self.__dict__[name]))
        self.__dict__[name] = value
        Ensures(Acc(self.__dict__[name]))
        Ensures(self.__dict__[name] == value)

    def some_method(self) -> None:
        Requires(MaySet(self, 'z'))
        Requires(MayCreate(self, 'a'))
        self.z: object = 10
        self.a = 100
        Ensures(Acc(self.z))
        Ensures(self.z == 10)
        Ensures(Acc(self.a))
        Ensures(self.a == 100)

    def another_method(self) -> None:
        Requires(Acc(self.__dict__['qwe']))
        self.__dict__['qwe'] = 1_000_000
        Assert(self.__dict__['qwe'] == 1_000_000)
        Ensures(Acc(self.__dict__['qwe']))
        Ensures(self.__dict__['qwe'] == 1_000_000)
        # Ensures(self.qwe == 1_000_000)


class Normal:
    def __init__(self) -> None:
        self.x = "25"
        Ensures(Acc(self.x))
        Ensures(self.x == "25")


def main() -> None:
    c = Parent()
    Assert(c.x == "15")
    Assert(c.y == 20)
    c.z = 22

    Assert(c.a == 99)

    # c.a = 22      # this would create an error
                    # because some_method has Requires(MayCreate(self, 'a'))

    c.some_method()
    Assert(c.z == 10)
    Assert(c.a == 100)
    # some_func(c)


if __name__ == "__main__":
    main()



