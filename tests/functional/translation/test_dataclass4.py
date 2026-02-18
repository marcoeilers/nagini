# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from dataclasses import dataclass, field

@dataclass(frozen=True)
class MissingType:
    #:: ExpectedOutput(unsupported:field() requires a type annotation)
    arr = field(default_factory=list)