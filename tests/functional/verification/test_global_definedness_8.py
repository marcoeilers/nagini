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