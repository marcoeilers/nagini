# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import cast, List


class String:
    pass


class StringLit(String):
    def __init__(self, s: str):
        Ensures(self.state())
        Ensures(Unfolding(self.state(), self.s is s))
        self.s: str = s
        Fold(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(Acc(self.state()))
        Requires(Implies(not Stateless(other), Acc(state_pred(other))))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                isinstance(other, StringLit),
                Unfolding(self.state(), Unfolding(state_pred(other),
                    Result() == (self.s == cast(StringLit, other).s)
                ))
            )
        )
        Ensures(
            Implies(
                isinstance(other, ListString),
                Unfolding(self.state(), Unfolding(state_pred(other),
                    Result() == (self.s == "".join(cast(ListString, other).ls))
                ))
            )
        )
        if isinstance(other, StringLit):
            return Unfolding(self.state(), Unfolding(state_pred(other),
                self.s == cast(StringLit, other).s
            ))
        elif isinstance(other, ListString):
            return Unfolding(self.state(), Unfolding(state_pred(other),
                self.s == "".join(cast(ListString, other).ls)
            ))
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.s)


class ListString(String):
    def __init__(self, ls: List[str]):
        Requires(Acc(state_pred(ls)))
        Ensures(self.state())
        Ensures(Unfolding(self.state(), self.ls is ls))

        Unfold(state_pred(ls))
        self.ls: List[str] = ls
        Fold(state_pred(self.ls))
        Fold(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(Acc(self.state()))
        Requires(Implies(not Stateless(other), Acc(state_pred(other))))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                isinstance(other, ListString),
                Unfolding(self.state(), Unfolding(state_pred(other),
                    Result() == ("".join(self.ls) == "".join(cast(ListString, other).ls))
                ))
            )
        )
        Ensures(
            Implies(
                isinstance(other, StringLit),
                Unfolding(self.state(), Unfolding(state_pred(other),
                    Result() == ("".join(self.ls) == cast(StringLit, other).s)
                ))
            )
        )
        if isinstance(other, StringLit):
            return Unfolding(self.state(), Unfolding(state_pred(other),
                "".join(self.ls) == cast(StringLit, other).s
            ))
        elif isinstance(other, ListString):
            return Unfolding(self.state(), Unfolding(state_pred(other),
                "".join(self.ls) == "".join(cast(ListString, other).ls)
            ))
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.ls) and Acc(state_pred(self.ls))


if __name__ == '__main__':
    t: List[str] = ['T', 'e', 's', 't']
    Fold(state_pred(t))
    ls: ListString = ListString(t)
    s: StringLit = StringLit("".join(t))
    assert ls == s
