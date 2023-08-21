# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Optional

class ListClass():
    def __init__(self, v: int) -> None:
        self.val = v
        self.next = None #type: Optional[ListClass]
        Fold(MyList(self.next))
        Fold(MyList(self))
        Ensures(MyList(self))
        Ensures(size(self) == 1)
        Ensures(Unfolding(MyList(self), self.val == v))

@Predicate
def accVal(l: ListClass) -> bool:
    return Acc(l.val) and LowVal(l.val)

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
    #:: ExpectedOutput(fold.failed:sif.fold)
    Fold(accVal(l))

def setValMethod2(l: ListClass, v: int) -> None:
    Requires(accVal(l))
    Requires(Low(v))
    Ensures(accVal(l))
    Ensures(getVal(l) == v)
    Unfold(accVal(l))
    l.val = v
    Fold(accVal(l))

def unfold_fail(secret: bool) -> None:
    if secret:
        l = ListClass(0)
        Unfold(MyList(l))
        Fold(accVal(l))
    else:
        l = ListClass(1)
        Unfold(MyList(l))
        Fold(accVal(l))
    #:: ExpectedOutput(unfold.failed:sif.unfold)
    Unfold(accVal(l))

@Predicate
def MyList(l: Optional[ListClass]) -> bool:
    return Implies(l is not None, Acc(l.val) and Acc(l.next) and MyList(l.next))

@Predicate
def MyListLow(l: Optional[ListClass]) -> bool:
    return Implies(l is not None, Acc(l.val) and Acc(l.next) and Low(l.val) and Low(l.next) and
                   MyListLow(l.next))

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

def getHead(l: Optional[ListClass]) -> Optional[int]:
    Requires(Implies(l is not None, MyList(l)))
    Ensures(Implies(l is not None, MyList(l)))
    if l is None:
        return None
    Unfold(MyList(l))
    res = l.val
    Fold(MyList(l))
    return res

def contains(l: Optional[ListClass], key: int, perm: int) -> bool:
    Requires(perm > 0)
    Requires(Implies(l is not None, Acc(MyListLow(l), 1/perm)))
    Ensures(Implies(l is not None, Acc(MyListLow(l), 1/perm)))
    if l is None:
        return False
    Unfold(Acc(MyListLow(l), 1/perm))
    if l.val == key:
        res = True
    else:
        Assert(Acc(MyListLow(l.next), 1/perm))
        res = contains(l.next, key, perm * 2)
    Fold(Acc(MyListLow(l), 1/perm))
    return res
