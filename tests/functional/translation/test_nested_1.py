# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

class A:
    #:: ExpectedOutput(invalid.program:nested.class.declaration)
    class B:
        pass