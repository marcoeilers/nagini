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
        Ensures(Result() == '5')
        return '5'

def test_1(o: Union[A, B]) -> None:
    x = o.foo(5)

def test_2(o: Union[A, B, C]) -> None:
    x = o.foo(5)

def test_3(o: Union[A, B]) -> None:
    #:: ExpectedOutput(call.precondition:assertion.false)
    x = o.foo(-5)

def test_4(o: Union[A, B, C]) -> None:
    #:: ExpectedOutput(call.precondition:assertion.false)
    x = o.foo(-5)

def test_5(o: Union[A, B]) -> None:
    if isinstance(o, A):
        x = o.foo(-2)
        assert x == 4
    if isinstance(o, B):
        x = o.foo(34) 
        assert x == 6
        #:: ExpectedOutput(call.precondition:assertion.false)
        x = o.foo(-34)

def test_6(o: Union[A, B], i: int) -> None:
    if isinstance(o, B):
        #:: ExpectedOutput(call.precondition:assertion.false)
        x = o.foo(i) 

def test_7(o: Union[A, B], i: int) -> None:
    #:: ExpectedOutput(call.precondition:assertion.false)
    x = o.foo(i)

def test_8(o: Union[A, B], i: int) -> None:
    if i > 0:
        x = o.foo(i)
        assert x == 4 or x == 6

def test_9(o: Union[A, B], j: int) -> None:
    Requires(j > 0)
    o.foo(j)

def test_10(o: Union[A, B], i: int) -> int:
    Requires(i > 0)
    Ensures(Result() == 4 or Result() == 6)
    return o.foo(i)

def test_11(o: Union[A, Union[B, C]]) -> None:
    x = o.foo(5)

def test_12(o: Union[Union[B, C]]) -> None:
    x = o.foo(5)

def test_13(o: Union[Union[A, B], C]) -> None:
    x = o.foo(5)

def test_14(o: Union[A]) -> None:
    x = o.foo(5)
