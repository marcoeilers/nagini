class A:
    pass

a = A()

#:: ExpectedOutput(assert.failed:assertion.false)
b = B()  # noqa: F821

class B:
    pass