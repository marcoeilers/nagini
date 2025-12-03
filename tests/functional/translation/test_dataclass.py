# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from dataclasses import dataclass

@dataclass(frozen=True)
class foo:
    num: int
    name: str
    obj: list[int]

@dataclass(frozen=True)
class A:
    data: foo