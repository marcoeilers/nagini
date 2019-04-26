# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from typing import Union


class A:
    pass


class B:
    pass


class BSub(B):
    pass


class BSubSub(BSub):
    pass


class C:
    pass


def m(u: Union[A, B]) -> Union[A, B]:
    return A()


def m2(u: Union[A, B]) -> Union[A, B]:
    return B()


def m3(u: Union[A, B]) -> Union[A, B]:
    return BSub()


def m4(u: Union[A, B]) -> Union[A, B]:
    return BSubSub()


def m_client() -> None:
    a = A()
    b = B()
    c = C()
    ma = m(a)
    mb = m(b)


def m_client2() -> None:
    a = A()
    b = B()
    c = C()
    ma = m(a)
    mb = m(b)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert isinstance(ma, A)


def m_client3() -> None:
    a = A()
    b = B()
    c = C()
    ma = m(a)
    mb = m(b)

    if isinstance(ma, A):
        #:: ExpectedOutput(assert.failed:assertion.false)
        assert isinstance(mb, A)


def m_client4() -> None:
    a = A()
    b = B()
    c = C()
    ma = m(a)
    mb = m(b)
    assert isinstance(ma, A) or isinstance(ma, B)
    assert not isinstance(ma, C)


def m_client5() -> None:
    a = A()
    b = B()
    c = C()
    ma = m(a)
    mb = m(b)
    if not isinstance(ma, B):
        assert isinstance(ma, A)


def m5(u: Union[A, B], a: A) -> None:
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert a is not u


def m6(u: Union[C, B], a: A) -> None:
    assert a is not u
