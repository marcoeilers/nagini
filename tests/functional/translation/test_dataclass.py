# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from typing import List
from nagini_contracts.contracts import *
from dataclasses import dataclass, field

@dataclass(frozen=True)
class foo:
    num: int
    name: str
    obj: list[int]

@dataclass(frozen=True)
class A:
    data: foo
    
@dataclass(frozen=True)
class B:
    num: int = 2
    direct = 3

@dataclass(frozen=True)
class FactoryClass:
    arr: List[int] = field(default_factory=list)

@dataclass() #:: ExpectedOutput(unsupported:Non frozen dataclass currently not supported)
class NonFrozen:
    data: int

def test_cons() -> None:
    f1 = foo(1, "hello", [])

    f2 = foo(num=2, name="hello", obj=[])