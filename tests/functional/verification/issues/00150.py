# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/


from typing import Optional, List, Tuple
from nagini_contracts.contracts import *

class Node:
    def __init__(self, function_name: str, children:List['Node']) -> None:
        self.function_name = function_name # type: str
        self.children = children # type: List['Node']
        Ensures(Acc(self.function_name) and self.function_name is function_name and
                Acc(self.children) and self.children is children)

@Pure
def can_node_be_compressed(marked_execution_tree: 'Node') -> int:
    """Searches for the longest compression possible. Returns:
    - int: number of nodes that can be compressed. 0 if None"""
    Requires(Acc(marked_execution_tree.children))
    Requires(Acc(list_pred(marked_execution_tree.children)))
    Requires(Forall(int, lambda i: Implies(i >= 0 and i < len(marked_execution_tree.children),
                                           Acc(marked_execution_tree.children[i].function_name))))
    Requires(Acc(marked_execution_tree.function_name))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Implies(len(marked_execution_tree.children) != 1, Result() == 0))
    Ensures(Result() == 0)
    if len(marked_execution_tree.children) != 1:
        return 1
    if marked_execution_tree.children[0].function_name != marked_execution_tree.function_name:
        return 0
    return can_node_be_compressed(marked_execution_tree.children[0]) + 1