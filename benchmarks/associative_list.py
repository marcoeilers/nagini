# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List, Optional


class Map:
    def __init__(self, keys: List[object], values: List[object]) -> None:
        Requires(Acc(self.keys))
        Requires(Acc(self.values))
        Requires(list_pred(keys) and list_pred(values))
        Requires(len(keys) == len(values))
        Ensures(Acc(self.keys))
        Ensures(Acc(self.values))
        Ensures(self.keys is keys and self.values is values)
        Ensures(list_pred(keys) and list_pred(values))
        Ensures(len(keys) == len(values))
        Ensures(len(self.keys) == len(self.values))
        Ensures(self.state())
        
        self.keys: List[object] = keys
        self.values: List[object] = values
        Fold(state_pred(keys))
        Fold(state_pred(values))
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

            Invariant(
              (res is None and found_idx == -1) or (res is not None and found_idx != -1)
            )
            Invariant(
                len(self.keys) == len(self.values) and 0 <= i and i <= len(self.keys) and (found_idx == -1 or 0 <= found_idx and found_idx < i)
            )
            Invariant(
                Implies(
                    (res is not None) and (found_idx != -1),
                    0 <= found_idx and found_idx < len(self.keys) and found_idx < len(self.values) and 
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