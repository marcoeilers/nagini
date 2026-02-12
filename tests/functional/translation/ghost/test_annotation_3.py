# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Union, Optional


#:: ExpectedOutput(invalid.program:invalid.ghost.annotation)
def main() -> Union[Optional[GStr], Union[int, str]]:
    pass