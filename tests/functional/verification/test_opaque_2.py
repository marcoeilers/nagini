# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

# check that if the foo is NOT overridden the functions is NOT opaque
# and the function implementation can be used in the proof
class X:
    @Pure
    def foo(self, i: int) -> int:
        Requires(i > 2)
        Ensures(Result() > 8)
        return i ** 2

@Pure
def bar(x: X) -> int:
    Ensures(Result() > 8)
    Ensures(Result() == 16)
    i = 4
    a = x.foo(i)  # a = 4 * 4 = 16
    return a

# @Pure
# def baz(y: SubX) -> int:
#     Ensures(Result() > 9)
#     #:: ExpectedOutput(postcondition.violated:assertion.false)
#     Ensures(Result() > 16)
#     i = 2
#     b = y.foo(i)  # b = 2^4 + 1 = 17
#     return b


x = X()
bar(x)