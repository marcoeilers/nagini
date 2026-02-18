# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from dataclasses import dataclass

@dataclass(frozen=False) #:: ExpectedOutput(unsupported:Non frozen dataclass currently not supported)
class NonFrozen2:
    data: int