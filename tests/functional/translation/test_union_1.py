from nagini_contracts.contracts import *
from typing import Union

class A:
    def foo(self) -> None:
        pass

class B:
    pass

def f(o: Union[A, B]) -> None:
    #:: ExpectedOutput(type.error:Some element of union has no attribute "foo")
    x = o.foo()
