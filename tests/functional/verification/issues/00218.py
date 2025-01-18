# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import  List

def test(numbers:List[int])->List[int]:
    Requires(list_pred(numbers))
    Requires(len(numbers)>0)
    Ensures(list_pred(Result()))
    Ensures(list_pred(numbers))
    Ensures(len(Result())==len(numbers))
    numbers_sorted=sorted(numbers)
    return numbers_sorted