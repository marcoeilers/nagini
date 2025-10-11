# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List, Optional


class Map:
    def __init__(self, keys: List[object], values: List[object]) -> None:
        Requires(Acc(state_pred(keys)))
        Requires(Acc(state_pred(values)))
        Requires(
            Unfolding(state_pred(keys), Unfolding(state_pred(values),
            len(keys) == len(values)
        )))
        Ensures(self.state())
        Ensures(Unfolding(
            self.state(), self.keys is keys and self.values is values
        ))
        #     Unfolding(state_pred(self.keys), Unfolding(state_pred(self.values),
        #         len(self.keys) == len(self.values)
        #     ))
        # ))

        Unfold(state_pred(keys))
        Unfold(state_pred(values))
        self.keys: List[object] = keys
        self.values: List[object] = values
        Fold(state_pred(self.keys))
        Fold(state_pred(self.values))
        Fold(self.state())

    @Pure
    def __contains__(self, key: object) -> bool:
        Requires(Acc(self.state()))
        Requires(Implies(not Stateless(key), Acc(state_pred(key))))
        Ensures(Unfolding(self.state(), Implies(key in self.keys, Result())))
        Ensures(Unfolding(self.state(), Implies(not (key in self.keys), not Result())))
        return Unfolding(self.state(),
            key in self.keys
        )
    
    def lookup(self, key: object) -> Optional[object]:
        Requires(Acc(self.state()))
        Requires(Implies(not Stateless(key), Acc(state_pred(key))))
        Requires(Unfolding(self.state(), Unfolding(state_pred(self.keys), Unfolding(state_pred(self.values), 
            len(self.keys) == len(self.values)
        ))))

        Ensures(Acc(self.state()))
        Ensures(Implies(not Stateless(key), Acc(state_pred(key))))
        Ensures(Unfolding(self.state(), Unfolding(state_pred(self.keys), Unfolding(state_pred(self.values),
            Implies(
                not (Result() is None),
                Exists(int, lambda j: 0 <= j and j < len(self.keys) and j < len(self.values) and self.keys[j] == key and Result() is self.values[j])
            )
        ))))

        res: Optional[object] = None
        i: int = 0
        found_idx: int = -1
        Unfold(self.state())
        Unfold(state_pred(self.keys))
        Unfold(state_pred(self.values))

        while (i < len(self.keys) and found_idx == -1):
            # Permissions
            Invariant(Acc(self.keys, 1/2) and Acc(self.values, 1/2))
            Invariant(list_pred(self.keys))
            Invariant(list_pred(self.values))
            Invariant(Implies(not Stateless(key), Acc(state_pred(key))))
            Invariant(Forall(self.keys, lambda i: Implies(not Stateless(i), Acc(state_pred(i)))))
            Invariant(Forall(self.values, lambda i: Implies(not Stateless(i), Acc(state_pred(i)))))

            # Witness
            Invariant(
              (res is None and found_idx == -1) or (res is not None and found_idx != -1)
            )
            Invariant(found_idx == -1 or 0 <= found_idx and found_idx < i)
            Invariant(len(self.keys) == len(self.values) and 0 <= i and i <= len(self.keys))
            Invariant(
                Implies(
                    not (res is None),
                    self.keys[found_idx] == key and res is self.values[found_idx]
                )
            )

            if key == self.keys[i]:
                res = self.values[i]
                if not (res is None):
                    found_idx = i
                    i += 1
                    break
            i += 1

        Fold(state_pred(self.values))
        Fold(state_pred(self.keys))
        Fold(self.state())
        return res

    @Predicate
    def state(self) -> bool:
        return Acc(self.keys) and Acc(self.values) and Acc(state_pred(self.keys)) and Acc(state_pred(self.values)) 

        # Timeout because of:
        # and (
        #     Unfolding(state_pred(self.keys), Unfolding(state_pred(self.values), len(self.keys) == len(self.values)))
        # )




        # Ensures(Unfolding(self.state(), 
        #     Implies(
        #         key in self.keys,
        #         Unfolding(state_pred(self.keys),
        #             Unfolding(state_pred(self.values),
        #                 Exists(int, lambda j: (j >= 0 and j < len(self.keys)) and
        #                     self.keys[j] == key and Result() is self.values[j]
        #                 )
        #             )
        #         )
        #     )
        # ))
        # Ensures(Unfolding(self.state(), Implies(not (key in self.keys), Result() is None)))

        


            # Invariant(
            #     Implies(
            #         res is None,
            #         Forall(int, lambda j: Implies(0 <= j and j <= len(self.keys), self.keys[j] != key))
            #     ) 
            #     and
            #     Implies(
            #         Forall(int, lambda j: Implies(0 <= j and j <= len(self.keys), self.keys[j] != key)),
            #         res is None
            #     )
            # )


            # Invariant(
            #     Implies(
            #         key in self.keys,
            #         Exists(int, lambda j: 0 <= j and j < len(self.keys) and self.keys[j] == key and res is self.values[j])
            #     )
            # )
            # Invariant(
            #     res is None or
            #     Exists(int, lambda j: 0 <= j and j < len(self.keys) and self.keys[j] == key and res is self.values[j])
            # )









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
