from contracts.contracts import *

@Pure
def func1() -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 16)
    return  15

@Pure
def func2() -> int:
    Ensures(Result() == 16)
    return  16

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
def func6(otherName: int) -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == otherName)
    return 17

@Pure
def func7(otherName: int) -> int:
    Requires(otherName > 5)
    Ensures(Result() > 7)
    return otherName + 2

@Pure
def func8(otherName: int) -> int:
    Requires(otherName > 5)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() > 7)
    return otherName - 2

@Pure
def func9(someName: int, otherName: int, thirdName : bool) -> bool:
    Requires(otherName > 5)
    Requires(someName > 17)
    Requires(thirdName)
    Ensures(Result() == thirdName)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == False)
    return thirdName == (someName + otherName > 22)

@Pure
def func10(someName: int, otherName: int, thirdName : bool) -> bool:
    Requires(otherName > 5)
    Requires(someName > 17)
    Ensures(Result() == thirdName)
    return thirdName == (someName + otherName > 22)

@Pure
def func11(someName: int, otherName: int, thirdName : bool) -> bool:
    Requires(otherName > 5)
    Requires(someName > 17)
    Requires(thirdName)
    Ensures(Result() == thirdName)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == False)
    a = someName
    c = 22
    b = (a + otherName > c)
    res = thirdName == b
    return res

@Pure
def func12(someName: int, otherName: int, thirdName : bool) -> bool:
    Requires(otherName > 5)
    Requires(someName > 17)
    Ensures(Result() == thirdName)
    a = someName
    c = 22
    b = (a + otherName > c)
    res = thirdName == b
    return thirdName == b
