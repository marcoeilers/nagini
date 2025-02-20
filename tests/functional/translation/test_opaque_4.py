# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

# Basic opaque tests
class A:
    @Pure
    @Opaque
    def foo(self) -> int:
        return 0

# pure opaque override
class SubA(A):
    @Pure
    @Opaque
    def foo(self) -> int:
        return 1

# pure opaque override of subclass function
class SubSubA(SubA):
    @Pure
    @Opaque
    def foo(self) -> int:
        return 2 

# impure and opaque override
class SubSubSubA(SubSubA):
    @Opaque
    #:: ExpectedOutput(invalid.program:invalid.opaque.method)
    def foo(self) -> int:
        return 1
