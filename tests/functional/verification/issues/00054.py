# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/



def foo() -> int:
    return 1


def test1() -> None:
    try:
        x = foo()
    except:
        pass


def test2() -> None:
    try:
        x = 5
    except:
        pass
