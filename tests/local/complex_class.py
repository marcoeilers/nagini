# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Any


@Complex
class GetattributeStuff:
    def __init__(self) -> None:
        self.x = 10
        self.y = 20
        Ensures(Acc(self.x))
        Ensures(self.x == 10)
        Ensures(Acc(self.y))
        Ensures(self.y == 20)
        Ensures(MayCreate(self, 'xyz'))

        # init still exhales write acc to all function names, which includes "foo" and "bar"
        # leaves a read permission

    def foo(self) -> object:
        Ensures(Result() == 50)
        return 50

    def bar(self) -> object:
        Ensures(Result() == 50)
        return 50

    def __getattr__(self, name: str) -> object:
        Ensures(Result() == 1_000)
        return 1_000

    # @Pure       # assumed @Pure
    def __getattribute__(self, name: str) -> object:

        # From the user:
        # Requires(Implies(name == "xyz", MaySet(self, name)))
        # Requires(Implies(name == "x", Acc(object.__getattribute__(self, name))))
        Requires(MaySet(self, name))
        

        # Auto generated:
        Ensures(Implies(name == "foo",      Result() == object.__getattribute__(self, name)))
        Ensures(Implies(name == "bar",      Result() == object.__getattribute__(self, name)))
        Ensures(Implies(name == "__dict__", Result() == object.__getattribute__(self, name)))

        #  func name        func name        important!            anything else the user wants
        if name == "foo" or name == "bar" or name == "__dict__" or name == "xyz":

            # cannot.have.object.__getattribute__.here
            # my_attr: object = object.__getattribute__(self, name)
            # return my_attr
            # return 50
            return object.__getattribute__(self, name)
        elif name == "x":
            return object.__getattribute__(self, name)
        else:
            # whatever else goes here
            return 1_000_000


def getattribute_example() -> None:
    g = GetattributeStuff()
    Assert(g.__dict__['x'] == 10)
    Assert(g.xyz == 1_000)
    Assert(object.__getattribute__(g, "x") == 10)
    # Assert(object.__getattribute__(g, "xyz") == 1_000)    # this won't work because __getattr__ is not called

    Assert(g.x == 10)                                           # call __getattribute__

    # calling g.__getattribute__ directly won't be allowed!
    Assert(g.__getattribute__('x') == 10)                       # g.x == 10.
    Assert(g.__getattribute__('xyz') == 1_000)                  # g.xyz == 1_000
    # Assert(g.__getattribute__('hello_world') == 1_000_000)      # g.hello_world == 1_000_000

    # Assert(g.__getattribute('hello_world') == 1_000_001)    # sanity check

    Assert(g.foo() == 50)   # still call foo(). does not call __getattribute__


@Complex
class SetattrStuff:
    def __init__(self) -> None:
        self.foo = 10
        self.__dict__['bar'] = 10
        Ensures(Acc(self.foo))
        Ensures(self.foo == 11)
        Ensures(Acc(self.__dict__['bar']))
        Ensures(self.__dict__['bar'] == 11)
        Ensures(MaySet(self, 'a'))

    def __getattr__(self, name: str) -> object:
        return None

    # def foo(self) -> int:
    #     return 32

    # def bar(self) -> int:
    #     return 23

    def __setattr__(self, name: str, value: int) -> None:
        Requires(MaySet(self, name))
        self.__dict__[name] = value + 1
        Ensures(Acc(self.__dict__[name]))
        Ensures(self.__dict__[name] == value + 1)
        Ensures(type(self.__dict__[name]) is int)


def setattr_example() -> None:
    s = SetattrStuff()
    s.a = 20
    Assert(s.a == 21)


@Complex
class Foobar:
    def __init__(self) -> None:
        self.x = 10
        Ensures(Acc(self.x))
        Ensures(self.x == 10)

    def __getattr__(self, name: str) -> object:
        return None

@Complex
class WrapsFoobar:
    def __init__(self, wraps: Foobar) -> None:
        self.f = wraps
        Ensures(Acc(self.f))
        Ensures(self.f is wraps)
        Ensures(MayCreate(self, 'x'))

    # @Pure assumed
    def __getattr__(self, name: str) -> object:
        Requires(Acc(self.__dict__['f']))
        Requires(Acc(self.__dict__['f'].__dict__[name]))
        return self.f.__dict__[name]


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

        Ensures(MayCreate(self, 'b'))
        
        Ensures('qw' + 'e' == 'qwe')
        Ensures('q' + 'we' == 'qwe')
        Ensures(Acc(self.__dict__['qw' + 'e']))
        Ensures(self.__dict__['q' + 'we'] == 0)

    def __getattr__(self, name: str) -> object:
        return 99


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

    def last_method(self) -> None:
        Requires(MaySet(self, 'b'))
        Requires(self.b == 99)
        Ensures(MaySet(self, 'b'))


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

    c.last_method()
    # some_func(c)


if __name__ == "__main__":
    main()



