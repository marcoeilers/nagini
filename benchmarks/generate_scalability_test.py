# for cls in "HIJKLMNOPQRSTUVWXYZ":
#     print(f"""class {cls}:
#     def __init__(self, i: int) -> None:
#         self.i: int = i
#         Fold(self.state())
#         Ensures(self.state())
# 
#     @Pure
#     def __eq__(self, other: object) -> bool:
#         Requires(state_pred(self))
#         Requires(Implies(not Stateless(other), state_pred(other)))
#         Ensures(Implies(self is other, Result()))
#         Ensures(
#             Implies(
#                 isinstance(other, {cls}), Unfolding(
#                     self.state(),
#                     Implies(
#                         not Stateless(other), Unfolding(
#                             state_pred(other),
#                             Result() == (self.i == cast({cls}, other).i)
#                         )
#                     )
#                 )
#             )
#         )
#         if self is other:
#             return True
#         elif isinstance(other, {cls}):
#             return Unfolding(
#                 self.state(),
#                 Unfolding(
#                     state_pred(other),
#                     self.i == cast({cls}, other).i
#                 )
#             )
#         return False
# 
#     @Predicate
#     def state(self) -> bool:
#         return Wildcard(self.i)\n""")
# 

for cls in "HIJKLMNOPQRSTUVWXYZ":
    print(f"""def foo{cls}(o1: object, o2: object) -> int:
    Requires(isinstance(o1, {cls}))
    Requires(isinstance(o2, {cls}))
    Requires(state_pred(o1))
    Requires(state_pred(o2))
    Requires(
        Unfolding(state_pred(o1),
            Unfolding(state_pred(o2),
                cast({cls}, o1).i == cast({cls}, o2).i
            )
        )
    )
    Ensures(state_pred(o1))
    Ensures(state_pred(o2))
    assert o1 == o2
    return 0\n""")
