"""
fixpoint PyClass PyClass_ObjectType(){
        return ObjectType;
}
"""
from nagini_contracts.contracts import *

def test_setup1(i:int, f:float, b:bool) -> int:
    """ 
    requires pyobj_hasvalue(args, PyTuple_v(cons(pair(?i__ptr, PyLong_t), cons(pair(?f__ptr, PyFloat_t), cons(pair(?b__ptr, PyBool_t), nil))))) &*&
    pyobj_hasvalue(i__ptr, PyLong_v(?i__val)) &*&
    pyobj_hasvalue(f__ptr, PyFloat_v(?f__val)) &*&
    pyobj_hasvalue(b__ptr, PyBool_v(?b__val));

    ensures pyobj_hasvalue(args, PyTuple_v(cons(pair(i__ptr, PyLong_t), cons(pair(f__ptr, PyFloat_t), cons(pair(b__ptr, PyBool_t), nil))))) &*&
    pyobj_hasvalue(i__ptr, PyLong_v(i__val)) &*&
    pyobj_hasvalue(f__ptr, PyFloat_v(f__val)) &*&
    pyobj_hasvalue(b__ptr, PyBool_v(b__val)) &*&
    pyobj_hasvalue(result, PyLong_v(?result__val));
    """
    Requires(True)
    Ensures(True)
    