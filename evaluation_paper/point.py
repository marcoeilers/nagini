# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import cast


class Point:
    def __init__(self, x: int, y: int):
        Ensures(self.state())
        Ensures(Unfolding(self.state(), self.x is x and self.y is y))
        self.x: int = x
        self.y: int = y
        Fold(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                isinstance(other, Point), 
                Unfolding(self.state(), Unfolding(state_pred(other),
                    Result() == (
                        self.x == cast(Point, other).x and
                        self.y == cast(Point, other).y 
                    )
                ))
            )
        )
        if isinstance(other, Point):
            return Unfolding(self.state(), Unfolding(state_pred(other),
                self.x == cast(Point, other).x and 
                self.y == cast(Point, other).y
            ))
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.x) and Acc(self.y)

class ColorPoint(Point):
    def __init__(self, x: int, y: int, color: str):
        Ensures(self.state())
        Ensures(Unfolding(self.state(), self.x is x and self.y is y and self.color is color))
        super().__init__(x, y)
        self.color: str = color
        Fold(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                isinstance(other, ColorPoint), 
                Unfolding(self.state(), Unfolding(state_pred(other),
                    Result() == (
                        self.x == cast(ColorPoint, other).x and
                        self.y == cast(ColorPoint, other).y and
                        self.color == cast(ColorPoint, other).color
                    )
                ))
            )
        )
        if isinstance(other, ColorPoint):
            return Unfolding(self.state(), Unfolding(state_pred(other),
                self.x == cast(ColorPoint, other).x and 
                self.y == cast(ColorPoint, other).y and
                self.color == cast(ColorPoint, other).color
            ))
        return False
    
    @Predicate
    def state(self) -> bool:
        return Acc(self.color)