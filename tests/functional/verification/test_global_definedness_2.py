# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/


def foo() -> int:
    return 12

foo()

#:: ExpectedOutput(assert.failed:assertion.false)
bar()  # noqa: F821

def bar() -> int:
    return 12