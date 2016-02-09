from contracts.contracts import *


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
def func6(othername: int) -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == othername)
    return 17


@Pure
def func7(othername: int) -> int:
    Requires(othername > 5)
    Ensures(Result() > 7)
    return othername + 2


@Pure
def func8(othername: int) -> int:
    Requires(othername > 5)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() > 7)
    return othername - 2


@Pure
def func9(somename: int, othername: int, otherthird: bool) -> bool:
    Requires(othername > 5)
    Requires(somename > 17)
    Requires(otherthird)
    Ensures(Result() == otherthird)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == False)
    return otherthird == (somename + othername > 22)


@Pure
def func10(somename: int, othername: int, otherthird: bool) -> bool:
    Requires(othername > 5)
    Requires(somename > 17)
    Ensures(Result() == otherthird)
    return otherthird == (somename + othername > 22)


@Pure
def func11(somename: int, othername: int, otherthird: bool) -> bool:
    Requires(othername > 5)
    Requires(somename > 17)
    Requires(otherthird)
    Ensures(Result() == otherthird)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == False)
    a = somename
    c = 22
    b = (a + othername > c)
    res = otherthird == b
    return res


@Pure
def func12(somename: int, othername: int, otherthird: bool) -> bool:
    Requires(othername > 5)
    Requires(somename > 17)
    Ensures(Result() == otherthird)
    a = somename
    c = 22
    b = (a + othername > c)
    res = otherthird == b
    return otherthird == b
