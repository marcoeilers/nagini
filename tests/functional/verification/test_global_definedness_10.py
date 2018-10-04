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