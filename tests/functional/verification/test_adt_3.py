# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from typing import (
    NamedTuple,
    cast,
)

from nagini_contracts.contracts import (
    Acc,
    Assert,
    Ensures,
    Requires,
)

from nagini_contracts.adt import ADT

# Fruit ADT
class Fruit(ADT):
    pass

class Banana(Fruit, NamedTuple('Banana', [])):
    pass

class Grape(Fruit, NamedTuple('Grape', [])):
    pass

# Tree ADT (compound ADT)
class Tree(ADT):
    pass

class Leaf(Tree, NamedTuple('Leaf', [('fruit', Fruit)])):
    pass

class Node(Tree, NamedTuple('Node', [('left', Tree), ('right', Tree)])):
    pass

def common_use_of_ADTs()-> None:
    t_1 = Leaf(Banana())
    t_2 = Leaf(Grape())
    polymorphic_tree = Node(t_1, t_2)

    assert isinstance(t_1, Leaf)
    assert isinstance(t_1.fruit, Fruit)
    assert isinstance(t_1.fruit, Banana)

    assert type(t_2.fruit) is Grape

    Assert(type(cast(Node, polymorphic_tree).left) is Leaf)
    Assert(type(cast(Leaf, cast(Node, polymorphic_tree).left).fruit) is Banana)

    Assert(type(cast(Node, polymorphic_tree).right) is Leaf)
    Assert(type(cast(Leaf, cast(Node, polymorphic_tree).right).fruit) is Grape)

# Ordinary class
class Property:
    def __init__(self, weight: int) -> None:
        Ensures(Acc(self.weight))
        self.weight = weight    # type: int

# An ADT that aggregates an object from ordinary class
class Pineapple(Fruit, NamedTuple('Pineapple', [('property', Property)])):
    pass

def heterogeneous_composition() -> None:
    pinapple = Pineapple(Property(400))
    x = pinapple.property.weight
