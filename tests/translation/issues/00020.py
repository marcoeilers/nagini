#:: IgnoreFile(/py2viper/issue/20/)
from py2viper_contracts.contracts import *

x = 4

if False:
    x = 5

def bla() -> None:
    Requires(True)
    Ensures(x == 5)
    pass
