from contracts.contracts import *


#:: ExpectedOutput(invalid.program:function.return.missing)
@Pure
def somefunc(a: bool, b: int) -> bool:
    c = b == 56
    d = a and c
