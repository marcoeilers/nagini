# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from typing import List
from nagini_contracts.contracts import *


class foo_list:
    @Predicate
    def predicate(self) -> bool:
        return Acc(self._buf) and list_pred(self._buf)

    def __init__(self) -> None:
        self._buf: List[int] = []
        Fold(self.predicate())
        Ensures(self.predicate())

    @Pure
    def buf(self) -> List[int]:
        Requires(Rd(self.predicate()))
        #:: ExpectedOutput(invalid.program:invalid.contract.position)
        Ensures(list_pred(Result()))
        return Unfolding(self.predicate(), self._buf)
