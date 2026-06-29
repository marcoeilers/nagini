"""
fixpoint PyClass PyClass_ObjectType(){
	return ObjectType;
}
"""
from nagini_contracts.contracts import *

def return_float() -> float:
        """
        requires PyExc(none, none) &*&
        pyobj_hasval(args, PyTuple_v(nil)) &*&
        true;
        ensures PyExc(none, none) &*&
        pyobj_hasval(args, PyTuple_v(nil)) &*&
        pyobj_hasval(result, PyFloat_v(?result__val)) &*&
        true;
        """
        Requires(True)
        Ensures(True)
        
@ContractOnly
@Native
def return_bool() -> bool:
        """
static PyObject * return_bool(PyObject *self, PyObject *args)
requires PyExc(none, none) &*&
gil_lock(?gstate) &*&
hasRef(args, false) &*&
pyobj_hasval(args, PyTuple_v(nil)) &*&
true;

ensures PyExc(none, none) &*&
gil_lock(gstate) &*&
hasRef(args, false) &*&
hasRef(result, true) &*&
pyobj_hasval(args, PyTuple_v(nil)) &*&
pyobj_hasval(result, PyBool_v(?result__val)) &*&
true;
"""
        Requires(True)
        Ensures(True)
        
@ContractOnly
@Native
def return_none() -> None:
        """
static PyObject * return_none(PyObject *self, PyObject *args)
requires PyExc(none, none) &*&
gil_lock(?gstate) &*&
hasRef(args, false) &*&
pyobj_hasval(args, PyTuple_v(nil)) &*&
true;

ensures PyExc(none, none) &*&
gil_lock(gstate) &*&
hasRef(args, false) &*&
hasRef(result, true) &*&
pyobj_hasval(args, PyTuple_v(nil)) &*&
pyobj_hasval(result, PyNone_v) &*&
true;
"""
        Requires(True)
        Ensures(True)