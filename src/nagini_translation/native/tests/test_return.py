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
        requires PyExc(none, none) &*&
        pyobj_hasval(args, PyTuple_v(nil)) &*&
        true;
        ensures PyExc(none, none) &*&
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
        requires PyExc(none, none) &*&
        pyobj_hasval(args, PyTuple_v(nil)) &*&
        true;
        ensures PyExc(none, none) &*&
        pyobj_hasval(args, PyTuple_v(nil)) &*&
        pyobj_hasval(result, PyNone_v) &*&
        true;
        """
        Requires(True)
        Ensures(True)