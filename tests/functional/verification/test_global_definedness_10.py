class A:
    pass

class B(A):
    pass


# undefined
#:: ExpectedOutput(assert.failed:assertion.false)
class D(C):
    pass

class C:
    pass