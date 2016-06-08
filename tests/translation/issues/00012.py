#:: IgnoreFile(/py2viper/issue/12/)
from py2viper_contracts.contracts import *

@Predicate
def test1(x: int):
    return x == 5
