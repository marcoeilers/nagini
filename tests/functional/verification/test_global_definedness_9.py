class B:
    bar = 12


def baz(b: object = B.bar) -> int:
    return 12


# undefined A
#:: ExpectedOutput(assert.failed:assertion.false)
def foo(a: object = A.bar) -> int:
    return 12

class A:
    bar = 12