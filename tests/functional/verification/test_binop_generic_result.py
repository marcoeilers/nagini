# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

# The result type of an operator on a generic container must keep the receiver's
# type arguments: each function below crashed the translator with an internal
# AttributeError ('PythonClass' object has no attribute 'type_args') when the
# element type of a BinOp result was needed.

from nagini_contracts.contracts import *


def binop_index() -> None:
    Assert((PSeq(1) + PSeq(2))[0] == 1)


def binop_toms() -> None:
    s = PSeq(1, 2, 2)  # type: PSeq[int]
    Assert(len(ToMS(s + s)) >= 0)


def binop_toseq() -> None:
    Assert(ToSeq(PSeq(1) + PSeq(2))[0] == 1)


def update_result() -> None:
    s = PSeq(1, 2)  # type: PSeq[int]
    Assert(s.update(0, 5)[0] == 5)


def pset_binop() -> None:
    a = PSet(1, 2)  # type: PSet[int]
    b = PSet(2, 3)  # type: PSet[int]
    Assert(len(ToSeq(a + b)) >= 0)


def pmultiset_binop() -> None:
    m = PMultiset(1, 2)  # type: PMultiset[int]
    Assert((m + m).num(1) == 2)
