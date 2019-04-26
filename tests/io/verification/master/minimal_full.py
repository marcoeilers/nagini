# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from nagini_contracts.io_contracts import *
from nagini_contracts.obligations import MustTerminate
from typing import Tuple
# Unverified library (stubs).
@IOOperation
def read_str_io(t1: Place, val: str = Result(),
                t2: Place = Result()) -> bool:
    Terminates(False)
@ContractOnly
def read_str(t1: Place) -> Tuple[Place, str]:
    IOExists2(Place, str)(
        lambda t2, val: (
            Requires(token(t1, 1) and read_str_io(t1, val, t2)),
            Ensures(token(t2) and Result()[0] == t2 and
                    Result()[1] is val)))
@IOOperation
def write_str_io(t1: Place, val: str, t2: Place = Result()) -> bool:
    Terminates(True)
    TerminationMeasure(1)
@ContractOnly
def write_str(t1: Place, val: str) -> Place:
    IOExists1(Place)(
        lambda t2: (
            Requires(token(t1, 1) and write_str_io(t1, val, t2) and
                     MustTerminate(1)),
            Ensures(token(t2) and Result() == t2)))
# Verified client code.
@IOOperation
def echo_io(t1: Place, t3: Place = Result()) -> bool:
    Terminates(False)
    return IOExists2(Place, str)(lambda t2, val:
        read_str_io(t1, val, t2) and write_str_io(t2, val, t3))
def echo(t1: Place) -> Place:
    IOExists1(Place)(
        lambda t3: (
            Requires(token(t1, 2) and echo_io(t1, t3)),
            Ensures(token(t3) and Result() == t3)))
    Open(echo_io(t1))
    t2, value = read_str(t1)
    t3 = write_str(t2, value)
    return t3
