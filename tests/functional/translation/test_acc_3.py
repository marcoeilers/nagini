from nagini_contracts.contracts import *

a = 12

def main() -> None:
    #:: ExpectedOutput(invalid.program:permission.to.final.var)
    Requires(Acc(a))