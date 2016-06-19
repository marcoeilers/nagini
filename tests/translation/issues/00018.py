#:: IgnoreFile(/py2viper/issue/18/)
from py2viper_contracts.contracts import *

def foo() -> None:
    while True:
        a = True
        Invariant(a)
