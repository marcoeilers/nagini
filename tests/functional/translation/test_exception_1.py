# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class MyException(Exception):
    pass


#:: ExpectedOutput(invalid.program:function.throws.exception)
@Pure
def some_function(a: int) -> int:
    Ensures(Result() > 17)
    Exsures(MyException, True)
    return 18
