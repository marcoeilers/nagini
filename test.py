from nagini_contracts.contracts import *
from typing import List, Tuple


class classA:
    def __init__(self, arg: int) -> None:
        self.attr = arg

@ContractOnly
@Native
def test_listpred(l: List[int]) -> int:
    """
    """
    Requires(list_pred(l))
    Ensures(list_pred(l))

@ContractOnly
@Native
def test_forallAcc1(l: List[classA]) -> int:
    """
    """
    Requires(list_pred(l) and Forall(int,
                                     lambda i: Implies(i >= 0 and i < len(l), Acc(l[i].attr))))
    Ensures(list_pred(l))

@ContractOnly
@Native
def test_forallAcc2(l: List[classA], j: int) -> int:
    """
    """
    Requires(list_pred(l) and Forall(int,
                                     lambda i: Implies(i >= 0 and i < len(l), Acc(l[i].attr, 1/2))) and (l[j].attr is j or l[j].attr != j))
    Ensures(list_pred(l))

@ContractOnly
#@Native
def test_forallAcc3(l: List[classA]) -> int:
    """
    """
    Requires(list_pred(l) and Forall(l, lambda el: Acc(el.attr)))
    Ensures(list_pred(l))

@ContractOnly
#@Native
def test_forallAcc4(l: List[classA], j: int) -> int:
    """
    """
    Requires(list_pred(l) and Forall(
        l, lambda el: Acc(el.attr)) and l[j].attr > 0)
    Ensures(list_pred(l))

@ContractOnly
#@Native
def test_forallAcc5(l: List[classA],) -> int:
    """
    """
    Requires(list_pred(l) and Forall(l, lambda el: Acc(el.attr)) and
             Forall(int, lambda i: Implies(i >= 0 and i < len(l), Acc(l[i].attr))))
    Ensures(list_pred(l))

#TODO: add tests calling length

#TODO: later, write tests Calling Implies as predfull and predless expression