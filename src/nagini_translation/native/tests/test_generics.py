"""
fixpoint PyClass PyClass_ObjectType(){
        return ObjectType;
}
fixpoint PyClass PyClass_module_0classA(){
        return PyClass("module_0classA", PyClass_ObjectType);
}
"""
from nagini_contracts.contracts import *
from typing import List, TypeVar, Generic

T = TypeVar('T')
V = TypeVar('V', bound=int)
W = TypeVar('W')



class Super(Generic[T, V]):
    def __init__(self, t: T, v: V) -> None:
        Ensures(Acc(self.t) and self.t is t)  # type: ignore
        Ensures(Acc(self.v) and self.v is v)  # type: ignore
        self.t = t
        self.v = v
class Someclass(Generic[T, V, W], Super[T, V]):
    def __init__(self, t: T, v: V, w: W) -> None:
        Ensures(Acc(self.t) and self.t is t)  # type: ignore
        Ensures(Acc(self.v) and self.v is v)  # type: ignore
        super().__init__(t, v)
        self.t = t
        self.v = v

@ContractOnly
@Native
def test_forallAcc1(l: List[Someclass[float, int, float]]) -> int:
    Requires(list_pred(l) and Forall(int,
                                     lambda i: Implies(i >= 0 and i < len(l), Acc(l[i].t))))
    Ensures(list_pred(l))
