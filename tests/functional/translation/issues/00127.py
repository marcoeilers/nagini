# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Dict, List, Union

def test_dict_read(a: Dict[int, int]) -> int:
    Requires(dict_pred(a))
    Requires(0 in a)
    return a[0]

def test_list_read(a: List[int]) -> int:
    Requires(list_pred(a))
    Requires(len(a) > 0)
    return a[0]

def test_implicit_function_call_1(a: Union[List[int], Dict[int, int]]) -> int:
    Requires(Implies(isinstance(a, list), list_pred(a) and len(a) > 0))
    Requires(Implies(isinstance(a, dict), dict_pred(a) and 0 in a))
    return a[0]

def test_dict_write(a: Dict[int, int]) -> None:
    Requires(dict_pred(a))
    a[0] = 5

def test_list_write(a: List[int]) -> None:
    Requires(list_pred(a))
    Requires(len(a) > 0)
    a[0] = 5

def test_implicit_method_call_1(a: Union[List[int], Dict[int, int]]) -> None:
    Requires(Implies(isinstance(a, list), list_pred(a) and len(a) > 0))
    Requires(Implies(isinstance(a, dict), dict_pred(a)))
    a[0] = 5
