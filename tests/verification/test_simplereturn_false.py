from contracts import *

@Pure
def func1() -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 16)
    return  15