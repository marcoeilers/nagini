# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from dataclasses import dataclass

#:: ExpectedOutput(unsupported:keyword unsupported)
@dataclass(frozen=True, init=False)
class NonInit:
    data: int