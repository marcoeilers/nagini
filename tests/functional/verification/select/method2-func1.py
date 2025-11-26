# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


@Pure
def func1(b: int) -> int:
    Requires(b == 15)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 32)
    a = 16
    return b + a

@Pure
def func2(b: int) -> int:
    Requires(b == 15)
    #ExpectedOutput(postcondition.violated:assertion.false)  # not selected
    Ensures(Result() == 32)
    a = 14
    return b + a

def method1(b: int) -> int:
    Requires(b == 15)
    #ExpectedOutput(postcondition.violated:assertion.false)  # not selected
    Ensures(Result() == 32)
    a = 16
    return b + a

def method2(b: int) -> int:
    Requires(b == 15)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 32)
    a = 14
    return b + a

