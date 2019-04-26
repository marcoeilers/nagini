# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


@Pure
def func1() -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 16)
    return 15


@Pure
def func2() -> int:
    Ensures(Result() == 16)
    return 16


@Pure
def func3() -> bool:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result())
    return False


@Pure
def func4() -> bool:
    Ensures(Result() == True)
    return True


@Pure
def func5(a: int) -> int:
    Ensures(Result() == a)
    return a


@Pure
def func6(other_name: int) -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == other_name)
    return 17


@Pure
def func7(other_name: int) -> int:
    Requires(other_name > 5)
    Ensures(Result() > 7)
    return other_name + 2


@Pure
def func8(other_name: int) -> int:
    Requires(other_name > 5)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() > 7)
    return other_name - 2


@Pure
def func9(some_name: int, other_name: int, other_third: bool) -> bool:
    Requires(other_name > 5)
    Requires(some_name > 17)
    Requires(other_third)
    Ensures(Result() == other_third)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == False)
    return other_third == (some_name + other_name > 22)


@Pure
def func10(some_name: int, other_name: int, other_third: bool) -> bool:
    Requires(other_name > 5)
    Requires(some_name > 17)
    Ensures(Result() == other_third)
    return other_third == (some_name + other_name > 22)


@Pure
def func11(some_name: int, other_name: int, other_third: bool) -> bool:
    Requires(other_name > 5)
    Requires(some_name > 17)
    Requires(other_third)
    Ensures(Result() == other_third)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == False)
    a = some_name
    c = 22
    b = (a + other_name > c)
    res = other_third == b
    return res


@Pure
def func12(some_name: int, other_name: int, other_third: bool) -> bool:
    Requires(other_name > 5)
    Requires(some_name > 17)
    Ensures(Result() == other_third)
    a = some_name
    c = 22
    b = (a + other_name > c)
    res = other_third == b
    return other_third == b
