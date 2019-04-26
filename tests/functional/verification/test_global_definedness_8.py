# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

def foo() -> 'A':
    return A()

class B:
    pass

def baz() -> B:
    return B()

#:: ExpectedOutput(assert.failed:assertion.false)
def bar() -> A:  # noqa: F821
    return A()

class A:
    pass