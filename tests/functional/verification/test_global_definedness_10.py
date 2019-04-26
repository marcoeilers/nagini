# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

class A:
    pass

class B(A):
    pass


# undefined
#:: ExpectedOutput(assert.failed:assertion.false)
class D(C):  # noqa: F821
    pass

class C:
    pass