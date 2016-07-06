#:: IgnoreFile(/py2viper/issue/22/)
from py2viper_contracts.contracts import *


def bla() -> None:
    Requires(True and True and True)
    a = 2
