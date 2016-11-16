from py2viper_contracts.contracts import *

x = 4

#:: ExpectedOutput(invalid.program:global.statement)
if False:
    x = 5

def bla() -> None:
    Requires(True)
    Ensures(x == 5)
    pass
