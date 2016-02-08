from contracts.contracts import *


class MyException(Exception):
    pass


class MySpecialException(MyException):
    pass


class MyOtherException(Exception):
    pass


class Container:
    def __init__(self) -> None:
        Ensures(Acc(self.value))  # type: ignore
        self.value = 0


def raisedAndDeclared(input: int, inCon: Container) -> Container:
    Requires(inCon != None and Acc(inCon.value))
    Ensures(Acc(inCon.value) and (
        Result() != None and (Acc(Result().value) and Result().value == input)))
    Exsures(MyException, Acc(inCon.value) and inCon.value == -1)
    res = Container()
    inCon.value = -1
    if input == 22:
        raise MyException()
    res.value = input
    return res


def raisedAndDeclared2(input: int, inCon: Container) -> Container:
    Requires(inCon != None and Acc(inCon.value))
    Ensures(Acc(inCon.value) and (
        Result() != None and (Acc(Result().value) and Result().value == input)))
    Exsures(Exception, Acc(inCon.value) and inCon.value == -1)
    res = Container()
    inCon.value = -1
    if input == 22:
        raise MyException()
    res.value = input
    return res


def raisedAndDeclared3(input: int, inCon: Container) -> None:
    Requires(inCon != None and Acc(inCon.value))
    Ensures(False)
    Exsures(MyException, Acc(inCon.value) and inCon.value == -2)
    inCon.value = -2
    raise MyException()


def raisedAndDeclared4(input: int, inCon: Container) -> None:
    Requires(inCon != None and Acc(inCon.value))
    Ensures(False)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Exsures(MyException, Acc(inCon.value) and inCon.value == -3)
    inCon.value = -2
    raise MyException()


def raisedAndDeclared5(input: int, inCon: Container) -> None:
    Requires(inCon != None and Acc(inCon.value))
    Ensures(False)
    Exsures(MyException, Acc(inCon.value) and inCon.value == -3)
    Exsures(MyOtherException, True)
    inCon.value = -3
    raise MyException()


def raisedAndUndeclared(input: int, inCon: Container) -> Container:
    Requires(inCon != None and Acc(inCon.value))
    Ensures(Acc(inCon.value) and (
        Result() != None and (Acc(Result().value) and Result().value == input)))
    res = Container()
    inCon.value = -1
    if input == 22:
        #:: ExpectedOutput(exhale.failed:assertion.false)
        raise MyException()
    res.value = input
    return res


# TODO: This doesn't work at the moment because the subtype axioms are too weak
#   axioms are too weak
# def raisedAndDeclared6(input: int, inCon: Container) -> None:
#     Requires(inCon != None and Acc(inCon.value))
#     Ensures(False)
#     Exsures(MyException, Acc(inCon.value) and inCon.value == -3)
#     Exsures(MyOtherException, True)
#     if input > 2:
#         inCon.value = -3
#         raise MyException()
#     else:
#         raise MyOtherException()

def helper(out: Container, i: int) -> None:
    Requires(Acc(out.value))
    Ensures(Acc(out.value) and out.value == 12)
    Exsures(MyException, Acc(out.value) and out.value == 13)
    if i > 34:
        out.value = 13
        raise MyException()
    else:
        out.value = 12


def raisedAndCaught(out: Container) -> None:
    Requires(Acc(out.value))
    Ensures(Acc(out.value) and out.value == 12)
    Exsures(MyException, False)
    try:
        raise MyException()
    except MyException:
        out.value = 12


def raisedAndCaught2(out: Container) -> None:
    Requires(Acc(out.value))
    Ensures(Acc(out.value) and (out.value == 24 or out.value == 39))
    tmp = Container()
    try:
        helper(tmp, 45)
        out.value = 2 * tmp.value
    except MyException:
        out.value = 3 * tmp.value
