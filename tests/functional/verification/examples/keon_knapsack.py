# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

#:: IgnoreFile(107)

from typing import List
from nagini_contracts.contracts import *


def print(o: object) -> None:
    pass


class Item(object):

    def __init__(self, value: int, weight: int) -> None:
        self.value = value
        self.weight = weight
        Ensures(Acc(self.value) and Acc(self.weight))
        Ensures(self.value == value and self.weight == weight)


def get_maximum_value(items: List[Item], capacity: int) -> int:
    Requires(list_pred(items) and capacity > 0)
    Requires(Forall(items, lambda i: Acc(i.weight) and Acc(i.value) and i.weight > 0))
    dp = [0] * (capacity + 1)
    for item in items:
        Invariant(Acc(list_pred(items), 1/4))
        Invariant(Forall(items, lambda i: Acc(i.weight) and Acc(i.value) and i.weight > 0))
        Invariant(Acc(list_pred(dp)) and len(dp) == capacity + 1)
        dp_tmp = [total_value for total_value in dp]
        for current_weight in range(0, capacity + 1):
            Invariant(list_pred(dp_tmp) and len(dp_tmp) == capacity + 1)
            Invariant(Acc(item.weight, 1/4) and Acc(item.value, 1/4) and item.weight > 0)
            Invariant(Acc(list_pred(dp), 1/2) and len(dp) == capacity + 1)
            total_weight = current_weight + item.weight
            if total_weight <= capacity:
                dp_tmp[total_weight] = max(dp_tmp[total_weight],
                                           dp[current_weight] + item.value)
        dp = dp_tmp
    return max(dp)

print(get_maximum_value([Item(60, 10), Item(100, 20), Item(120, 30)],
                        50))
print(get_maximum_value([Item(60, 5), Item(50, 3), Item(70, 4), Item(30, 2)],
                        5))