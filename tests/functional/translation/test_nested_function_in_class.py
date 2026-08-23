# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


# Nested functions remain unsupported, including inside a nested class.
class Outer:
    class Inner:
        def method(self) -> None:
            #:: ExpectedOutput(invalid.program:nested.function.declaration)
            def local() -> None:
                pass
