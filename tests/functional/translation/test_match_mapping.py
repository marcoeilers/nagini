# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Dict


def match_mapping(d: Dict[str, int]) -> int:

    match d:  #:: ExpectedOutput(unsupported:mapping patterns not yet supported)
        case {'key': v}:
            return v
        case _:
            return 0
