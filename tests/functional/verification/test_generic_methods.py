from nagini_contracts.contracts import *
from typing import TypeVar, List, Tuple

T = TypeVar('T')
V = TypeVar('V', bound=int)


class Container:
    def __init__(self) -> None:
        pass


def m(v: V, lt: List[T]) -> Tuple[T, V, int]:
    Requires(Acc(list_pred(lt)) and len(lt) > 0)
    return lt[0], v, 2 + v


def client() -> None:
    cont = Container()
    t = m(True, [cont])
    assert isinstance(t[0], Container)
    assert isinstance(t[1], bool)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False