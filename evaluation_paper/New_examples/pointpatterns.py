# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import cast

# Suggested patterns for implementing equality from the paper
# An Empirical Study of the Design and Implementation of Object Equality in Java

## Type compatible equality from Fig. 3
class Point2D1:
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
                isinstance(other, Point2D1),
                Unfolding(self.state(), Unfolding(state_pred(other),
                    Result() == (
                        self.x == cast(Point2D1, other).x and
                        self.y == cast(Point2D1, other).y
                    )
                ))
            )
        )
        if isinstance(other, Point2D1):
            return Unfolding(self.state(), Unfolding(state_pred(other),
                self.x == cast(Point2D1, other).x and
                self.y == cast(Point2D1, other).y
            ))
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.x) and Acc(self.y)

## Type incompatible equality from Fig. 5

class Point2D2:
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
        if other is None:
            return False
        if type(other) != type(self):
            return False
        return Unfolding(self.state(), Unfolding(state_pred(other),
            self.x == cast(Point2D2, other).x and
            self.y == cast(Point2D2, other).y
        ))

    @Predicate
    def state(self) -> bool:
        return Acc(self.x) and Acc(self.y)

class Point3D2(Point2D2):
    def __init__(self, x: int, y: int, z: int):
        Ensures(self.state())
        Ensures(Unfolding(self.state(), self.x is x and self.y is y and self.z is z))
        super().__init__(x, y)
        self.z: int = z
        Fold(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        if other is None:
            return False
        if type(other) != type(self):
            return False
        return Unfolding(self.state(), Unfolding(state_pred(other),
            self.x == cast(Point3D2, other).x and
            self.y == cast(Point3D2, other).y and
            self.z == cast(Point3D2, other).z
        ))

    @Predicate
    def state(self) -> bool:
        return Acc(self.z)

##  Hybrid equality from Fig. 8

class Point2D3:
    def __init__(self, x: int, y: int):
        Ensures(self.state())
        Ensures(Unfolding(self.state(), self.x is x and self.y is y))
        self.x: int = x
        self.y: int = y
        Fold(self.state())


    ## Currently cannot prove transitivity for this because equalsDelegate is not known to be transitive.
    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                isinstance(other, Point2D3),
                Result() == (Unfolding(self.state(), Unfolding(state_pred(other),
                                                  (
                                                          self.x == cast(Point2D3, other).x and
                                                          self.y == cast(Point2D3, other).y
                                                  )
                                                  )) and
                             cast(Point2D3, other).equalsDelegate(self) and
                             self.equalsDelegate(other))
            )
        )
        if not isinstance(other, Point2D3):
            return False
        return Unfolding(self.state(), Unfolding(state_pred(other),
            self.x == cast(Point2D3, other).x and
            self.y == cast(Point2D3, other).y
        )) and cast(Point2D3, other).equalsDelegate(self) and self.equalsDelegate(other)

    @Pure
    def equalsDelegate(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        return True

    @Predicate
    def state(self) -> bool:
        return Acc(self.x) and Acc(self.y)


class ColorPoint(Point2D3):
    def __init__(self, x: int, y: int, color: str):
        Ensures(self.state())
        Ensures(Unfolding(self.state(), self.x is x and self.y is y and self.color is color))
        super().__init__(x, y)
        self.color: str = color
        Fold(self.state())

    @Pure
    def equalsDelegate(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        if not isinstance(other, ColorPoint):
            return False
        return Unfolding(self.state(), Unfolding(state_pred(other),
                                                 self.x == cast(ColorPoint, other).x and
                                                 self.y == cast(ColorPoint, other).y and
                                                 self.color == cast(ColorPoint, other).color
                                                 ))

    @Predicate
    def state(self) -> bool:
        return Acc(self.color)