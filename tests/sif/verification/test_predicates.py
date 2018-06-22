from nagini_contracts.contracts import *
from typing import Optional

class ListClass():
    def __init__(self, v: int) -> None:
        Ensures(MyList(self))
        Ensures(size(self) == 1)
        self.val = v
        self.next = None #type: Optional[ListClass]
        Fold(MyList(self.next))
        Fold(MyList(self))

@Predicate
def accVal(l: ListClass) -> bool:
    return Acc(l.val) and Low(l.val)

@Pure
def getVal(l: ListClass) -> int:
    Requires(accVal(l))
    return Unfolding(accVal(l), l.val)

def setValMethod(l: ListClass, v: int) -> None:
    Requires(accVal(l))
    Ensures(accVal(l))
    Ensures(getVal(l) == v)
    Unfold(accVal(l))
    l.val = v
    #:: ExpectedOutput(assert.failed:assertion.false)
    Fold(accVal(l))

def setValMethod2(l: ListClass, v: int) -> None:
    Requires(accVal(l))
    Requires(Low(v))
    Ensures(accVal(l))
    Ensures(getVal(l) == v)
    Unfold(accVal(l))
    l.val = v
    Fold(accVal(l))

@Predicate
def MyList(l: Optional[ListClass]) -> bool:
    return Implies(l is not None, Acc(l.val) and Acc(l.next) and MyList(l.next))

@Pure
def size(l: Optional[ListClass]) -> int:
    Requires(MyList(l))
    Ensures(Result() >= 0)
    return 0 if l is None else Unfolding(MyList(l), 1 + size(l.next))

def m1() -> ListClass:
    Ensures(MyList(Result()))
    Ensures(size(Result()) == 2)
    new_list = ListClass(0)
    Assert(size(new_list) == 1)
    next_list = ListClass(1)
    Unfold(MyList(new_list))
    new_list.next = next_list
    Fold(MyList(new_list))
    return new_list
