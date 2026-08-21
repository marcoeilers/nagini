# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from typing import Type, cast, List, Tuple
from nagini_contracts.contracts import *

class MyClass:
    pass

class MyOtherClass(MyClass):
    pass

class MyThirdClass(MyClass):
    pass

def tester1(o: object) -> None:
    if type(o) == MyClass:
        mc = cast(MyClass, o)
    elif type(o) in (MyClass, MyOtherClass):
        moc = cast(MyOtherClass, o)
    if isinstance(o, MyClass):
        mc = cast(MyClass, o)
    ls = [int, MyClass]
    if type(o) in ls:
        if not isinstance(o, MyClass):
            a = cast(int, o)

def tester1f1(o: object) -> None:
    if type(o) == MyClass:
        #:: ExpectedOutput(application.precondition:assertion.false)
        mc = cast(MyOtherClass, o)

def tester1f2(o: object) -> None:
    if type(o) == MyClass:
        mc = cast(MyClass, o)
    elif type(o) in (MyThirdClass, MyOtherClass):
        #:: ExpectedOutput(application.precondition:assertion.false)
        moc = cast(MyOtherClass, o)

def tester1f3(o: object) -> None:
    if type(o) == MyClass:
        mc = cast(MyClass, o)
    elif type(o) in (MyClass, MyOtherClass):
        moc = cast(MyOtherClass, o)
    ls = [int, MyClass]
    if type(o) in ls:
        #:: ExpectedOutput(application.precondition:assertion.false)
        a = cast(int, o)

def tester2(o: object, t: type) -> None:
    Requires(type(o) == int)
    if isinstance(o, MyClass):
        Assert(False)
    Assert(type(o) != bool)

def tester2f1(o: object, t: type) -> None:
    Requires(type(o) == int)
    if isinstance(o, object):
        #:: ExpectedOutput(assert.failed:assertion.false)
        Assert(False)


def tester3(o: object, t: Type[int]) -> None:
    pass

def tester4(o: object, t: type, b: bool) -> None:
    Requires(Implies(b, t == MyClass))
    ii = isinstance(o, t)
    if b and isinstance(o, MyOtherClass):
        Assert(ii)


def tester5(o: object, t: type) -> None:
    if isinstance(o, (int, t)):
        if t == bool:
            a = cast(int, o)

def tester5f(o: object, t: type) -> None:
    if isinstance(o, (int, t)):
        if t == str:
            #:: ExpectedOutput(assert.failed:assertion.false)
            a = cast(int, o)


def tester6(o: object, t: type) -> None:
    tps: Tuple[type, type] = (int, t)
    if isinstance(o, tps):
        if t == bool:
            a = cast(int, o)


def tester6f(o: object, t: type) -> None:
    tps: Tuple[type, type] = (int, t)
    if isinstance(o, tps):
        if t == str:
            #:: ExpectedOutput(assert.failed:assertion.false)
            a = cast(int, o)