"""
fixpoint PyClass PyClass_ObjectType(){
                return ObjectType;
}
"""
from nagini_contracts.contracts import *
@ContractOnly
@Native
def test_setup1(i:int, f:float, b:bool) -> int:
        """ 
        requires PyExc(none, none) &*&
        pyobj_hasval(args, PyTuple_v(cons(pair(?i__ptr, PyLong_t), cons(pair(?f__ptr, PyFloat_t), cons(pair(?b__ptr, PyBool_t), nil))))) &*&
        pyobj_hasval(i__ptr, PyLong_v(?i__val)) &*&
        pyobj_hasval(f__ptr, PyFloat_v(?f__val)) &*&
        pyobj_hasval(b__ptr, PyBool_v(?b__val));

        ensures PyExc(none, none) &*&
        pyobj_hasval(args, PyTuple_v(cons(pair(i__ptr, PyLong_t), cons(pair(f__ptr, PyFloat_t), cons(pair(b__ptr, PyBool_t), nil))))) &*&
        pyobj_hasval(i__ptr, PyLong_v(i__val)) &*&
        pyobj_hasval(f__ptr, PyFloat_v(f__val)) &*&
        pyobj_hasval(b__ptr, PyBool_v(b__val)) &*&
        pyobj_hasval(result, PyLong_v(?result__val));
        """
        pass
        