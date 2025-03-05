from nagini_contracts.contracts import *
from typing import List, Tuple


class ClassA:
    def __init__(self, arg: int, arg2: Tuple[int, int]) -> None:
        self.attrA1 = arg


@ContractOnly
@Native
def simple_access(i: int, i2: int, c: ClassA, d: ClassA) -> int:
    """
    pyobj_hasvalue(args, PyTuple_v(cons(pair(?i__ptr, PyLong_t), cons(pair(?i2__ptr, PyLong_t), cons(pair(?c__ptr, PyClass_t(PyClass_ClassA)), cons(pair(?d__ptr, PyClass_t(PyClass_ClassA)), nil)))))) &*&
    pyobj_hasvalue(i__ptr, PyLong_v(?i__val)) &*&
    pyobj_hasvalue(i2__ptr, PyLong_v(?i2__val)) &*&
    pyobj_hasvalue(c__ptr, PyClassInstance_v(PyClass_ClassA)) &*&
    pyobj_hasvalue(d__ptr, PyClassInstance_v(PyClass_ClassA)) &*&
    pyobj_hasattr(c__ptr, attrA1, ?c_DOT_attrA1__ptr) &*&
    pyobj_hasvalue(c_DOT_attrA1__ptr, PyLong_v(?c_DOT_attrA1__val)) &*&
    pyobj_hasattr(d__ptr, attrA1, ?d_DOT_attrA1__ptr) &*&
    pyobj_hasvalue(d_DOT_attrA1__ptr, PyLong_v(?d_DOT_attrA1__val)) &*&
    (((i__val == i2__val) ? c_DOT_attrA1__val : d_DOT_attrA1__val) == 0)
    """
    Requires(Acc(c.attrA1) and Acc(d.attrA1) and (
        c.attrA1 if (i == i2) else d.attrA1) == 0)
