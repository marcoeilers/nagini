"""
fixpoint PyClass PyClass_ObjectType(){
      return ObjectType;
}
fixpoint PyClass PyClass_module_1mytupledclass(){
      return PyClass("module_1mytupledclass", PyClass_ObjectType);
}
"""
import nagini_translation.t1 as t1
from nagini_contracts.contracts import *

@ContractOnly
@Native
#TODO: this passes the translation and fails the verification
def compare3(c: t1.mytupledclass) -> int:
      """
      requires pyobj_hasvalue(args, PyTuple_v(cons(pair(?c__ptr, PyClass_t(PyClass_module_1mytupledclass)), nil))) &*&
      pyobj_hasvalue(c__ptr, PyClassInstance_v(PyClass_module_1mytupledclass)) &*&
      pyobj_hasattr(c__ptr, arg, ?c_DOT_arg__ptr) &*&
      pyobj_hasvalue(c_DOT_arg__ptr, PyLong_v(?c_DOT_arg__val)) &*&
      false;

      ensures pyobj_hasvalue(args, PyTuple_v(cons(pair(c__ptr, PyClass_t(PyClass_module_1mytupledclass)), nil))) &*&
      pyobj_hasvalue(c__ptr, PyClassInstance_v(PyClass_module_1mytupledclass)) &*&
      pyobj_hasvalue(result, PyLong_v(?result__val));
      """
      Requires(Acc(c.arg) and c.arg == (3,(21,12)))