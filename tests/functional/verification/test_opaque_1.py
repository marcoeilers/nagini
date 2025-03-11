# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

# check that if the foo is overridden the functions are opaque
# and the function definitions cannot be used in proofs
class X:
    @Pure
    def foo(self, i: int) -> int:
        Requires(i > 2)
        Ensures(Result() > 8)
        return i ** 2

class SubX(X):
    @Pure
    def foo(self, i: int) -> int:
        Requires(i > 1)
        Ensures(Result() > 9)
        return i ** 4 + 1

@Pure
def bar(x: X) -> int:
    Ensures(Result() > 8)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() > 15)
    Ensures(Result() != 16)
    i = 4
    a = x.foo(i)  # a = 4 * 4 = 16
    return a

@Pure
def baz(y: SubX) -> int:
    Ensures(Result() > 9)  # given from SubX.foo
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() > 16)  # could be proven only with the definition
    Ensures(Result() != 17)
    i = 2
    b = y.foo(i)  # b = 2^4 + 1 = 17
    return b

x = X()
y = SubX()
bar(x)
bar(y)
baz(y)