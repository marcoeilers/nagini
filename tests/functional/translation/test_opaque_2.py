# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

# impure opaque
class A:
    @Opaque
    #:: ExpectedOutput(invalid.program:invalid.opaque.method)
    def foo(self) -> int:
        return 0
