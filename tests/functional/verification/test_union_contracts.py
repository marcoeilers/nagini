from nagini_contracts.contracts import *
from typing import Union

class A:
    def __init__(self) -> None:
        self.field = 5

    def foo(self, i: int) -> int:
        Requires(True)
        Ensures(Result() == 4)
        return 4
 
class B:
    def __init__(self) -> None:
        self.field = 'B'

    def foo(self, i: int) -> int:
        Requires(i > 0)
        Ensures(Result() == 6)
        return 6

class C:
    def foo(self, i: int) -> str:
        Requires(True)
        Ensures(Result() == '5')
        return '5'

# Method calls

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

# Method calls when classes belong to an hierarchy

class Base:
    def foo(self, i: int) -> int:
        Requires(i > 3)
        Ensures(Result() > 3)
        return 4

class DerivedLeft (Base):
    def foo(self, i: int) -> int:
        Requires(i > 2)
        Ensures(Result() > 5)
        return 6

class DerivedRight (Base):
    def foo(self, i: int) -> int:
        Requires(i > 2)
        Ensures(Result() > 5)
        return 6

class SingleInheritanceLeft(DerivedRight):
    def foo(self, i: int) -> int:
        Requires(i > 1)
        Ensures(Result() > 6)
        return 7

class SingleInheritanceRight(DerivedRight):
    def foo(self, i: int) -> int:
        Requires(i > 1)
        Ensures(Result() > 6)
        return 7

def test_15(o: Union[Base, DerivedLeft]) -> None:
    x = o.foo(5)
 
def test_16(o: Union[DerivedLeft, Base]) -> None:
    x = o.foo(5)
 
def test_17(o: Union[DerivedLeft, DerivedRight, Base, SingleInheritanceLeft]) -> None:
    x = o.foo(5)

class DataStructure:
    def append(self, item: int) -> None:
        pass

# Mixing native types with user defined ones

def test_18(o: Union[DataStructure, List[int]]) -> None:
    Requires(Implies(not isinstance(o, DataStructure), Acc(list_pred(o))))
    o.append(5)

# Accessing fields for reading and writing

def test_19(o: Union[A, B]) -> None:
    Requires(Acc(o.field))
    x = o.field

def test_20(o: Union[A, B]) -> None:
    Requires(Acc(o.field))
    o.field = 5
