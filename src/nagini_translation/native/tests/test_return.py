"""
fixpoint PyClass PyClass_ObjectType(){
        return ObjectType;
}
"""
from types import NoneType
from nagini_contracts.contracts import *

def return_float() -> float:
    """
    requires pyobj_hasvalue(args, PyTuple_v(nil)) &*&
    true;
    ensures pyobj_hasvalue(args, PyTuple_v(nil)) &*&
    pyobj_hasvalue(result, PyFloat_v(?result__val)) &*&
    true;
    """
    Requires(True)
    Ensures(True)
    
@ContractOnly
@Native
def return_bool() -> bool:
    """
    requires pyobj_hasvalue(args, PyTuple_v(nil)) &*&
    true;
    ensures pyobj_hasvalue(args, PyTuple_v(nil)) &*&
    pyobj_hasvalue(result, PyBool_v(?result__val)) &*&
    true;
    """
    Requires(True)
    Ensures(True)
    
@ContractOnly
@Native
def return_none() -> None:
    """
    requires pyobj_hasvalue(args, PyTuple_v(nil)) &*&
    true;
    ensures pyobj_hasvalue(args, PyTuple_v(nil)) &*&
    pyobj_hasvalue(result, PyNone_v) &*&
    true;
    """
    Requires(True)
    Ensures(True)