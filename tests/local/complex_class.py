# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Any

@Complex
class PrefixStuff:
    def __init__(self) -> None:
        Ensures(MayCreate(self, 'x'))
        Ensures(MayCreate(self, '__x'))

    def __getattr__(self, name: str) -> object:
        Requires(Implies(len(name) >= 2, name[:2] != "__"))
        return 10

def main2() -> None:
    p = PrefixStuff()
    Assert(p.x == 10)

    # this will fail, names starting with "__" not allowed
    # Assert(p.__x == 10)

@Complex
class GetattributeStuff:
    def __init__(self) -> None:
        self.x, self.y = 10, 20
        # self.y = 20
        Ensures(Acc(self.x))
        Ensures(self.x == 10)
        Ensures(Acc(self.y))
        Ensures(self.y == 20)
        Ensures(MayCreate(self, 'xyz'))
        Ensures(MayCreate(self, 'qwe'))

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
        Requires(MaySet(self, name))

        # Auto generated:
        # Ensures(Implies(name in PSet("foo", "bar", "__dict__", ...), Result() == object.__getattribute__(self, name)))

        if name == "xyz" or name == "__dict_":
            # cannot.have.object.__getattribute__.here
            # my_attr: object = object.__getattribute__(self, name)
            # return my_attr
            return 1_000_000
        else:
            return object.__getattribute__(self, name)


def getattribute_example() -> None:
    g = GetattributeStuff()
    Assert(g.__dict__['x'] == 10)
    Assert(g.xyz == 1_000_000)
    Assert(object.__getattribute__(g, "x") == 10)
    # Assert(object.__getattribute__(g, "qwe") == 1_000)    # this won't work because __getattr__ is not called

    Assert(g.x == 10)                                           # call __getattribute__

    # calling g.__getattribute__ directly not allowed!

    Assert(g.x == 10)                                   # g.__getattribute__('x')   == 10        WITH __getattr__
    Assert(g.qwe == 1_000)                              # g.__getattribute__('qwe') == 1_000     WITH __getattr__
    Assert(g.xyz == 1_000_000)                          # g.__getattribute__('xyz') == 1_000_000 WITH __getattr__

    Assert(g.foo() == 50)   # still call foo(). does not call __getattribute__


@Complex
class SetattrStuff:
    def __init__(self) -> None:
        self.foo = 10
        self.__dict__['bar'] = 10
        Ensures(Acc(self.foo))
        Ensures(self.foo == 11)
        Ensures(Acc(self.__dict__['bar']))
        Ensures(self.__dict__['bar'] == 10)
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

        # this is awkward:
        Ensures(self.__dict__[name] is value + 1)


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

@Complex
class WrapsFoobar:
    def __init__(self, wraps: Foobar) -> None:
        self.f = wraps
        Ensures(Acc(self.f))
        Ensures(self.f is wraps)
        Ensures(MayCreate(self, 'x'))

    # @Pure assumed
    def __getattr__(self, name: str) -> object:
        Requires(Acc(self.__dict__['f']))       # need this instead of self.f because that recurses via precondition!
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


class Child(Parent):
    def __init__(self) -> None:
        self.k = "15"
        Ensures(Acc(self.k))
        Ensures(self.k == "15")


class Normal:
    def __init__(self) -> None:
        self.x = "25"
        Ensures(Acc(self.x))
        Ensures(self.x == "25")


class A:
    def __init__(self) -> None:
        self.k = "15"
        Ensures(Acc(self.k))
        Ensures(self.k == "15")


@Complex
class B(A):
    def __init__(self) -> None:
        super().__init__()
        Ensures(Acc(self.k))
        Ensures(self.k == "15")


@Complex
class LockStuff:
    def __init__(self) -> None:
        self.__dict__['lock'] = False
        self.foo = 10
        self.__dict__['lock'] = True
        Ensures(Acc(self.foo))
        Ensures(self.foo == 10)
        Ensures(Acc(self.__dict__['lock']))
        Ensures(self.__dict__['lock'] == True)

    def __getattr__(self, item: str) -> object:
        return None

    def __setattr__(self, name: str, value: int) -> None:
        Requires(MaySet(self, name))
        Requires(Acc(self.lock))
        Requires(self.lock == False)

        self.__dict__[name] = value

        Ensures(Acc(self.lock))
        Ensures(Acc(self.__dict__[name]))
        # this is awkward:
        Ensures(self.__dict__[name] is value)
        # need this:
        # ensures issubtype(typeof(keydict___getitem__(self_22, name_7)), typeof(value_1))
        # in order to be able to use this:
        # Ensures(type(self.__dict__[name]) == type(value))

def lock_example() -> None:
    l = LockStuff()
    Assert(l.foo == 10)

    l.__dict__['lock'] = False  # without this, lines below will fail
    l.foo = 31
    Assert(l.foo == 31)

def main() -> None:
    p = Parent()
    Assert(p.x == "15")
    Assert(p.y == 20)
    p.z = 22

    Assert(p.a == 99)

    # p.a = 22      # this would create an error
                    # because some_method has Requires(MayCreate(self, 'a'))

    p.some_method()
    Assert(p.z == 10)
    Assert(p.a == 100)

    p.last_method()
    # some_func(p)

    a = A()
    b = B()

    c = Child()
    Assert(c.k == "15")
    Assert(c.__dict__['k'] == "15")

    Assert(a.k == "15")
    Assert(b.k == "15")

    Assert(b.__dict__['k'] == "15")
    # Assert(a.__dict__['k'] == "15")   # will not work because A is not-complex.

    s = "hello world"
    Assert(s[2:5] == "llo")

    x = "abcd"
    y = x + "efg"
    Assert(y == "abcdefg")
    Assert(y[2:6] == "cdef")

if __name__ == "__main__":
    main()


