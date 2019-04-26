# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

class A:
    def foo(self) -> int:
        return a_const

a_const = 12


def bar(a: A) -> int:
    return a.foo()

bar(A())

class B(A):
    def foo(self) -> int:
        return b_const

b_const = 14

bar(A())


class C(A):
    def foo(self) -> int:
        return c_const


#:: ExpectedOutput(assert.failed:assertion.false)
bar(A())

c_const = 14
