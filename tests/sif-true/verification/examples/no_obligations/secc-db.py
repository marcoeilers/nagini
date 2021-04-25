# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List, Tuple


class Elem:
    def __init__(self, key: int, value: int) -> None:
        self.key = key
        self.value = value


SUCCESS = 0
FAILURE = 1


def lookup(elems: List[Elem], key: int) -> Tuple[int, int]:
    Requires(Acc(list_pred(elems)))
    Requires(Low(len(elems)) and Low(key))
    Requires(Forall(int, lambda i: (Implies(i >= 0 and i < len(elems), Acc(elems[i].key) and Acc(elems[i].value) and Low(elems[i].key) and Implies(elems[i].key is key, Low(elems[i].value))), [[elems[i]]])))
    Ensures(Acc(list_pred(elems)))
    Ensures(Forall(int, lambda i: (Implies(i >= 0 and i < len(elems), Acc(elems[i].key) and Acc(elems[i].value) and Low(elems[i].key) and Implies(elems[i].key is key, Low(elems[i].value))), [[elems[i]]])))
    Ensures(Implies(Result()[0] == SUCCESS, Low(Result()[1])))
    Ensures(Implies(Result()[0] == FAILURE, Result()[1] == -1))
    Ensures(Result()[0] == SUCCESS or Result()[0] == FAILURE)

    i = 0
    while i < len(elems):
        Invariant(Acc(list_pred(elems)) and Low(len(elems)))
        Invariant(Low(i) and LowExit())
        Invariant(i >= 0 and i <= len(elems))
        Invariant(Forall(int, lambda j: (Implies(j >= 0 and j < len(elems), Acc(elems[j].key) and Acc(elems[j].value) and Low(elems[j].key) and Implies(elems[j].key is key, Low(elems[j].value))), [[elems[j]]])))

        if elems[i].key is key:
            return (SUCCESS, elems[i].value)
        i += 1
    return (FAILURE, -1)


def binsearch(elems: List[Elem], from_: int, l: int, key: int) -> Tuple[int, int]:
    Requires(Acc(list_pred(elems)))
    Requires(Low(l) and Low(key) and Low(from_))
    Requires(0 <= from_ and from_ + l <= len(elems))
    Requires(Forall(int, lambda i: (Implies(i >= 0 and i < len(elems), Acc(elems[i].key) and Acc(elems[i].value) and Low(elems[i].key) and Implies(elems[i].key is key, Low(elems[i].value))), [[elems[i]]])))
    Ensures(Acc(list_pred(elems)))
    Ensures(Forall(int, lambda i: (Implies(i >= 0 and i < len(elems), Acc(elems[i].key) and Acc(elems[i].value) and Low(elems[i].key) and Implies(elems[i].key is key, Low(elems[i].value))), [[elems[i]]])))
    Ensures(Implies(Result()[0] == SUCCESS, Low(Result()[1])))
    Ensures(Implies(Result()[0] == FAILURE, Result()[1] == -1))
    Ensures(Result()[0] == SUCCESS or Result()[0] == FAILURE)

    if l <= 0:
        return FAILURE, -1

    mid = l // 2

    e = elems[from_ + mid]
    k = e.key
    if k is key:
        return SUCCESS, elems[from_ + mid].value
    else:
        if l == 1:
            return FAILURE, -1
        if k > key:
            return binsearch(elems, from_, mid - 1, key)
        else:
            return binsearch(elems, from_ + mid + 1, l - (mid + 1), key)


def sum_all(elems: List[Elem], key: int) -> int:
    Requires(Acc(list_pred(elems)))
    Requires(Low(len(elems)) and Low(key))
    Requires(Forall(int, lambda i: (Implies(i >= 0 and i < len(elems), Acc(elems[i].key) and Acc(elems[i].value) and Low(elems[i].key) and Implies(elems[i].key is key, Low(elems[i].value))), [[elems[i]]])))
    Ensures(Acc(list_pred(elems)))
    Ensures(Forall(int, lambda i: (Implies(i >= 0 and i < len(elems), Acc(elems[i].key) and Acc(elems[i].value) and Low(elems[i].key) and Implies(elems[i].key is key, Low(elems[i].value))), [[elems[i]]])))
    Ensures(Low(Result()))

    sum = 0
    i = 0
    while i < len(elems):
        Invariant(Acc(list_pred(elems)) and Low(len(elems)))
        Invariant(i >= 0 and i <= len(elems))
        Invariant(Low(sum) and Low(i))
        Invariant(Forall(int, lambda j: (Implies(j >= 0 and j < len(elems), Acc(elems[j].key) and Acc(elems[j].value) and Low(elems[j].key) and Implies(elems[j].key is key, Low(elems[j].value))), [[elems[j]]])))

        if elems[i].key is key:
            sum += elems[i].value
        i += 1
    return sum


def sum_all_rec(elems: List[Elem], from_: int, l: int, key: int, init: int) -> int:
    Requires(Acc(list_pred(elems)))
    Requires(Low(l) and Low(key) and Low(from_) and Low(init))
    Requires(0 <= from_ and from_ + l <= len(elems))
    Requires(Forall(int, lambda i: Implies(i >= 0 and i < len(elems), Acc(elems[i].key) and Acc(elems[i].value) and Low(elems[i].key) and Implies(elems[i].key is key, Low(elems[i].value)))))
    Ensures(Acc(list_pred(elems)))
    Ensures(Forall(int, lambda i: Implies(i >= 0 and i < len(elems), Acc(elems[i].key) and Acc(elems[i].value) and Low(elems[i].key) and Implies(elems[i].key is key, Low(elems[i].value)))))
    Ensures(Low(Result()))

    if l > 0:
        e = elems[from_]
        if e.key is key:
            return sum_all_rec(elems, from_ + 1, l - 1, key, init + e.value)
        else:
            return sum_all_rec(elems, from_ + 1, l - 1, key, init)
    else:
        return init


def remove_all(elems: List[Elem], key: int) -> None:
    Requires(Acc(list_pred(elems)))
    Requires(Low(len(elems)) and Low(key))
    Requires(Forall(int, lambda i: (Implies(i >= 0 and i < len(elems), Acc(elems[i].key) and Acc(elems[i].value) and Low(elems[i].key) and Implies(elems[i].key is key, Low(elems[i].value))), [[elems[i]]])))
    Ensures(Acc(list_pred(elems)))
    Ensures(Forall(int, lambda i: (Implies(i >= 0 and i < len(elems), Acc(elems[i].key) and Acc(elems[i].value) and Low(elems[i].key) and Implies(elems[i].key is key, Low(elems[i].value))), [[elems[i]]])))

    i = 0
    while i < len(elems):
        Invariant(Acc(list_pred(elems)) and Low(len(elems)))
        Invariant(i >= 0 and i <= len(elems))
        Invariant(Low(i))
        Invariant(Forall(int, lambda j: (Implies(j >= 0 and j < len(elems), Acc(elems[j].key) and Acc(elems[j].value) and Low(elems[j].key) and Implies(elems[j].key is key, Low(elems[j].value))), [[elems[j]]])))

        if elems[i].key is key:
            elems[i].value = 0
        i += 1
