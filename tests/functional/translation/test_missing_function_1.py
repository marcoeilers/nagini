# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

#:: IgnoreFile(29)
from nagini_contracts.contracts import *
from typing import List


def test(r: List[int]) -> None:
    Requires(Forall(r, lambda x: (foo(x), [])))
