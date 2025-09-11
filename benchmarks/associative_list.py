# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import cast, List, Set, Dict, Tuple, Optional

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
        res: Optional[object] = None
        i: int = 0
        while i < len(self.keys):
            # I need wildcard accesses here
            Invariant(Acc(self.keys) and Acc(self.values))
            Invariant(Acc(list_pred(self.keys)) and Acc(list_pred(self.values)))

            Invariant(0 <= i and i <= len(self.keys))
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

# @ContractOnly
# @Pure
# def indexof(l: List[object], item: object) -> int:
#     Requires(isinstance() issubtype(typeof(self), list(list_arg(typeof(self), 0)))
#     Requires(issubtype(typeof(item), list_arg(typeof(self), 0))
#     Requires(acc(state(self), wildcard)
#     Requires(unfolding acc(state(self), wildcard) in list___contains__(self, item)
#     ensures exists i: Int :: i >= 0 && i < list___len__(self) ==> object___eq___merged(item, list___getitem___index(self, __prim__int___box__(i))) && result == i


    # @Pure
    # def lookup(self, key: int) -> Optional[object]:
    #     Requires(Acc(self.state()))
    #     Ensures(Unfolding(self.state(), Implies(key in self.m, Result() is self.m[key][1])))
    #     Ensures(Unfolding(self.state(), Implies(not (key in self.m), Result() is None)))

    #     return Unfolding(
    #         self.state(),
    #         self.m[key][1] if key in self.m else None
    #     )


    # def __contains__(self, key: int) -> bool:
    #     for (k, v) in self.m:
    #         if k == key:

# ints_1: List[int] = [1,2,3,42]
# ints_2: List[int] = [1,2,3,42]
# Fold(state_pred(ints_1))
# Fold(state_pred(ints_2))
# one: E = E(ints_1)
# two: F = F(ints_2)
# assert one == two
# 
# Unfold(state_pred(one))
# Unfold(state_pred(two))
# 
# assert 42 in one.l
# assert 3 in two.l



# class E:
#     def __init__(self, l: List[int]) -> None:
#         Requires(state_pred(l))
#         Ensures(self.state())
#         # must be reference equality
#         Ensures(Unfolding(self.state(), self.l is l))
#         self.l: List[int] = l
#         Fold(self.state())
# 
#     @Pure
#     def __eq__(self, other: object) -> bool:
#         Requires(state_pred(self))
#         Requires(Implies(not Stateless(other), state_pred(other)))
#         Ensures(Implies(self is other, Result()))
#         Ensures(
#             Implies(
#                 type(self) == type(other), Unfolding(
#                     self.state(),
#                     Implies(
#                         not Stateless(other), Unfolding(
#                             state_pred(other),
#                             Result() == (self.l == cast(E, other).l)
#                         )
#                     )
#                 )
#             )
#         )
#         Ensures(
#             Implies(
#                 type(other) == F, Unfolding(
#                     self.state(),
#                     Implies(
#                         not Stateless(other), Unfolding(
#                             state_pred(other),
#                             Result() == (self.l == cast(F, other).l)
#                         )
#                     )
#                 )
#             )
#         )
#         if self is other:
#             return True
#         elif type(self) == type(other):
#             return Unfolding(
#                 self.state(),
#                 Unfolding(
#                     state_pred(other),
#                     self.l == cast(E, other).l
#                 )
#             )
#         elif type(other) == F:
#             return Unfolding(
#                 self.state(),
#                 Unfolding(
#                     state_pred(other),
#                     self.l == cast(F, other).l
#                 )
#             )
#         return False
# 
#     @Predicate
#     def state(self) -> bool:
#         return Acc(self.l) and Acc(state_pred(self.l))
# 
# class F:
#     def __init__(self, l: List[int]) -> None:
#         Requires(state_pred(l))
#         Ensures(self.state())
#         # must be reference equality
#         Ensures(Unfolding(self.state(), self.l is l))
#         self.l: List[int] = l
#         Fold(self.state())
# 
#     @Pure
#     def __eq__(self, other: object) -> bool:
#         Requires(state_pred(self))
#         Requires(Implies(not Stateless(other), state_pred(other)))
#         Ensures(Implies(self is other, Result()))
#         Ensures(
#             Implies(
#                 type(self) == type(other), Unfolding(
#                     self.state(),
#                     Implies(
#                         not Stateless(other), Unfolding(
#                             state_pred(other),
#                             Result() == (self.l == cast(F, other).l)
#                         )
#                     )
#                 )
#             )
#         )
#         Ensures(
#             Implies(
#                 type(other) == E, Unfolding(
#                     self.state(),
#                     Implies(
#                         not Stateless(other), Unfolding(
#                             state_pred(other),
#                             Result() == (self.l == cast(E, other).l)
#                         )
#                     )
#                 )
#             )
#         )
#         if self is other:
#             return True
#         elif type(self) == type(other):
#             return Unfolding(
#                 self.state(),
#                 Unfolding(
#                     state_pred(other),
#                     self.l == cast(F, other).l
#                 )
#             )
#         elif type(other) == E:
#             return Unfolding(
#                 self.state(),
#                 Unfolding(
#                     state_pred(other),
#                     self.l == cast(E, other).l
#                 )
#             )
#         return False
# 
#     @Predicate
#     def state(self) -> bool:
#         return Acc(self.l) and Acc(state_pred(self.l))


# class D1:
#     def __init__(self, l: List[int]) -> None:
#         Requires(state_pred(l))
#         Ensures(self.state())
#         # we need reference equality here
#         Ensures(Unfolding(self.state(), self.l == l))
#         self.l: List[int] = l
# 
#         # self.s: Set[A] = set()
#         # Fold(state_pred(self.l))
#         # Fold(state_pred(self.s))
#         Fold(self.state())
# 
#     @Pure
#     def __eq__(self, other: object) -> bool:
#         Requires(state_pred(self))
#         Requires(Implies(not Stateless(other), state_pred(other)))
#         Ensures(Implies(
#             self is other or type(other) == D1,
#             Result() ==
#             Unfolding(self.state(),
#                 Unfolding(state_pred(other),
#                     self.l == cast(D1, other).l # and self.s == cast(D1, other).s)
#                 )
#             )
#         ))
#         if self is other or type(other) == D1:
#             return Unfolding(self.state(),
#                 Unfolding(state_pred(other),
#                     self.l == cast(D1, other).l # and self.s == cast(D1, other).s
#             ))
#         return False
# 
#     @Predicate
#     def state(self) -> bool:
#         return Acc(self.l) and Acc(state_pred(self.l)) # and Acc(self.s) and Acc(state_pred(self.s))

# ints_1: List[int] = [1,2,3,42]
# ints_2: List[int] = [1,2,3,42]
# Fold(state_pred(ints_1))
# Fold(state_pred(ints_2))
# one: E = E(ints_1)
# two: F = F(ints_2)
# assert one == two
# 
# Unfold(state_pred(one))
# Unfold(state_pred(two))
# 
# assert 42 in one.l
# assert 3 in two.l



# def foo(one: D1, two: D1):
#     Requires(one.state())
#     Requires(two.state())
#     Ensures(one.state())
#     Ensures(two.state())
# 
#     Unfold(one.state())
#     Unfold(two.state())
# 
#     assert 
# 
#     Fold(one.state())
#     Fold(two.state())