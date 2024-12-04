# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.obligations import MustTerminate
from nagini_contracts.contracts import *

@Inline
def power3_A(input: int) -> int:
    out_a = input
    try:

        for i in range(2):
            Invariant(out_a == input * (input ** len(Previous(i))))
            try:
                out_a = out_a * input
                out_a -= 5
            finally:
                out_a = out_a + 5
    finally:
        out_a = out_a - 5
    return out_a + 5


@Inline
def power3_B(input: int) -> int:
    i = 0
    out_b = input
    while i < 2:
        Invariant(0 <= i and i <= 2)
        Invariant(out_b == input * (input ** i))
        out_b = out_b * input
        i += 1
    return out_b

@Inline
def not_always_correct(i: int, j: int) -> int:
    if j < 0:
        assert False  # would lead to an error but is not reached by any call

    if i == 0:
        res = 8
        #:: ExpectedOutput(assert.failed:assertion.false,L1)
        assert False # would lead to an error
    elif i > 0:
        res = 14
    else:
        res = 9
    return res

def partly_correct_caller() -> None:
    tst = not_always_correct(5, 8)
    Assert(tst == 14)
    #:: Label(L1)
    tst = not_always_correct(0, 8)

@Inline
def may_not_terminate(i: int) -> None:
    will_terminate = i >= 0
    #:: ExpectedOutput(leak_check.failed:loop_context.has_unsatisfied_obligations,L2)
    while i != 0:
        Invariant(Implies(will_terminate, MustTerminate(i)))
        i -= 1

def should_terminate() -> None:
    Requires(MustTerminate(5))

    may_not_terminate(8)

    #:: Label(L2)
    may_not_terminate(-6)


class A:
    @Inline
    def foo(self) -> int:
        return 1

    def bar(self) -> int:
        return 1

def test_calls(input: int, a: A) -> None:
    Requires(input > 0)
    Assert(a.foo() == 1)

    Assert(power3_A(input) == power3_B(input))

    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(a.bar() == 1)

@Inline
def plus_two(i: int) -> int:
    a = i + 2
    return a

@Inline
def plus_seven(i: int) -> int:
    a = plus_two(i)
    b = plus_two(a)
    return b + 3

def nested_caller() -> None:
    Assert(plus_seven(9) == 16)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(plus_seven(5) == 13)

@Inline
def raises(a: int) -> None:
    if a > 0:
        raise Exception

@Inline
def raises_and_catches(b: int) -> int:
    r = 9
    try:
        if b == 9:
            raise Exception
        r = 7
    except:
        r = 12
    return r

def calls_raises_1() -> int:
    Ensures(Result() == 8888)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(False)
    r = 43

    try:
        r = 12
        raises(-3)
        r = 456
        raises(4)
        r = 2
    except:
        Assert(r == 456)
        r = 8888
    return r

#:: ExpectedOutput(exhale.failed:assertion.false,L3)
def calls_raises_2() -> None:
    #:: Label(L3)
    raises(8)  # error bc raises exception

def calls_raises_3(i: int) -> None:
    Ensures(i <= 0)
    Exsures(Exception, i > 0)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Exsures(Exception, False)
    raises(i)

def calls_raises_and_catches_1() -> None:
    raises_and_catches(12)

    raises_and_catches(9)

    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(False)

