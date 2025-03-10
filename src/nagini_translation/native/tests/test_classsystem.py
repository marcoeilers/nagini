"""
fixpoint PyClass PyClass_ObjectType(){
    return ObjectType;
}
fixpoint PyClass PyClass_module_0ClassA(){
      return PyClass("module_0ClassA", PyClass_ObjectType);
}
fixpoint PyClass PyClass_module_0ClassB(){
      return PyClass("module_0ClassB", PyClass_ClassA);
}
fixpoint PyClass PyClass_module_0ClassC(){
      return PyClass("module_0ClassC", PyClass_ClassB);
}
fixpoint PyClass PyClass_module_0ClassD(){
      return PyClass("module_0ClassD", PyClass_ClassC);
}
fixpoint PyClass PyClass_module_0ClassB2(){
      return PyClass("module_0ClassB2", PyClass_ClassA);
}
fixpoint PyClass PyClass_module_0ClassC2(){
      return PyClass("module_0ClassC2", PyClass_ClassB2);
}
"""
from nagini_contracts.contracts import *
from typing import List, Tuple


class ClassA:
    pass


class ClassB(ClassA):
    pass


class ClassC(ClassB):
    pass


class ClassD(ClassC):
    pass


class ClassB2(ClassA):
    pass


class ClassC2(ClassB2):
    pass


@ContractOnly
@Native
def test(a: ClassA, b: ClassB, c: ClassC, d: ClassD, b2: ClassB2, c2: ClassC2) -> int:
    """
    pyobj_hasvalue(args, PyTuple_v(cons(pair(?a__ptr, PyClass_t(PyClass_module_0ClassA)), cons(pair(?b__ptr, PyClass_t(PyClass_module_0ClassB)), cons(pair(?c__ptr, PyClass_t(PyClass_module_0ClassC)), cons(pair(?d__ptr, PyClass_t(PyClass_module_0ClassD)), cons(pair(?b2__ptr, PyClass_t(PyClass_module_0ClassB2)), cons(pair(?c2__ptr, PyClass_t(PyClass_module_0ClassC2)), nil)))))))) &*&
    pyobj_hasvalue(a__ptr, PyClassInstance_v(PyClass_module_0ClassA)) &*&
    pyobj_hasvalue(b__ptr, PyClassInstance_v(PyClass_module_0ClassB)) &*&
    pyobj_hasvalue(c__ptr, PyClassInstance_v(PyClass_module_0ClassC)) &*&
    pyobj_hasvalue(d__ptr, PyClassInstance_v(PyClass_module_0ClassD)) &*&
    pyobj_hasvalue(b2__ptr, PyClassInstance_v(PyClass_module_0ClassB2)) &*&
    pyobj_hasvalue(c2__ptr, PyClassInstance_v(PyClass_module_0ClassC2))
    """
    pass
