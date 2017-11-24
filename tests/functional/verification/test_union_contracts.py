from nagini_contracts.contracts import *
from typing import Union

class A:
    def foo(self, i: int) -> int:
        Requires(True)
        Ensures(Result() == 4)
        return 4
 
class B:
    def foo(self, i: int) -> int:
        Requires(i > 0)
        Ensures(Result() == 6)
        return 6

class C:
    def foo(self, i: int) -> str:
        Requires(True)
        Ensures(Result() == '4')
        return '4'

def a(o: Union[A, B]) -> None:
    x = o.foo(5)

def b(o: Union[A, B, C]) -> None:
    x = o.foo(5)

def c(o: Union[A, B]) -> None:
    #:: ExpectedOutput(call.precondition:assertion.false)
    x = o.foo(-5)

def d(o: Union[A, B, C]) -> None:
    #:: ExpectedOutput(call.precondition:assertion.false)
    x = o.foo(-5)

def e(o: Union[A, B]) -> None:
    if isinstance(o, A):
        x = o.foo(-2)
        assert x == 4
    if isinstance(o, B):
        x = o.foo(34) 
        assert x == 6
        #:: ExpectedOutput(call.precondition:assertion.false)
        x = o.foo(-34)

def f(o: Union[A, B], i: int) -> None:
    if isinstance(o, B):
        #:: ExpectedOutput(call.precondition:assertion.false)
        x = o.foo(i) 

def g(o: Union[A, B], i: int) -> None:
    #:: ExpectedOutput(call.precondition:assertion.false)
    x = o.foo(i)

def h(o: Union[A, B], i: int) -> None:
    if i > 0:
        x = o.foo(i)
        assert x == 4 or x == 6

def i(o: Union[A, B], j: int) -> None:
    Requires(j > 0)
    o.foo(j)

def j(o: Union[A, B], i: int) -> int:
    Requires(i > 0)
    Ensures(Result() == 4 or Result() == 6)
    return o.foo(i)

def k(o: Union[A, Union[B, C]]) -> None:
    x = o.foo(5)

def l(o: Union[Union[B, C]]) -> None:
    x = o.foo(5)

def m(o: Union[A]) -> None:
    x = o.foo(5)