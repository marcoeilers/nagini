from typing import List

from nagini_contracts.contracts import *

def check(password: List[str], inpt: List[str]) -> bool:
    Requires(list_pred(password) and list_pred(inpt))
    Requires(Low(inpt))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Low(Result()))
    result = len(password) == len(inpt)
    i = 0
    while i < min(len(password), len(inpt)):
        Invariant(list_pred(password) and list_pred(inpt))
        Invariant(i >= 0 and i <= len(password) and i <= len(inpt))
        result = result and password[i] == inpt[i]
        i += 1
    return result

def check_fixed(password: List[str], inpt: List[str]) -> bool:
    Requires(list_pred(password) and list_pred(inpt))
    Requires(Low(inpt))
    Ensures(Low(Result()))
    result = len(password) == len(inpt)
    i = 0
    while i < min(len(password), len(inpt)):
        Invariant(list_pred(password) and list_pred(inpt))
        Invariant(i >= 0 and i <= len(password) and i <= len(inpt))
        result = result and password[i] == inpt[i]
        i += 1
    Declassify(result)
    return result
