# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import cast

# A real word example with a reflexive, symmetric and transitive
# equality function

class Habitat:
    def __init__(self, location: str):
        self.location: str = location
        Fold(self.state())
        Ensures(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(
            Implies(
                type(self) == type(other) or self is other, 
                Unfolding(self.state(),
                    Unfolding(state_pred(other),
                        Result() == (self.location == cast(Habitat, other).location) 
                    )
                )
            )
        )
        if type(self) == type(other) or self is other:
            return Unfolding(self.state(),
                Unfolding(state_pred(other),
                    self.location == cast(Habitat, other).location
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.location)

class Animal:
    def __init__(self, habitat: Habitat, age: int, name: str):
        self.habitat: Habitat = habitat
        self.age: int = age
        self.name: str = name
        Fold(self.state())
        Ensures(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(
            Implies(
                type(self) == type(other) or self is other,
                Unfolding(self.state(),
                    Unfolding(state_pred(other),
                        Implies(
                            Result(),
                            (self.habitat == cast(Animal, other).habitat and 
                            self.age == cast(Animal, other).age and
                            self.name == cast(Animal, other).name)
                        )
                    )
                )
            )
        )
        if type(self) == type(other) or self is other:
            return Unfolding(self.state(),
                Unfolding(state_pred(other),
                    self.habitat == cast(Animal, other).habitat and 
                    self.age == cast(Animal, other).age and
                    self.name == cast(Animal, other).name
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.habitat) and Acc(self.age) and Acc(self.name) and Acc(state_pred(self.habitat))

class Bird(Animal):
    def __init__(self, habitat: Habitat, age: int, name: str, wing_size: int):
        super().__init__(habitat, age, name)
        self.wing_size: int = wing_size
        Fold(self.state())
        Ensures(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(
            Implies(
                type(self) == type(other) or self is other, 
                Unfolding(self.state(),
                    Unfolding(state_pred(other),
                        Result() == (self.habitat == cast(Bird, other).habitat and 
                                     self.age == cast(Bird, other).age and
                                     self.name == cast(Bird, other).name and
                                     self.wing_size == cast(Bird, other).wing_size)
                    )
                )
            )
        )
        if type(self) == type(other) or self is other:
            return Unfolding(self.state(),
                Unfolding(state_pred(other),
                    self.habitat == cast(Bird, other).habitat and 
                    self.age == cast(Bird, other).age and
                    self.name == cast(Bird, other).name and
                    self.wing_size == cast(Bird, other).wing_size
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.wing_size)
