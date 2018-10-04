from nagini_contracts.contracts import *


class Node:
    def __init__(self) -> None:
        self.val = 0

@Predicate
def P(x: Node) -> bool:
    return True


def m(n: Node) -> None:
    #:: ExpectedOutput(invalid.program:invalid.contract.position)
    Requires(Unfolding(P(n), Acc(n.val)))