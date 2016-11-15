from py2viper_contracts.contracts import *


def list_loop() -> None:
    b = [1, 2, 3]
    a = [b, [4, 5]]
    for c in a:
        #:: ExpectedOutput(invalid.program:invalid.previous)
        Invariant(len(Previous(b)) > 2)
        c.append(7)
    a.append([4])