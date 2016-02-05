from contracts.contracts import *

class MyException(Exception):
    pass

#:: ExpectedOutput(invalid.program:function.throws.exception)
@Pure
def someFunction(a: int) -> int:
    Ensures(Result() > 17)
    Exsures(MyException, True)
    return 18