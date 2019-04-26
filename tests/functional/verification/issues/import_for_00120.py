# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.adt import ADT
from typing import NamedTuple

class Tree(ADT):
    pass

class Leaf(Tree, NamedTuple('Leaf', [('elem', int)])):
    pass

class Node(Tree, NamedTuple('Node', [('left', Tree), ('right', Tree)])):
    pass