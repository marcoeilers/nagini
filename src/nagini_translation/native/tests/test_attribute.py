"""
fixpoint PyClass PyClass_ObjectType(){
    return ObjectType;
}
fixpoint PyClass PyClass_module_0ClassA(){
    return PyClass("module_0ClassA", PyClass_ObjectType);
}
"""
from nagini_contracts.contracts import *
from typing import List, Tuple


class ClassA:
    def __init__(self, arg: int, arg2: Tuple[int, int]) -> None:
        self.attrA1 = arg


@ContractOnly
@Native
def ternary_val(i: int, i2: int, c: ClassA, d: ClassA) -> int:
    """
    requires pyobj_hasvalue(args, PyTuple_v(cons(pair(?i__ptr, PyLong_t), cons(pair(?i2__ptr, PyLong_t), cons(pair(?c__ptr, PyClass_t(PyClass_module_0ClassA)), cons(pair(?d__ptr, PyClass_t(PyClass_module_0ClassA)), nil)))))) &*&
    pyobj_hasvalue(i__ptr, PyLong_v(?i__val)) &*&
    pyobj_hasvalue(i2__ptr, PyLong_v(?i2__val)) &*&
    pyobj_hasvalue(c__ptr, PyClassInstance_v(PyClass_module_0ClassA)) &*&
    pyobj_hasvalue(d__ptr, PyClassInstance_v(PyClass_module_0ClassA)) &*&
    pyobj_hasattr(c__ptr, attrA1, ?c_DOT_attrA1__ptr) &*&
    pyobj_hasvalue(c_DOT_attrA1__ptr, PyLong_v(?c_DOT_attrA1__val)) &*&
    pyobj_hasattr(d__ptr, attrA1, ?d_DOT_attrA1__ptr) &*&
    pyobj_hasvalue(d_DOT_attrA1__ptr, PyLong_v(?d_DOT_attrA1__val)) &*&
    (((i__val == i2__val) ? c_DOT_attrA1__val : d_DOT_attrA1__val) == 0);

    ensures pyobj_hasvalue(args, PyTuple_v(cons(pair(i__ptr, PyLong_t), cons(pair(i2__ptr, PyLong_t), cons(pair(c__ptr, PyClass_t(PyClass_module_0ClassA)), cons(pair(d__ptr, PyClass_t(PyClass_module_0ClassA)), nil)))))) &*&
    pyobj_hasvalue(i__ptr, PyLong_v(i__val)) &*&
    pyobj_hasvalue(i2__ptr, PyLong_v(i2__val)) &*&
    pyobj_hasvalue(c__ptr, PyClassInstance_v(PyClass_module_0ClassA)) &*&
    pyobj_hasvalue(d__ptr, PyClassInstance_v(PyClass_module_0ClassA)) &*&
    pyobj_hasattr(c__ptr, attrA1, ?NEW_c_DOT_attrA1__ptr) &*&
    pyobj_hasvalue(NEW_c_DOT_attrA1__ptr, PyLong_v(?NEW_c_DOT_attrA1__val)) &*&
    pyobj_hasattr(d__ptr, attrA1, ?NEW_d_DOT_attrA1__ptr) &*&
    pyobj_hasvalue(NEW_d_DOT_attrA1__ptr, PyLong_v(?NEW_d_DOT_attrA1__val)) &*&
    (NEW_c_DOT_attrA1__val == 1) &*&
    (NEW_d_DOT_attrA1__val == 2);
    """
    Requires(Acc(c.attrA1) and Acc(d.attrA1) and (
        c.attrA1 if (i == i2) else d.attrA1) == 0)
    Ensures(Acc(c.attrA1) and Acc(d.attrA1)
            and c.attrA1 == 1 and d.attrA1 == 2)


@ContractOnly
@Native
def double_access(i: int, i2: int, c: ClassA) -> int:
    """
    requires pyobj_hasvalue(args, PyTuple_v(cons(pair(?i__ptr, PyLong_t), cons(pair(?i2__ptr, PyLong_t), cons(pair(?c__ptr, PyClass_t(PyClass_module_0ClassA)), nil))))) &*&
    pyobj_hasvalue(i__ptr, PyLong_v(?i__val)) &*&
    pyobj_hasvalue(i2__ptr, PyLong_v(?i2__val)) &*&
    pyobj_hasvalue(c__ptr, PyClassInstance_v(PyClass_module_0ClassA)) &*&
    pyobj_hasattr(c__ptr, attrA1, ?c_DOT_attrA1__ptr) &*&
    pyobj_hasvalue(c_DOT_attrA1__ptr, PyLong_v(?c_DOT_attrA1__val)) &*&
    pyobj_hasattr(c__ptr, attrA1, c_DOT_attrA1__ptr) &*&
    pyobj_hasvalue(c_DOT_attrA1__ptr, PyLong_v(c_DOT_attrA1__val));
    
    ensures pyobj_hasvalue(args, PyTuple_v(cons(pair(i__ptr, PyLong_t), cons(pair(i2__ptr, PyLong_t), cons(pair(c__ptr, PyClass_t(PyClass_module_0ClassA)), nil))))) &*&
    pyobj_hasvalue(i__ptr, PyLong_v(i__val)) &*&
    pyobj_hasvalue(i2__ptr, PyLong_v(i2__val)) &*&
    pyobj_hasvalue(c__ptr, PyClassInstance_v(PyClass_module_0ClassA)) &*&
    pyobj_hasattr(c__ptr, attrA1, ?NEW_c_DOT_attrA1__ptr) &*&
    pyobj_hasvalue(NEW_c_DOT_attrA1__ptr, PyLong_v(?NEW_c_DOT_attrA1__val)) &*&
    pyobj_hasattr(c__ptr, attrA1, NEW_c_DOT_attrA1__ptr) &*&
    pyobj_hasvalue(NEW_c_DOT_attrA1__ptr, PyLong_v(NEW_c_DOT_attrA1__val)) &*&
    (NEW_c_DOT_attrA1__val == 0);
    """
    Requires(Acc(c.attrA1) and Acc(c.attrA1))
    Ensures(Acc(c.attrA1) and Acc(c.attrA1) and c.attrA1 == 0)


@ContractOnly
@Native
def delayed_ternary_acc(i: int, i2: int, c: ClassA, d: ClassA) -> int:
    """
    requires pyobj_hasvalue(args, PyTuple_v(cons(pair(?i__ptr, PyLong_t), cons(pair(?i2__ptr, PyLong_t), cons(pair(?c__ptr, PyClass_t(PyClass_module_0ClassA)), cons(pair(?d__ptr, PyClass_t(PyClass_module_0ClassA)), nil)))))) &*&
    pyobj_hasvalue(i__ptr, PyLong_v(?i__val)) &*&
    pyobj_hasvalue(i2__ptr, PyLong_v(?i2__val)) &*&
    pyobj_hasvalue(c__ptr, PyClassInstance_v(PyClass_module_0ClassA)) &*&
    pyobj_hasvalue(d__ptr, PyClassInstance_v(PyClass_module_0ClassA)) &*&
    (i__val == i2__val) ? (
    pyobj_hasattr(c__ptr, attrA1, ?c_DOT_attrA1__ptr) &*&
    pyobj_hasvalue(c_DOT_attrA1__ptr, PyLong_v(?c_DOT_attrA1__val))) : (
    pyobj_hasattr(d__ptr, attrA1, ?d_DOT_attrA1__ptr) &*&
    pyobj_hasvalue(d_DOT_attrA1__ptr, PyLong_v(?d_DOT_attrA1__val))) &*&
    ((i__val == i2__val) ? (None == 0) : (None == 0));

    ensures pyobj_hasvalue(args, PyTuple_v(cons(pair(i__ptr, PyLong_t), cons(pair(i2__ptr, PyLong_t), cons(pair(c__ptr, PyClass_t(PyClass_module_0ClassA)), cons(pair(d__ptr, PyClass_t(PyClass_module_0ClassA)), nil)))))) &*&
    pyobj_hasvalue(i__ptr, PyLong_v(i__val)) &*&
    pyobj_hasvalue(i2__ptr, PyLong_v(i2__val)) &*&
    pyobj_hasvalue(c__ptr, PyClassInstance_v(PyClass_module_0ClassA)) &*&
    pyobj_hasvalue(d__ptr, PyClassInstance_v(PyClass_module_0ClassA));
    """
    Requires((Acc(c.attrA1)) if i == i2 else (Acc(d.attrA1)))
    Requires((c.attrA1 == 0) if i == i2 else (d.attrA1 == 0))


@ContractOnly
@Native
def fractional(i: int, i2: int, c: ClassA, d: ClassA) -> int:
    """
    requires pyobj_hasvalue(args, PyTuple_v(cons(pair(?i__ptr, PyLong_t), cons(pair(?i2__ptr, PyLong_t), cons(pair(?c__ptr, PyClass_t(PyClass_module_0ClassA)), cons(pair(?d__ptr, PyClass_t(PyClass_module_0ClassA)), nil)))))) &*&
    pyobj_hasvalue(i__ptr, PyLong_v(?i__val)) &*&
    pyobj_hasvalue(i2__ptr, PyLong_v(?i2__val)) &*&
    pyobj_hasvalue(c__ptr, PyClassInstance_v(PyClass_module_0ClassA)) &*&
    pyobj_hasvalue(d__ptr, PyClassInstance_v(PyClass_module_0ClassA)) &*&
    [1/2]pyobj_hasattr(c__ptr, attrA1, ?c_DOT_attrA1__ptr) &*&
    [1/2]pyobj_hasvalue(c_DOT_attrA1__ptr, PyLong_v(?c_DOT_attrA1__val)) &*&
    [1/18]pyobj_hasattr(d__ptr, attrA1, ?d_DOT_attrA1__ptr) &*&
    [1/18]pyobj_hasvalue(d_DOT_attrA1__ptr, PyLong_v(?d_DOT_attrA1__val)) &*&
    (((i__val == i2__val) ? c_DOT_attrA1__val : d_DOT_attrA1__val) == 0);
    
    ensures pyobj_hasvalue(args, PyTuple_v(cons(pair(i__ptr, PyLong_t), cons(pair(i2__ptr, PyLong_t), cons(pair(c__ptr, PyClass_t(PyClass_module_0ClassA)), cons(pair(d__ptr, PyClass_t(PyClass_module_0ClassA)), nil)))))) &*&
    pyobj_hasvalue(i__ptr, PyLong_v(i__val)) &*&
    pyobj_hasvalue(i2__ptr, PyLong_v(i2__val)) &*&
    pyobj_hasvalue(c__ptr, PyClassInstance_v(PyClass_module_0ClassA)) &*&
    pyobj_hasvalue(d__ptr, PyClassInstance_v(PyClass_module_0ClassA));
    """
    Requires(Acc(c.attrA1, 1/2) and Acc(d.attrA1, 1/18) and (
        c.attrA1 if (i == i2) else d.attrA1) == 0)
    
@ContractOnly
@Native
def double_fractional(i: int, i2: int, c: ClassA) -> int:
    """
    requires pyobj_hasvalue(args, PyTuple_v(cons(pair(?i__ptr, PyLong_t), cons(pair(?i2__ptr, PyLong_t), cons(pair(?c__ptr, PyClass_t(PyClass_module_0ClassA)), nil))))) &*&
    pyobj_hasvalue(i__ptr, PyLong_v(?i__val)) &*&
    pyobj_hasvalue(i2__ptr, PyLong_v(?i2__val)) &*&
    pyobj_hasvalue(c__ptr, PyClassInstance_v(PyClass_module_0ClassA)) &*&
    [1/2]pyobj_hasattr(c__ptr, attrA1, ?c_DOT_attrA1__ptr) &*&
    [1/2]pyobj_hasvalue(c_DOT_attrA1__ptr, PyLong_v(?c_DOT_attrA1__val)) &*&
    [1/2]pyobj_hasattr(c__ptr, attrA1, c_DOT_attrA1__ptr) &*&
    [1/2]pyobj_hasvalue(c_DOT_attrA1__ptr, PyLong_v(c_DOT_attrA1__val));
    
    ensures pyobj_hasvalue(args, PyTuple_v(cons(pair(i__ptr, PyLong_t), cons(pair(i2__ptr, PyLong_t), cons(pair(c__ptr, PyClass_t(PyClass_module_0ClassA)), nil))))) &*&
    pyobj_hasvalue(i__ptr, PyLong_v(i__val)) &*&
    pyobj_hasvalue(i2__ptr, PyLong_v(i2__val)) &*&
    pyobj_hasvalue(c__ptr, PyClassInstance_v(PyClass_module_0ClassA)) &*&
    [1/2]pyobj_hasattr(c__ptr, attrA1, ?NEW_c_DOT_attrA1__ptr) &*&
    [1/2]pyobj_hasvalue(NEW_c_DOT_attrA1__ptr, PyLong_v(?NEW_c_DOT_attrA1__val)) &*&
    [1/2]pyobj_hasattr(c__ptr, attrA1, NEW_c_DOT_attrA1__ptr) &*&
    [1/2]pyobj_hasvalue(NEW_c_DOT_attrA1__ptr, PyLong_v(NEW_c_DOT_attrA1__val)) &*&
    (NEW_c_DOT_attrA1__val == 0);
    """
    Requires(Acc(c.attrA1, 1/2) and Acc(c.attrA1, 1/2))
    Ensures(Acc(c.attrA1, 1/2) and Acc(c.attrA1, 1/2) and c.attrA1 == 0)