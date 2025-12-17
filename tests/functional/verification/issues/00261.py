# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

class A(int):
    pass

def client() -> None:
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert A(5) == 2

