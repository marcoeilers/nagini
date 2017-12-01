
def foo() -> int:
    return 12

foo()

#:: ExpectedOutput(assert.failed:assertion.false)
bar()

def bar() -> int:
    return 12