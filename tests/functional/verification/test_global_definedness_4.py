# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

def foo_1() -> int:
    return bar_1()

def bar_1() -> int:
    return baz_1()

def baz_1() -> int:
    return 12

f1 = foo_1()

def foo_2() -> int:
    return bar_2()

def bar_2() -> int:
    return baz_2()

#:: ExpectedOutput(assert.failed:assertion.false)
f2 = foo_2()

def baz_2() -> int:
    return 12