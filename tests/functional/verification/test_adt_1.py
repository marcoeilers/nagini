from nagini_contracts.adt import ADT
from nagini_contracts.contracts import *

from typing import (
    cast,
    List,
    NamedTuple,
)

class LinkedList(ADT):
    pass

class Node(LinkedList, NamedTuple('Node', [('elem', int), ('next', LinkedList)])):
    pass

class Null(LinkedList, NamedTuple('Null', [])):
    pass

def common_use_of_ADTs()-> None:
    l_1 = Null()

    l_2 = Node(2, Null())
    x = l_2.elem
    assert l_2.elem == x
    Assert(l_2.elem == 2)

    l_3 = Node(3, Node(4, Null()))
    assert cast(Node, l_3.next).elem == 4

def preppend(l: LinkedList, elem: int) -> LinkedList:
    Ensures(Result() == Node(elem, l))
    return Node(elem, l)

def constructor_totality_1(l: LinkedList) -> None:
    if type(l) is Node:
        Assert(type(l) is not Null)
    else:
        Assert(type(l) is Null)

def constructor_totality_2(l: LinkedList) -> None:
    if type(l) is Null:
        Assert(type(l) is not Node)
    else:
        Assert(type(l) is Node)

def wrong_cast_1(l: LinkedList) -> None:
    Requires(l == Node(3, Node(4, Null())))
    #:: ExpectedOutput(application.precondition:assertion.false)
    temp = cast(Null, l)

def wrong_cast_2(l: LinkedList) -> None:
    Requires(l == Node(3, Null()))
    #:: ExpectedOutput(application.precondition:assertion.false)
    temp = cast(Null, l)
