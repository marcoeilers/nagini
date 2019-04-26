# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

def foo(a: 'A') -> int:
    return 12

class B:
    pass

def baz(b: B) -> int:
    return 12

#:: ExpectedOutput(assert.failed:assertion.false)
def bar(a: A) -> int:  # noqa: F821
    return 12

class A:
    pass