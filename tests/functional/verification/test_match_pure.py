"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
from nagini_contracts.contracts import *


@Pure
def pure_match_true(x: bool) -> bool:
    Ensures(Result() == x)
    match x:
        case True:
            return True
        case False:
            return False


@Pure
def pure_match_true_postcond(x: bool) -> bool:
    Ensures(Implies(x == False, Result() == True))
    match x:
        case False:
            return True
        case _:
            return False


@Pure
def pure_match_true_wrong_postcond(x: bool) -> bool:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Implies(x == True, Result() == False))
    match x:
        case True:
            return True
        case _:
            return False


@Pure
def pure_int_one_does_not_match_true(x: int) -> int:
    Requires(not isinstance(x, bool))
    Requires(x == 1)
    Ensures(Result() == 0)
    match x:
        case True:
            return 1
        case _:
            return 0


@Pure
def pure_true_matches_true(x: bool) -> int:
    Requires(x == True)
    Ensures(Result() == 1)
    match x:
        case True:
            return 1
        case _:
            return 0


@Pure
def pure_match_value(x: int) -> int:
    Ensures(Result() == 0 or Result() == 1)
    match x:
        case 0:
            return 0
        case _:
            return 1


@Pure
def pure_match_value_postcond(x: int) -> int:
    Ensures(Result() == 0 or Result() == 1)
    Ensures(Implies(x == 0, Result() == 0))
    match x:
        case 0:
            return 0
        case _:
            return 1


@Pure
def pure_match_none(x: object) -> bool:
    Ensures(Result() == (x is None))
    match x:
        case None:
            return True
        case _:
            return False


@Pure
def pure_match_wildcard(x: int) -> int:
    Ensures(Result() == x)
    match x:
        case _:
            return x


@Pure
def pure_match_capture(x: int) -> int:
    Ensures(Result() == x)
    match x:
        case y:
            return y


@Pure
def pure_match_class_int(x: object) -> bool:
    Ensures(Result() == isinstance(x, int))
    match x:
        case int():
            return True
        case _:
            return False


@Pure
def pure_match_or(x: int) -> int:
    Ensures(Result() == 0 or Result() == x)
    Ensures(Implies(x == 0 or x == 1, Result() == 0))
    match x:
        case 0 | 1:
            return 0
        case _:
            return x


@Pure
def pure_match_guard(x: int) -> int:
    Ensures(Result() >= 0)
    match x:
        case y if y > 0:
            return y
        case _:
            return 0


@Pure
def pure_match_as(x: int) -> int:
    Ensures(Result() == x)
    match x:
        case int() as y:
            return y


@Pure
def pure_match_multi_case(x: int) -> int:
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

@Pure
def pure_match_value_wrong_postcond(x: int) -> int:
    Ensures(Result() == 0 or Result() == 1)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Implies(x == 0, Result() == 1))
    match x:
        case 0:
            return 0
        case _:
            return 1


@Pure
def pure_match_none_wrong_postcond(x: object) -> bool:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == True)
    match x:
        case None:
            return True
        case _:
            return False


@Pure
def pure_match_guard_wrong_postcond(x: int) -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() > 0)
    match x:
        case y if y > 0:
            return y
        case _:
            return 0


@Pure
def pure_match_or_wrong_postcond(x: int) -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Implies(x == 1, Result() == 1))
    match x:
        case 0 | 1:
            return 0
        case _:
            return x


@Pure
def pure_match_class_wrong_postcond(x: object) -> bool:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == False)
    match x:
        case int():
            return True
        case _:
            return False


# --- Assignments in case branches and after the match ---

@Pure
def pure_match_assign_in_branches(x: int) -> int:
    Ensures(Result() == 0 or Result() == 1)
    Ensures(Implies(x == 0, Result() == 0))
    match x:
        case 0:
            y = 0
        case _:
            y = 1
    return y


@Pure
def pure_match_assign_in_branches_wrong_postcond(x: int) -> int:
    Ensures(Result() == 0 or Result() == 1)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Implies(x == 0, Result() == 1))
    match x:
        case 0:
            y = 0
        case _:
            y = 1
    return y


@Pure
def pure_match_assign_with_capture(x: int) -> int:
    Ensures(Result() == x + 1)
    match x:
        case y:
            z = y + 1
    return z


@Pure
def pure_match_assign_then_use(x: int) -> int:
    Ensures(Implies(x == 0, Result() == 42))
    Ensures(Implies(x != 0, Result() == x))
    match x:
        case 0:
            y = 42
        case _:
            y = x
    z = y
    return z


# --- Definedness: variables only defined in some match cases ---

@Pure
def pure_match_capture_read_in_body(x: int) -> int:
    Ensures(Result() >= 0)
    match x:
        case y if y > 0:
            return y
        case _:
            return 0


@Pure
def pure_match_capture_undefined_after(x: int) -> int:
    match x:
        case 0:
            z = 0
        case y:
            z = 1
    #:: ExpectedOutput(expression.undefined:undefined.local.variable)
    return y


