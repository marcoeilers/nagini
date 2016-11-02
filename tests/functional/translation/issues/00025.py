#:: IgnoreFile(/py2viper/issue/25/)
from py2viper_contracts.contracts import *

class C:
    def __init__(self) -> None:
        self.f = 1

def bla(x: C) -> None:
    if Acc(x.f):
        pass
