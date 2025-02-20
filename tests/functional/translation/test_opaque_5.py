# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

# pure opaque not belonging to class
@Opaque
@Pure
#:: ExpectedOutput(invalid.program:invalid.opaque.function)
def foo() -> int:
    return 0