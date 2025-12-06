# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from enum import IntEnum

# class flag(int):
#     pass

# def test() -> None:
#     f = flag(1)    
#     assert f == flag(1)

class flag(IntEnum):
    success = 0
    failure = 1
    
def test() -> None:
    f = flag(1)
    
    assert f == flag(1)
    assert f == 1