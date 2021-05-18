# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

from typing import cast

class Example:
    def __init__(self) -> None:
        self.f = 0
        self.g = 1
        Ensures(Acc(self.f) and Acc(self.g))
        Ensures(self.f == 0 and self.g == 1)

    # LowVal currently doesn't support __eq__ for objects, will just use reference equality.
    # Currently Nagini doesn't allow overriding __eq__ anyway.
    # @Pure
    # def __eq__(self, other: object) -> bool:
    #     Requires(Acc(self.f, 1/4))
    #     Requires(Implies(isinstance(other, Example), Acc(cast(Example, other).f, 1/4)))
    #     if isinstance(other, Example):
    #         return self.f == cast(Example, other).f and self.g == cast(Example, other).g
    #     return cast(object, self).__eq__(other)

class StringContainer:
    def __init__(self, s: str) -> None:
        self.s = s
        Ensures(Acc(self.s))
        Ensures(self.s == s)

def example_low(secret: bool) -> Example:
    Ensures(Acc(Result().f) and Acc(Result().g))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Low(Result()))
    a = Example()
    b = Example()
    if secret:
        return a
    return b

def example_lowval(secret: bool) -> Example:
    Ensures(Acc(Result().f) and Acc(Result().g))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(LowVal(Result())) # for objects the same as Low.
    a = Example()
    b = Example()
    if secret:
        return a
    return b

def example_tuple_low(secret: bool) -> Example:
    Ensures(Acc(Result().f) and Acc(Result().g))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Low((Result().f, Result().g)))
    a = Example()
    b = Example()
    if secret:
        return a
    return b

def example_tuple_lowval(secret: bool) -> Example:
    Ensures(Acc(Result().f) and Acc(Result().g))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(LowVal((Result().f, Result().g)))
    a = Example()
    b = Example()
    if secret:
        return a
    return b

def example_each_field_lowval(secret: bool) -> Example:
    Ensures(Acc(Result().f) and Acc(Result().g))
    Ensures(LowVal(Result().f) and LowVal(Result().g))
    a = Example()
    b = Example()
    if secret:
        return a
    return b

def int_constant(secret: bool) -> int:
    Ensures(Low(Result()))
    if secret:
        return 1
    return 1

def int_unchanged_low(secret: int, x: int) -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Implies(Low(x), Low(Result())))
    if secret == 0:
        return x + secret
    return x

def int_unchanged_lowval(secret: int, x: int) -> int:
    Ensures(Implies(Low(x), LowVal(Result())))
    if secret == 0:
        return x + secret
    return x

def bool_int(secret: bool) -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Low(Result()))
    if secret:
        return 1
    return True

def bool_int_lowval(secret: bool) -> int:
    Ensures(LowVal(Result()))
    if secret:
        return 1
    return True

def string_container_low(secret: bool, x: str) -> str:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Implies(Low(x), Low(Result())))
    a = StringContainer(x)
    b = StringContainer(x)
    if secret:
        return a.s
    return b.s

def string_container_lowval(secret: bool, x: str) -> str:
    Ensures(Implies(Low(x), LowVal(Result())))
    a = StringContainer(x)
    b = StringContainer(x)
    if secret:
        return a.s
    return b.s
