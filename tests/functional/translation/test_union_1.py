# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Union

class A:
    def __init__(self) -> None:
        self.field = 5

    def method(self) -> None:
        pass

class B:
    pass

def test_1(o: Union[A, B]) -> None:
    #:: ExpectedOutput(type.error:Some element of union has no attribute "method")
    x = o.method()

def test_2(o: Union[A, B]) -> None:
    #:: ExpectedOutput(type.error:Some element of union has no attribute "field")
    x = o.field

def test_3(o: Union[A, B]) -> None:
    #:: ExpectedOutput(type.error:Some element of union has no attribute "field")
    o.field = 5
