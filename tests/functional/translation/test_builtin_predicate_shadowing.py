# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

# Calls to built-in predicates dispatch on the bare name, so a user definition
# with the same name would be silently shadowed by the built-in.

from typing import Optional

from nagini_contracts.contracts import Acc, Implies, Predicate


class ListNode:
    def __init__(self, val: int, next: Optional['ListNode']) -> None:
        self.val = val
        self.next = next


@Predicate
#:: ExpectedOutput(invalid.program:builtin.predicate.shadowed)
def list_pred(node: ListNode) -> bool:
    return (Acc(node.val) and Acc(node.next) and
            Implies(node.next is not None, list_pred(node.next)))
