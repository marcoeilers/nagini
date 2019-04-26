# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from resources.test_import_file import test_func, test_method

@Pure
def local_func() -> bool:
    Ensures(Result())
    return test_func()

def local_method(b: int) -> int:
    Ensures(Result() >= 2)
    Ensures(Implies(b - 2 > 0, Result() < b))
    Ensures(Implies(b - 2 <= 0, Result() == 2))
    return test_method(b - 2) + 2

@Pure
def local_func_wrong() -> bool:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(not Result())
    return test_func()

def local_method_wrong(b: int) -> int:
    Ensures(Result() >= 2)
    Ensures(Implies(b - 2 > 0, Result() < b))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Implies(b - 2 <= 0, Result() == 0))
    return test_method(b - 2) + 2

