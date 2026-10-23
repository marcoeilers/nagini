from typing import List
from nagini_contracts.contracts import *


def reverse_in_place(xs: List[int]) -> None:
    Requires(Acc(list_pred(xs)))
    Ensures(Acc(list_pred(xs)))
    Ensures(len(xs) == Old(len(xs)))
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(xs), xs[i] == Old(ToSeq(xs))[len(xs) - 1 - i]), [[xs[i]]])))
    xs.reverse()


def reverse_pair(xs: List[int]) -> None:
    Requires(Acc(list_pred(xs)))
    Requires(len(xs) == 2)
    Ensures(Acc(list_pred(xs)))
    Ensures(len(xs) == 2)
    Ensures(xs[0] == Old(xs[1]) and xs[1] == Old(xs[0]))
    xs.reverse()


def reverse_twice(xs: List[int]) -> None:
    Requires(Acc(list_pred(xs)))
    Ensures(Acc(list_pred(xs)))
    Ensures(ToSeq(xs) == Old(ToSeq(xs)))
    xs.reverse()
    xs.reverse()


def reverse_changes(xs: List[int]) -> None:
    Requires(Acc(list_pred(xs)))
    Requires(len(xs) == 2 and xs[0] != xs[1])
    Ensures(Acc(list_pred(xs)))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(ToSeq(xs) == Old(ToSeq(xs)))
    xs.reverse()
