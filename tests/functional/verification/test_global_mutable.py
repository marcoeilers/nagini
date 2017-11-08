from nagini_contracts.contracts import *


a, d = 2, 5
b = [a]

def foo() -> int:
    Requires(Acc(a) and Acc(b) and a >= 1)
    global b, a
    a = 0  # b[0]
    b = [12]
    return a