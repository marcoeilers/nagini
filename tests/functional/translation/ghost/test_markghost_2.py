# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List

GBoolList = List[GBool]
MarkGhost(GBoolList)
#:: ExpectedOutput(type.error:MarkGhost may only define ghost names once.)
MarkGhost(GBoolList)

def main() -> None:
    glst: GBoolList = [True]
