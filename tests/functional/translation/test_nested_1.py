from nagini_contracts.contracts import *

class A:
    #:: ExpectedOutput(invalid.program:nested.class.declaration)
    class B:
        pass