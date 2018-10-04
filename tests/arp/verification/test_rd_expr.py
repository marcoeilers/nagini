from nagini_contracts.contracts import *


class State:

    def __init__(self) -> None:
        # represents a mapping from variables to values
        # int used to just model permissions to it
        self.mapping = 0  # type: int


class Expr:

    def __init__(self) -> None:
        self.left = Expr()  # type: Expr
        self.right = Expr()  # type: Expr
        Ensures(Acc(self.left))
        Ensures(Acc(self.right))

    @Predicate
    def valid(self) -> bool:
        return Rd(self.left) and Rd(self.right) and \
               Implies(self.left is not None, self.left.valid()) and \
               Implies(self.right is not None, self.right.valid())

    def eval(self, state: State) -> int:
        Requires(self.valid())
        Requires(Rd(state.mapping))
        Ensures(self.valid())
        Ensures(Rd(state.mapping))
        Unfold(self.valid())
        result = 0  # type: int
        if self.left is not None:
            result += self.left.eval(state)
        if self.right is not None:
            result += self.right.eval(state)
        Fold(self.valid())
        return result

