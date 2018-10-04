
def foo() -> int:
    return 12

foo()

#:: ExpectedOutput(assert.failed:assertion.false)
bar()  # noqa: F821

def bar() -> int:
    return 12