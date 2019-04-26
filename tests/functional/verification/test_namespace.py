# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
import resources.namespace_test as nt
from resources.namespace_test_3 import a_function, P as PPP


class Sub(nt.resources.namespace_test_2.Super):
    @Predicate
    def some_pred(self, i: int) -> bool:
        return i < OTHER_GLOBAL


GLOBAL = 43
OTHER_GLOBAL = 36


def a_method() -> bool:
    Ensures(not Result())
    return False


def constructor_isinstance() -> None:
    a = nt.Sub()
    b = Sub()
    Assert(isinstance(a, nt.resources.namespace_test_2.Super))
    Assert(isinstance(b, nt.resources.namespace_test_2.Super))
    Assert(not isinstance(b, nt.Sub))
    Assert(isinstance(a, nt.Sub))
    Assert(isinstance(a, object))
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(not isinstance(b, object))


def global_vars() -> None:
    Assert(GLOBAL == nt.GLOBAL + 1)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(nt.GLOBAL == 45)


def methods() -> None:
    a = a_method()
    b = nt.a_method()
    Assert(a == (not b))
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(not b)


def functions() -> None:
    a = a_function()
    b = nt.a_function()
    Assert(a == (not b))
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(b)


def static_call() -> int:
    Ensures(Result() > 40)
    a = Sub()
    return nt.resources.namespace_test_2.Super.get(a)


def static_call_2() -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() > 60)
    a = Sub()
    return nt.resources.namespace_test_2.Super.get(a)


def signature(a: Sub, b: nt.Sub, c: bool) -> nt.resources.namespace_test_2.Super:
    Ensures(Implies(c, isinstance(Result(), Sub)))
    Ensures(Implies(not c, isinstance(Result(), nt.Sub)))
    if c:
        return a
    return b


def catches() -> None:
    try:
        raise nt.SpecificException()
    except nt.SpecificException:
        pass


def throws() -> None:
    Exsures(nt.SpecificException, True)
    raise nt.SpecificException()


def pred_use(i: int) -> None:
    Requires(nt.resources.namespace_test_2.B(i))
    Ensures(Acc(nt.PP(i)))
    Unfold(nt.resources.namespace_test_2.B(i))
    Fold(PPP(i))
    Fold(nt.PP(i))


def pred_fam_use(u: int, s: Sub) -> None:
    Requires(s.some_pred(u))
    Ensures(Acc(s.some_pred(u)))
    Unfold(s.some_pred(u))
    Assert(u == 35)
    Fold(s.some_pred(u))
