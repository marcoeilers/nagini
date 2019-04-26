# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.adt import ADT
from nagini_contracts.contracts import *

from typing import (
    cast,
    List,
    NamedTuple,
)

class LinkedList(ADT):
    """
    This class defines a linked list ADT.
    """
    pass

class Node(LinkedList, NamedTuple('Node', [('elem', int), ('next', LinkedList)])):
    """
    Constructor for Node.
    """
    pass

class Null(LinkedList, NamedTuple('Null', [])):
    """
    Constructor for Null.
    """
    pass

def common_use_of_ADTs()-> None:
    l_1 = Null()

    l_2 = Node(2, Null())
    x = l_2.elem
    assert l_2.elem == x
    Assert(l_2.elem == 2)

    l_3 = Node(3, Node(4, Null()))
    assert cast(Node, l_3.next).elem == 4

def prepend(l: LinkedList, elem: int) -> LinkedList:
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

def constructor_instance_1(l: LinkedList) -> None:
    if isinstance(l, Null):
        Assert(not isinstance(l, Node))
    else:
        Assert(not isinstance(l, Null))
        Assert(isinstance(l, Node) or isinstance(l, LinkedList))

def constructor_instance_2(l: LinkedList) -> None:
    if isinstance(l, Node):
        Assert(not isinstance(l, Null))
    else:
        Assert(not isinstance(l, Node))
        Assert(isinstance(l, Null) or isinstance(l, LinkedList))

def deconstructor_in_contract_1(l: Node) -> int:
    Requires(isinstance(l.elem, int))
    Requires(l.elem == 5)
    Ensures(Result() == 10)
    return l.elem * 2

def deconstructor_in_constract_2(l: LinkedList) -> int:
    Requires(type(l) is Node)
    Requires(isinstance(cast(Node, l).elem, int))
    Requires(cast(Node, l).elem == 5)
    Ensures(Result() == 10)
    return cast(Node, l).elem * 2

def receive_object_and_convert_to_adt(o: object) -> None:
    Requires(isinstance(o, LinkedList))
    Requires(type(o) is Null)
    l = cast(LinkedList, o)
    Assert(type(o) is Null)

@Predicate
def positive_values_predicate(l: LinkedList) -> bool:
    return Implies(type(l) is Node, type(cast(Node, l).elem) is int and cast(Node, l).elem > 0 and positive_values_predicate(cast(Node, l).next))

def test_predicate_positive_values(l: LinkedList) -> None:
    Requires(positive_values_predicate(l))
    Requires(type(l) is Node)
    Ensures(positive_values_predicate(l))
    Unfold(positive_values_predicate(l))
    Assert(cast(Node, l).elem > 0)
    Fold(positive_values_predicate(l))

@Pure
def get_head(l: LinkedList) -> int:
    Requires(type(l) is Node)
    Requires(positive_values_predicate(l))
    Ensures(Result() > 0)
    return Unfolding(positive_values_predicate(l), cast(Node, l).elem)

@Pure
def get_ith_value(l: LinkedList, index: int) -> int:
    Requires(positive_values_predicate(l))
    Requires(index >= 0)
    Ensures(Result() >= 0)
    return Unfolding(positive_values_predicate(l), 0 if type(l) is Null else cast(Node, l).elem if index == 0 else get_ith_value(cast(Node, l).next, index - 1))

global_adt = Node(62, Node(32, Null()))

def test_globals() -> None:
    Assert(global_adt.elem == 62)
    Assert(cast(Node, global_adt.next).elem == 32)

def wrong_cast_1(l: LinkedList) -> None:
    Requires(l == Node(3, Node(4, Null())))
    #:: ExpectedOutput(application.precondition:assertion.false)
    temp = cast(Null, l)

def wrong_cast_2(l: LinkedList) -> None:
    Requires(l == Node(3, Null()))
    #:: ExpectedOutput(application.precondition:assertion.false)
    temp = cast(Null, l)
