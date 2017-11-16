class A:
    bar = 12


class C:
    baz = A.bar


# undefined
#:: ExpectedOutput(assert.failed:assertion.false)
class D:
    baz = B.bar

class B:
    bar = 12