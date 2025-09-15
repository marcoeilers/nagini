# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import cast, List, Set, Dict, Tuple, Optional


class Map:
    # list of key/value pairs
    def __init__(self, keys: List[int], values: List[object]) -> None:
        Requires(state_pred(keys))
        Requires(state_pred(values))
        Ensures(self.state())
        Ensures(Unfolding(self.state(), self.keys is keys and self.values is values))
        
        self.keys: List[int] = keys
        self.values: List[object] = values
        Fold(self.state())

    @Pure
    def __contains__(self, key: int) -> bool:
        Requires(Acc(self.state()))
        Ensures(Unfolding(self.state(), Implies(key in self.keys, Result())))
        Ensures(Unfolding(self.state(), Implies(not (key in self.keys), not Result())))
        return Unfolding(
            self.state(),
            key in self.keys
        )
    
    def lookup(self, key: int) -> Optional[object]:
        Requires(Acc(self.state()))
        Requires(Unfolding(self.state(), Unfolding(state_pred(self.keys), Unfolding(state_pred(self.values), len(self.keys) == len(self.values)))))
        Ensures(Acc(self.state()))
        Ensures(Unfolding(self.state(), Unfolding(state_pred(self.keys), Unfolding(state_pred(self.values), len(self.keys) == len(self.values)))))
        Ensures(Unfolding(self.state(), 
            Unfolding(state_pred(self.keys),
                Unfolding(state_pred(self.values),
                    Implies(
                        key in self.keys,
                        Exists(int, lambda i: (i >= 0 and i < len(self.keys)) and
                               self.keys[i] == key and
                               Result() is self.values[i]
                        )
                    )
                )
            )
        ))
        Ensures(Unfolding(self.state(), Implies(not (key in self.keys), Result() is None)))
        Unfold(self.state())
        Unfold(state_pred(self.keys))
        Unfold(state_pred(self.values))
        if self.keys == []:
            return None
        res: Optional[object] = None
        i: int = 0
        while i < len(self.keys):

            # need wildcard accesses here: how? cannot use Wildcard(...)
            Invariant(Acc(self.keys) and Acc(self.values))
            Invariant(Acc(list_pred(self.keys)) and Acc(list_pred(self.values)))

            Invariant(0 <= i and i < len(self.keys))
            Invariant(len(self.keys) == len(self.values))
            Invariant(res is None or Exists(
                int, lambda j: 0 <= j and j < len(self.keys) and self.keys[j] == key and res is self.values[j]
            ))
            if self.keys[i] == key:
                res = self.values[i]
                break
            i += 1
        Fold(state_pred(self.values))
        Fold(state_pred(self.keys))
        Fold(self.state())
        return res

    @Predicate
    def state(self) -> bool:
        return Acc(self.keys) and Acc(self.values) and Acc(state_pred(self.keys)) and Acc(state_pred(self.values))
















# class Node:
#     def __init__(self, k: int, v: object) -> None:
#         Requires(Acc(state_pred(v)))
#         Ensures(Acc(self.state()))
#         Unfold(state_pred(v))
#         self.data: Tuple[int, object] = (k, v)
#         self.next: Node = None
#         Fold(Acc(state_pred(self.data)))
#         Fold(Acc(self.state()))
# 
#     @Predicate
#     def state(self) -> bool:
#         return Acc(self.data) and Acc(state_pred(self.data))
# 
# @Predicate
# def lseg(start: Node, end: Node) -> bool:
#     return Implies(not (start is end), Acc(start.state()) and Acc(start.next) and Acc(lseg(start.next, end)))
# 
# class Map:
#     # list of key/value pairs
#     def __init__(self) -> None:
#         Ensures(self.state())
#         self.head: Node = None
#         Fold(lseg(self.head, None))
#         Fold(self.state())
# 
#     @Predicate
#     def state(self) -> bool:
#         return Acc(self.head) and Acc(lseg(self.head, None))
# 
#     @Pure
#     def lookup(self, key: int) -> Optional[object]:
#         Requires(Acc(self.state()))
#         # Ensures(Implies(key in self.m, Result() == self.m[key]))
#         # Ensures(Implies(not (key in self.m), Result() == None))
#         return None
# 
#         # Unfold(self.state())
#         # res: object = None
#         # for (k, v) in self.m:
#         #     if k == key:
#         #         res = v
#         #         break
#         # Fold(self.state())
#         # return res
