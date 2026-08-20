"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
from nagini_contracts.contracts import *


def match_true(x: bool) -> bool:
    Ensures(Result() == x)
    match x:
        case True:
            return True
        case False:
            return False


def match_true_postcond(x: bool) -> bool:
    Ensures(Implies(x == False, Result() == True))
    match x:
        case False:
            return True
        case _:
            return False


def match_true_wrong_postcond(x: bool) -> bool:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Implies(x == True, Result() == False))
    match x:
        case True:
            return True
        case _:
            return False


# bool is a subtype of int, so `x: int` could hold True (and True == 1).
# The isinstance guard is required to tell the verifier x is a plain int.
def int_one_does_not_match_true(x: int) -> int:
    Requires(not isinstance(x, bool))
    Requires(x == 1)
    Ensures(Result() == 0)
    match x:
        case True:
            return 1
        case _:
            return 0


def true_matches_true(x: bool) -> int:
    Requires(x == True)
    Ensures(Result() == 1)
    match x:
        case True:
            return 1
        case _:
            return 0


def match_value(x: int) -> int:
    Ensures(Result() == 0 or Result() == 1)
    match x:
        case 0:
            return 0
        case _:
            return 1


def match_value_postcond(x: int) -> int:
    Ensures(Result() == 0 or Result() == 1)
    Ensures(Implies(x == 0, Result() == 0))
    match x:
        case 0:
            return 0
        case _:
            return 1


def match_none(x: object) -> bool:
    Ensures(Result() == (x is None))
    match x:
        case None:
            return True
        case _:
            return False


def match_wildcard(x: int) -> int:
    Ensures(Result() == x)
    match x:
        case _:
            return x


def match_capture(x: int) -> int:
    Ensures(Result() == x)
    match x:
        case y:
            return y


def match_class_int(x: object) -> bool:
    Ensures(Result() == isinstance(x, int))
    match x:
        case int():
            return True
        case _:
            return False


def match_or(x: int) -> int:
    Ensures(Result() == 0 or Result() == x)
    Ensures(Implies(x == 0 or x == 1, Result() == 0))
    match x:
        case 0 | 1:
            return 0
        case _:
            return x


def match_guard(x: int) -> int:
    Ensures(Result() >= 0)
    match x:
        case y if y > 0:
            return y
        case _:
            return 0


def match_as(x: int) -> int:
    Ensures(Result() == x)
    match x:
        case int() as y:
            return y


def match_multi_case(x: int) -> int:
    Ensures(Result() >= 0)
    Ensures(Result() <= 2)
    match x:
        case 0:
            return 0
        case 1:
            return 1
        case _:
            return 2


# --- Soundness: wrong postconditions must be rejected ---

def match_value_wrong_postcond(x: int) -> int:
    Ensures(Result() == 0 or Result() == 1)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Implies(x == 0, Result() == 1))
    match x:
        case 0:
            return 0
        case _:
            return 1


def match_none_wrong_postcond(x: object) -> bool:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == True)
    match x:
        case None:
            return True
        case _:
            return False


def match_guard_wrong_postcond(x: int) -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() > 0)
    match x:
        case y if y > 0:
            return y
        case _:
            return 0


def match_or_wrong_postcond(x: int) -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Implies(x == 1, Result() == 1))
    match x:
        case 0 | 1:
            return 0
        case _:
            return x


# --- Soundness: wrong postcondition for class pattern ---

def match_class_wrong_postcond(x: object) -> bool:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == False)
    match x:
        case int():
            return True
        case _:
            return False


# --- Soundness: pattern conditions known inside case bodies ---

def match_value_cond_in_branch(x: int) -> None:
    match x:
        case 0:
            assert x == 0
        case _:
            pass


def match_value_cond_wrong_in_branch(x: int) -> None:
    match x:
        case 0:
            #:: ExpectedOutput(assert.failed:assertion.false)
            assert x == 1
        case _:
            pass


def match_capture_value_in_branch(x: int) -> None:
    match x:
        case y:
            assert y == x


def match_capture_value_wrong_in_branch(x: int) -> None:
    match x:
        case y:
            #:: ExpectedOutput(assert.failed:assertion.false)
            assert y != x


def match_class_cond_in_branch(x: object) -> None:
    match x:
        case int():
            assert isinstance(x, int)
        case _:
            pass


def match_class_cond_wrong_in_branch(x: object) -> None:
    match x:
        case int():
            #:: ExpectedOutput(assert.failed:assertion.false)
            assert not isinstance(x, int)
        case _:
            pass


def match_class_else_cond_in_branch(x: object) -> None:
    match x:
        case int():
            pass
        case _:
            assert not isinstance(x, int)


def match_class_else_cond_wrong_in_branch(x: object) -> None:
    match x:
        case int():
            pass
        case _:
            #:: ExpectedOutput(assert.failed:assertion.false)
            assert isinstance(x, int)


def match_none_cond_in_branch(x: object) -> None:
    match x:
        case None:
            assert x is None
        case _:
            pass


def match_guard_cond_in_branch(x: int) -> None:
    match x:
        case y if y > 0:
            assert y > 0
        case _:
            pass


# --- Definedness: variables defined only in some cases ---
#:: ExpectedOutput(carbon)(postcondition.violated:assertion.false)
def match_capture_undefined_after(x: int) -> int:
    match x:
        case 0:
            pass
        case y:
            pass
    #:: ExpectedOutput(expression.undefined:undefined.local.variable)
    return y


def match_capture_defined_in_all(x: int) -> int:
    Ensures(Result() >= 0)
    match x:
        case 0:
            y = 0
        case _:
            y = 1
    return y


# When a precondition makes one case unreachable, the verifier can prove that
# a variable bound only in the other case is always defined after the match.
def match_capture_guaranteed(x: int) -> int:
    Requires(x != 0)
    Ensures(Result() == x)
    match x:
        case 0:
            pass
        case y:
            pass
    return y


def match_madness() -> None:
    to_match = 1
    res = 0
    match to_match:
        case True:
            assert False
        case _:
            res = 7
    assert res == 7

def match_madness_2() -> None:
    to_match = True
    res = 0
    match to_match:
        case 1:
            res = 7
        case _:
            assert False
    assert res == 7

class Point:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y
        Ensures(Acc(self.x) and Acc(self.y) and self.x is x and self.y is y)

def match_madness_3() -> None:
    p = Point(3,4)
    res = 0
    match 4:
        case p.x:
            assert False
        case p.y:
            res = 7
        case _:
            assert False
    assert res == 7