# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

class A:
    pass

a = A()

#:: ExpectedOutput(assert.failed:assertion.false)
b = B()  # noqa: F821

class B:
    pass