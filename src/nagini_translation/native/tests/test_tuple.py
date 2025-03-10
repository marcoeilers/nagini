"""
fixpoint PyClass PyClass_ObjectType(){
    return ObjectType;
}
"""
from nagini_contracts.contracts import *
from typing import List, Tuple


@ContractOnly
@Native
def simpletuple(t: Tuple[int, int]) -> int:
    """
    pyobj_hasvalue(args, PyTuple_v(cons(pair(?t__ptr, PyTuple_t(cons(PyLong_t, cons(PyLong_t, nil)))), nil))) &*&
    pyobj_hasvalue(t__ptr, PyTuple_v(cons(pair(?t_AT0__ptr, PyLong_t), cons(pair(?t_AT1__ptr, PyLong_t), nil)))) &*&
    pyobj_hasvalue(t_AT0__ptr, PyLong_v(?t_AT0__val)) &*&
    pyobj_hasvalue(t_AT1__ptr, PyLong_v(?t_AT1__val)) &*&
    ((t_AT0__val == 1) && (t_AT1__val == 2))
    """
    Requires(t == (1, 2))
    Ensures(Result() == 3)

@ContractOnly
@Native
def doubletuple(t: Tuple[Tuple[int, int]]) -> int:
    """
    pyobj_hasvalue(args, PyTuple_v(cons(pair(?t__ptr, PyTuple_t(cons(PyTuple_t(cons(PyLong_t, cons(PyLong_t, nil))), nil))), nil))) &*&
    pyobj_hasvalue(t__ptr, PyTuple_v(cons(pair(?t_AT0__ptr, PyTuple_t(cons(PyLong_t, cons(PyLong_t, nil)))), nil))) &*&
    pyobj_hasvalue(t_AT0__ptr, PyTuple_v(cons(pair(?t_AT0_AT0__ptr, PyLong_t), cons(pair(?t_AT0_AT1__ptr, PyLong_t), nil)))) &*&
    pyobj_hasvalue(t_AT0_AT0__ptr, PyLong_v(?t_AT0_AT0__val)) &*&
    pyobj_hasvalue(t_AT0_AT1__ptr, PyLong_v(?t_AT0_AT1__val)) &*&
    false
    """
    Requires(t == ((1, 2), 3))
    Ensures(Result() == 3)
