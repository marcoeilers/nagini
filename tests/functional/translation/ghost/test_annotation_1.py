# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List, Tuple, Optional, Union

GInt = int
MarkGhost(GInt)

def foo() -> List[Tuple[List[int], int]]:
    pass

def bar() -> Tuple[Tuple[int, int], Tuple[GInt, GInt]]:
    pass

def union() -> Tuple[Union[int, str], int]:
    pass

def optional() -> Optional[GInt]:
    pass

def without_optional() -> Union[GInt, None]:
    gi: GInt = 0
    return gi

def futureRef() -> 'GStr':
    s: GStr = 'future'
    return s

@Ghost
def ghost() -> Union[int, GInt, None, bool]:
    pass

GStr = str
MarkGhost(GStr)