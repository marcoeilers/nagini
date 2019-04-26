# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List, Optional


class A:
    pass


#:: ExpectedOutput(postcondition.violated:assertion.false)
def m(b: bool) -> A:
    if b:
        return A()


def m2(b: bool) -> Optional[A]:
    if b:
        return A()


#:: ExpectedOutput(postcondition.violated:assertion.false)
def m3(l: List[bool]) -> A:
    Requires(Acc(list_pred(l)))
    for b in l:
        if b:
            return A()


def m4(l: List[bool]) -> Optional[A]:
    Requires(Acc(list_pred(l)))
    for b in l:
        if b:
            return A()


#:: ExpectedOutput(postcondition.violated:assertion.false)
def m5(b: bool) -> A:
    pass


def m6(b: bool) -> Optional[A]:
    pass