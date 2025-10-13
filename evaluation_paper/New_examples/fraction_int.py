# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import cast, List, Tuple, Optional


# TODO: Int class: i: Optional[int] -> None ~= not defined

class Fraction:
    def __init__(self, a: int, b: int):
        Ensures(self.state())
        Ensures(Unfolding(self.state(),
            Implies(
                a != 0 and b > 0 and self._gcd(a, b) != 0, self.num is a // self._gcd(a, b) and self.denom is b // self._gcd(a, b)
            ) and
            Implies(
                a != 0 and b < 0 and self._gcd(a, b) != 0, self.num is a // (-self._gcd(a, b)) and self.denom is b // (-self._gcd(a, b))
            ) and
            Implies(
                a == 0 and b != 0, self.num == a and self.denom == 1
            ) and
            Implies(
                b == 0, self.num == 1 and self.denom == b
            )
        ))
        _a: int = a
        _b: int = b

        if a == 0 and b != 0:
            _b = 1
        elif b == 0:
            _a = 1
        else:
            # algorithm from fractions package
            g: int = self._gcd(a, b)
            if b < 0:
                g = -g
            _a = a // g
            _b = b // g
        self.num: int = _a
        self.denom: int = _b
        Fold(self.state())

    @Pure
    @ContractOnly
    def _gcd(self, a: int, b: int) -> int:
        Requires(a != 0 or b != 0)
        Ensures(Result() > 0)
        Ensures(
            a % Result() == 0 and
            b % Result() == 0
        )
        Ensures(
            Forall(int, lambda d:
                Implies(d > 0 and d <= abs(a) and d <= abs(b) and a % d == 0 and b % d == 0, d <= Result())
            )
        )

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(Acc(self.state()))
        Requires(Implies(not Stateless(other), Acc(state_pred(other))))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                isinstance(other, Fraction),
                Unfolding(self.state(), Unfolding(state_pred(other),
                    Result() == (
                        self.num == cast(Fraction, other).num and
                        self.denom == cast(Fraction, other).denom
                    )
                ))
            )
        ) 
        # Ensures(
        #     Implies(
        #         isinstance(other, Int),
        #         Unfolding(self.state(), Unfolding(state_pred(other),
        #             Result() == (cast(Int, other).denom != 0 and
        #                         self.num == cast(Fraction, other).num and
        #                         self.denom == cast(Fraction, other).denom)
        #         ))
        #     )
        # ) 
        Ensures(
            Implies(
                isinstance(other, Int),
                Unfolding(self.state(), Unfolding(state_pred(other),
                    Result() == (
                        (self.num == 1 and self.denom == 0 and cast(Int, other).i is None) or
                        (self.denom != 0 and not cast(Int, other).i is None) and self.num == cast(Int, other).i and self.denom == 1)
                    )
                )
            )
        )
        # Ensures(Implies(Unfolding(self.state(), self.denom == 0), not Result()))
        # Ensures(Implies(isinstance(other, Fraction) and Unfolding(state_pred(other), cast(Fraction, other).denom == 0), not Result()))
        # Ensures(
        #     Implies(
        #         isinstance(other, Int),
        #         Unfolding(self.state(), Unfolding(state_pred(other),
        #             Result() == (
        #                 self.denom != 0 and not self.denom_zero and (self.num % self.denom == 0) and 
        #                 (self.num // self.denom) == cast(Int, other).i
        #             )
        #         ))
        #     )
        # )
        if self is other:
            return True
        if isinstance(other, Fraction):
            return Unfolding(self.state(), Unfolding(state_pred(other),
                self.num == cast(Fraction, other).num and
                self.denom == cast(Fraction, other).denom
            ))
        elif isinstance(other, Int):
            return Unfolding(self.state(), Unfolding(state_pred(other),
                (self.num == 1 and self.denom == 0 and cast(Int, other).i is None) or
                (self.denom != 0 and not cast(Int, other).i is None) and self.num == cast(Int, other).i and self.denom == 1)
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.num) and Acc(self.denom)


class Int:
    def __init__(self, i: Optional[int]):
        Ensures(self.state())
        Ensures(Unfolding(self.state(), self.i is i))

        self.i: Optional[int] = i
        Fold(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(Acc(self.state()))
        Requires(Implies(not Stateless(other), Acc(state_pred(other))))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                isinstance(other, Int),
                Unfolding(self.state(), Unfolding(state_pred(other),
                    Result() == (self.i is None and cast(Int, other).i is None or 
                                 not (self.i is None or cast(Int, other).i is None) and self.i == cast(Int, other).i)
                ))
            )
        )
        Ensures(
            Implies(
                isinstance(other, Fraction),
                Unfolding(self.state(), Unfolding(state_pred(other),
                    Result() == (
                        (self.i is None and cast(Fraction, other).num == 1 and cast(Fraction, other).denom == 0) or
                        (not (self.i is None) and cast(Fraction, other).denom != 0 and
                         cast(Fraction, other).num == self.i and cast(Fraction, other).denom == 1)
                    )
                ))
            )
        ) 
        # Ensures(
        #     Implies(
        #         isinstance(other, Int),
        #         Unfolding(self.state(), Unfolding(state_pred(other),
        #             Result() == (self.i == cast(Int, other).i)
        #         ))
        #     )
        # )
        # Ensures(
        #     Implies(
        #         isinstance(other, Fraction),
        #         Unfolding(self.state(), Unfolding(state_pred(other),
        #             Result() == (
        #                 (cast(Fraction, other).denom != 0 and not cast(Fraction, other).denom_zero) and
        #                 (cast(Fraction, other).num % cast(Fraction, other).denom == 0) and
        #                 (self.i == (cast(Fraction, other).num // cast(Fraction, other).denom))
        #             )
        #         ))
        #     )
        # )
        # if isinstance(other, Int):
        #     return Unfolding(self.state(), self.i) == Unfolding(state_pred(other), cast(Int, other).i)
        # if isinstance(other, Fraction):
        #     return Unfolding(self.state(), Unfolding(state_pred(other),
        #         cast(Fraction, other).denom != 0 and not cast(Fraction, other).denom_zero and (cast(Fraction, other).num % cast(Fraction, other).denom == 0) and
        #         (self.i == cast(Fraction, other).num // cast(Fraction, other).denom)
        #     ))
        # return False
        if self is other:
            return True
        if isinstance(other, Int):
            return Unfolding(self.state(), Unfolding(state_pred(other),
                (self.i is None and cast(Int, other).i is None) or 
                (not (self.i is None or cast(Int, other).i is None) and self.i == cast(Int, other).i)
            ))
        elif isinstance(other, Fraction):
            return Unfolding(self.state(), Unfolding(state_pred(other),
                (self.i is None and cast(Fraction, other).num == 1 and cast(Fraction, other).denom == 0) or
                (not (self.i is None) and cast(Fraction, other).denom != 0 and cast(Fraction, other).num == self.i and cast(Fraction, other).denom == 1)
            ))
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.i)


# if __name__ == '__main__':
#     f: Fraction = Fraction(8, 4)
#     i: Int = Int(2)
#     Assert(f == i)
#     Assert(i == f)

    # ff: Fraction = Fraction(17, 0)
    # fff: Fraction = Fraction(2, 0)
    # ii: Int = Int(None)
    # Assert(ff == ii)
    # Assert(ii == ff)
    # Assert(ff == fff)
    # Assert(fff == ff)
    # Assert(fff == ii)
    # Assert(ii == fff)
