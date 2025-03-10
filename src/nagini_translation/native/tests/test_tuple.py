"""
fixpoint PyClass PyClass_ObjectType(){
    return ObjectType;
}
"""
from nagini_contracts.contracts import *
from typing import List, Tuple


@ContractOnly
@Native
def simpletuple_eq(t: Tuple[int, int]) -> int:
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
def simpletuple_neq1(t: Tuple[int, int]) -> int:
    """
    pyobj_hasvalue(args, PyTuple_v(cons(pair(?t__ptr, PyTuple_t(cons(PyLong_t, cons(PyLong_t, nil)))), nil))) &*&
    pyobj_hasvalue(t__ptr, PyTuple_v(cons(pair(?t_AT0__ptr, PyLong_t), cons(pair(?t_AT1__ptr, PyLong_t), nil)))) &*&
    pyobj_hasvalue(t_AT0__ptr, PyLong_v(?t_AT0__val)) &*&
    pyobj_hasvalue(t_AT1__ptr, PyLong_v(?t_AT1__val)) &*&
    ((t_AT0__val != 1) || (t_AT1__val != 2))
    """
    Requires(t != (1, 2))
    Ensures(Result() == 3)
    
@ContractOnly
@Native
def simpletuple_neq2(t: Tuple[int, int]) -> int:
    """
    pyobj_hasvalue(args, PyTuple_v(cons(pair(?t__ptr, PyTuple_t(cons(PyLong_t, cons(PyLong_t, nil)))), nil))) &*&
    pyobj_hasvalue(t__ptr, PyTuple_v(cons(pair(?t_AT0__ptr, PyLong_t), cons(pair(?t_AT1__ptr, PyLong_t), nil)))) &*&
    pyobj_hasvalue(t_AT0__ptr, PyLong_v(?t_AT0__val)) &*&
    pyobj_hasvalue(t_AT1__ptr, PyLong_v(?t_AT1__val)) &*&
    true
    """
    Requires(t != (1, 2, 3))
    Ensures(Result() == 3)

@ContractOnly
@Native
def doubletuple_eq1(t: Tuple[Tuple[int, int], int]) -> int:
    """
    pyobj_hasvalue(args, 
        PyTuple_v(
            cons(
                pair(
                    ?t__ptr, 
                    PyTuple_t(
                        cons(
                            PyTuple_t(
                                cons(PyLong_t, 
                                cons(PyLong_t, nil))
                            ), 
                        cons(
                            PyLong_t
                        , nil))
                    )
                )
            , nil)
        )
    ) &*&
    pyobj_hasvalue(t__ptr, PyTuple_v(cons(pair(?t_AT0__ptr, PyTuple_t(cons(PyLong_t, cons(PyLong_t, nil)))), cons(pair(?t_AT1__ptr, PyLong_t), nil)))) &*&
    pyobj_hasvalue(t_AT0__ptr, PyTuple_v(cons(pair(?t_AT0_AT0__ptr, PyLong_t), cons(pair(?t_AT0_AT1__ptr, PyLong_t), nil)))) &*&
    pyobj_hasvalue(t_AT0_AT0__ptr, PyLong_v(?t_AT0_AT0__val)) &*&
    pyobj_hasvalue(t_AT0_AT1__ptr, PyLong_v(?t_AT0_AT1__val)) &*&
    pyobj_hasvalue(t_AT1__ptr, PyLong_v(?t_AT1__val)) &*&
    (((t_AT0_AT0__val == 1) && (t_AT0_AT1__val == 2)) && (t_AT1__val == 3))
    """
    Requires(t == ((1, 2), 3))
    Ensures(Result() == 3)