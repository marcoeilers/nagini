#!/usr/bin/python3

# Abstract definition:
# Tree = Leaf(elem: int)
#      | Node(left: Tree, right: Tree)
#

from typing import (
    NamedTuple,
    cast
)

from nagini_contracts.adt import ADT
import import_for_00120

class Tree(ADT):
    pass

class Leaf(Tree, NamedTuple('Leaf', [('elem', int)])):
    pass

class Node(Tree, NamedTuple('Node', [('left', Tree), ('right', Tree)])):
    pass

def common_use_of_ADTs()-> None:
    t_1 = Leaf(5)
    t_2 = Leaf(6)
    t_3 = Node(t_1, t_2)

    assert t_1.elem == 5
    assert t_2.elem == 6

    assert cast(Leaf, t_3.left).elem == 5
    assert cast(Leaf, t_3.right).elem == 6
