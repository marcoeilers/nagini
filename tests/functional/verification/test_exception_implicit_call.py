# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class RaisingAdd:
    def __init__(self) -> None:
        pass

    def __add__(self, other: 'RaisingAdd') -> 'RaisingAdd':
        Ensures(False)
        Exsures(ValueError, True)
        raise ValueError()


def caught_add() -> None:
    c = RaisingAdd()
    raised = False
    try:
        x = c + c
    except ValueError:
        raised = True
    assert raised


#:: ExpectedOutput(exhale.failed:assertion.false)
def undeclared_add() -> None:
    c = RaisingAdd()
    x = c + c


class RaisingRadd:
    def __init__(self) -> None:
        pass

    def __radd__(self, other: int) -> int:
        Ensures(False)
        Exsures(ValueError, True)
        raise ValueError()


def caught_radd() -> None:
    c = RaisingRadd()
    raised = False
    try:
        x = 1 + c
    except ValueError:
        raised = True
    assert raised


#:: ExpectedOutput(exhale.failed:assertion.false)
def undeclared_radd() -> None:
    c = RaisingRadd()
    x = 1 + c


class RaisingIadd:
    def __init__(self) -> None:
        pass

    def __iadd__(self, other: 'RaisingIadd') -> 'RaisingIadd':
        Ensures(False)
        Exsures(ValueError, True)
        raise ValueError()


def caught_iadd() -> None:
    c = RaisingIadd()
    raised = False
    try:
        c += c
    except ValueError:
        raised = True
    assert raised


#:: ExpectedOutput(exhale.failed:assertion.false)
def undeclared_iadd() -> None:
    c = RaisingIadd()
    c += c


class RaisingNeg:
    def __init__(self) -> None:
        pass

    def __neg__(self) -> 'RaisingNeg':
        Ensures(False)
        Exsures(ValueError, True)
        raise ValueError()


def caught_neg() -> None:
    c = RaisingNeg()
    raised = False
    try:
        x = -c
    except ValueError:
        raised = True
    assert raised


#:: ExpectedOutput(exhale.failed:assertion.false)
def undeclared_neg() -> None:
    c = RaisingNeg()
    x = -c


class RaisingContains:
    def __init__(self) -> None:
        pass

    def __contains__(self, item: int) -> bool:
        Ensures(False)
        Exsures(ValueError, True)
        raise ValueError()


def caught_contains() -> None:
    c = RaisingContains()
    raised = False
    try:
        x = 1 in c
    except ValueError:
        raised = True
    assert raised


#:: ExpectedOutput(exhale.failed:assertion.false)
def undeclared_contains() -> None:
    c = RaisingContains()
    x = 1 in c


class RaisingLen:
    def __init__(self) -> None:
        pass

    def __len__(self) -> int:
        Ensures(False)
        Exsures(ValueError, True)
        raise ValueError()


def caught_len() -> None:
    c = RaisingLen()
    raised = False
    try:
        x = len(c)
    except ValueError:
        raised = True
    assert raised


#:: ExpectedOutput(exhale.failed:assertion.false)
def undeclared_len() -> None:
    c = RaisingLen()
    x = len(c)


class RaisingGetitem:
    def __init__(self) -> None:
        pass

    def __getitem__(self, i: int) -> int:
        Ensures(False)
        Exsures(ValueError, True)
        raise ValueError()


def caught_getitem() -> None:
    c = RaisingGetitem()
    raised = False
    try:
        x = c[0]
    except ValueError:
        raised = True
    assert raised


#:: ExpectedOutput(exhale.failed:assertion.false)
def undeclared_getitem() -> None:
    c = RaisingGetitem()
    x = c[0]


class RaisingSetitem:
    def __init__(self) -> None:
        pass

    def __getitem__(self, i: int) -> int:
        return 0

    def __setitem__(self, i: int, v: int) -> None:
        Ensures(False)
        Exsures(ValueError, True)
        raise ValueError()


def caught_setitem() -> None:
    c = RaisingSetitem()
    raised = False
    try:
        c[0] = 1
    except ValueError:
        raised = True
    assert raised


#:: ExpectedOutput(exhale.failed:assertion.false)
def undeclared_setitem() -> None:
    c = RaisingSetitem()
    c[0] = 1


class RaisingEnter:
    def __init__(self) -> None:
        pass

    def __exit__(self, t: object, e: object, tb: object) -> bool:
        return t is None

    def __enter__(self) -> 'RaisingEnter':
        Ensures(False)
        Exsures(ValueError, True)
        raise ValueError()


def caught_enter() -> None:
    c = RaisingEnter()
    raised = False
    try:
        with c:
            pass
    except ValueError:
        raised = True
    assert raised


#:: ExpectedOutput(exhale.failed:assertion.false)
def undeclared_enter() -> None:
    c = RaisingEnter()
    with c:
        pass


class RaisingExit:
    def __init__(self) -> None:
        pass

    def __enter__(self) -> 'RaisingExit':
        return self

    def __exit__(self, t: object, e: object, tb: object) -> bool:
        Ensures(False)
        Exsures(ValueError, True)
        raise ValueError()


def caught_exit() -> None:
    c = RaisingExit()
    raised = False
    try:
        with c:
            pass
    except ValueError:
        raised = True
    assert raised


#:: ExpectedOutput(exhale.failed:assertion.false)
def undeclared_exit() -> None:
    c = RaisingExit()
    with c:
        pass


class RaisingSetter:
    def __init__(self) -> None:
        pass

    @property
    def p(self) -> int:
        return 0

    @p.setter
    def p(self, v: int) -> None:
        Ensures(False)
        Exsures(ValueError, True)
        raise ValueError()


def caught_setter() -> None:
    c = RaisingSetter()
    raised = False
    try:
        c.p = 1
    except ValueError:
        raised = True
    assert raised


#:: ExpectedOutput(exhale.failed:assertion.false)
def undeclared_setter() -> None:
    c = RaisingSetter()
    c.p = 1


def caught_setter_in_tuple() -> None:
    c = RaisingSetter()
    raised = False
    try:
        c.p, y = 1, 2
    except ValueError:
        raised = True
    assert raised


#:: ExpectedOutput(exhale.failed:assertion.false)
def undeclared_setter_in_tuple() -> None:
    c = RaisingSetter()
    c.p, y = 1, 2
