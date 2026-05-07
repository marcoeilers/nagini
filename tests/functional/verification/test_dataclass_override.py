# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Optional, TypeVar, Generic
from dataclasses import dataclass

T = TypeVar('T')

@dataclass(frozen=True)
class ResultDataclass(Generic[T]):
    success: bool
    error_code: int = 0
    data: Optional[T] = None
    
    @Pure
    def __bool__(self) -> bool:
        return self.success
    
    def __post_init__(self) -> None:
        Requires(Implies(self.success, self.data != None))
        Requires((self.success and self.error_code <= 0) or (not self.success and self.error_code > 0))

        if not self.success and self.error_code <= 0:
            raise Exception()

        if self.success and self.error_code > 0:
            raise Exception()
    
def test_bool() -> None:
    res = ResultDataclass(True, 0, 'data')

    assert res.success
    assert res

    #:: ExpectedOutput(assert.failed:assertion.false)
    assert res.error_code == 1

def test_bool2(res: ResultDataclass[int]) -> None:
    
    if res.success:
        assert res

    #:: ExpectedOutput(assert.failed:assertion.false)
    assert res

def test_init_False() -> None:
    res = ResultDataclass(False, 1, '')

    #:: ExpectedOutput(call.precondition:assertion.false)
    res = ResultDataclass(False, 0, None)

def test_init_code() -> None:
    res = ResultDataclass(True, 0, 'data')

    #:: ExpectedOutput(call.precondition:assertion.false)
    res = ResultDataclass(True, 1, 'data')

def test_init_None() -> None:
    res = ResultDataclass(True, 0, 'data')

    #:: ExpectedOutput(call.precondition:assertion.false)
    res = ResultDataclass(True, 0, None)

def test_data(res: ResultDataclass[str]) -> None:
    if res.success:
        #:: ExpectedOutput(assert.failed:assertion.false)
        assert isinstance(res.data, str)