# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/


class A(int):
    pass

def client() -> None:
    assert A(5) == 5
    assert A() == 0
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False


class B(int):
    def __init__(self, o: int) -> None:
        pass


class C(A):
    pass

def client2() -> None:
    assert B(4) == 0
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert B(5) == 5


def client3() -> None:
    a = A()
    assert isinstance(a, A)
    assert isinstance(a, int)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert isinstance(a, B)


def client4() -> None:
    a1 = A(2)
    a2 = A(2)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert a1 is a2


def client5() -> None:
    a1 = A(2)
    a2 = 2
    assert a1 is not a2
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False


def client6() -> None:
    assert C(5) == 5
    assert C() == 0
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False
