from nagini_contracts.adt import ADT
from typing import NamedTuple

class Tree(ADT):
    pass

class Leaf(Tree, NamedTuple('Leaf', [('elem', int)])):
    pass

class Node(Tree, NamedTuple('Node', [('left', Tree), ('right', Tree)])):
    pass