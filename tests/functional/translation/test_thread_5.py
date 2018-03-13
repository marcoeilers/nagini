from nagini_contracts.thread import arg
from nagini_contracts.contracts import *

def test(o: object) -> None:
    #:: ExpectedOutput(invalid.program:invalid.arg.use)
    Requires(arg(1) == o)
    pass