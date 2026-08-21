# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from typing import Type, cast, Dict, List, Tuple
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
            #:: ExpectedOutput(application.precondition:assertion.false)
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
            #:: ExpectedOutput(application.precondition:assertion.false)
            a = cast(int, o)


# A type object read back out of a list. This is the case the feature is for:
# the list holds type objects, and one of them is used as a type again.
def tester7(o: object) -> None:
    ls = [int, MyClass]
    Assert(ls[1] == MyClass)
    t = ls[1]
    if isinstance(o, t):
        mc = cast(MyClass, o)


# Same, for a tuple whose element types are declared as plain `type`.
def tester8(o: object) -> None:
    tp: Tuple[type, type] = (int, MyClass)
    t = tp[1]
    Assert(t == MyClass)
    if isinstance(o, t):
        mc = cast(MyClass, o)


# Same again without the annotation. Here mypy infers the precise element types
# Tuple[Type[int], Type[MyClass]], where Type[int] is an overloaded callable
# (int has several constructor overloads) rather than a TypeType.
def tester8a(o: object) -> None:
    tp = (int, MyClass)
    t = tp[1]
    Assert(t == MyClass)
    if isinstance(o, t):
        mc = cast(MyClass, o)


def tester8b(o: object) -> None:
    ls = [MyClass, MyOtherClass]
    t = ls[0]
    if isinstance(o, t):
        mc = cast(MyClass, o)


# isinstance is a subtype check, type(o) == C is an exact check; the two must
# not be conflated.
def tester9(o: MyOtherClass) -> None:
    Assert(isinstance(o, MyClass))


def tester9f(o: MyOtherClass) -> None:
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(type(o) == MyClass)


# Equality and identity between two type-typed variables.
def tester10(t1: type, t2: type, o: object) -> None:
    Requires(t1 == t2)
    Requires(isinstance(o, t1))
    Assert(isinstance(o, t2))


def tester11(t1: type, t2: type) -> None:
    Requires(t1 is t2)
    Assert(t1 == t2)


def tester11f(t1: type, t2: type, o: object) -> None:
    Requires(isinstance(o, t1))
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(isinstance(o, t2))


# A type object as a return value, referred to via Result() in a postcondition.
def type_of(o: object) -> type:
    Ensures(Result() == type(o))
    return type(o)


def tester12(o: MyClass) -> None:
    t = type_of(o)
    Assert(isinstance(o, t))


# The same as a pure function, so that it can be used in specifications.
@Pure
def pure_type_of(o: object) -> type:
    Ensures(Result() == type(o))
    return type(o)


def tester13(o: object) -> None:
    Requires(type(o) == MyClass)
    Assert(pure_type_of(o) == MyClass)


# A type object stored in a field.
class TypeHolder:
    def __init__(self, t: type) -> None:
        self.t = t
        Ensures(Acc(self.t))
        Ensures(self.t is t)


def tester14(o: object) -> None:
    h = TypeHolder(MyClass)
    if isinstance(o, h.t):
        mc = cast(MyClass, o)


# Comparing a type against something that is not a type is legal in Python and
# yields False; it must not be rejected as a precondition violation.
def tester15(t: type, o: object) -> None:
    Assert(not (t == 5))
    Assert(t != 5)
    b = t == o


# Inequality between type objects.
def tester16(t: type, o: object) -> None:
    Requires(isinstance(o, t))
    Requires(t != MyClass)
    Assert(not (t == MyClass))


# Two dynamically obtained types compared with each other.
def tester17(a: object, b: object) -> None:
    Requires(type(a) == type(b))
    Requires(isinstance(a, MyClass))
    Assert(isinstance(b, MyClass))


# A quantifier ranging over type objects.
def tester18(o: object) -> None:
    Requires(Forall(type, lambda t: Implies(isinstance(o, t), t == MyClass)))
    Assert(isinstance(o, MyClass) or True)


# A type object stored in and read back out of a dict.
def tester19(o: object) -> None:
    d = {}  # type: Dict[str, type]
    d['a'] = MyClass
    Assert(d['a'] == MyClass)
    if isinstance(o, d['a']):
        mc = cast(MyClass, o)


# A Type[C] parameter is usable once its value is pinned down.
def tester20(t: Type[MyClass], o: object) -> None:
    Requires(t == MyClass)
    if isinstance(o, t):
        mc = cast(MyClass, o)


def tester20f(t: Type[MyClass]) -> None:
    # t may be a subclass of MyClass, so it is not necessarily MyClass itself.
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(t == MyClass)


# KNOWN LIMITATION: a Type[MyClass] annotation carries no information relating
# the value of t to MyClass, so isinstance(o, t) does not establish that o is a
# MyClass. Encoding that would require type() to become a generic PyType. If
# this is ever fixed, this test starts failing and should become a positive one.
def tester21(t: Type[MyClass], o: object) -> None:
    if isinstance(o, t):
        #:: ExpectedOutput(application.precondition:assertion.false)
        mc = cast(MyClass, o)


# Type objects in the specification-level containers.
def tester22(o: object) -> None:
    Requires(isinstance(o, PSeq(int, MyClass)[1]))
    Assert(PSeq(int, MyClass)[1] == MyClass)
    Assert(isinstance(o, MyClass))


def tester23(t: type) -> None:
    Requires(t in PSet(int, MyClass))
    Assert(t == int or t == MyClass)


# The mirror image of tester15: a type object on the right hand side of a
# comparison whose left hand side is not a type.
def tester24(o: object) -> None:
    b = o == MyClass


# A type-typed parameter in an overridden method, so that the behavioural
# subtyping check has to relate two type-typed arguments.
class Base:
    def m(self, t: type) -> bool:
        Requires(t == MyClass)
        Ensures(Result())
        return True


class Derived(Base):
    def m(self, t: type) -> bool:
        Requires(t == MyClass)
        Ensures(Result())
        return True
