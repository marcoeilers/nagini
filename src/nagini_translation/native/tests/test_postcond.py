"""
fixpoint PyClass PyClass_ObjectType(){
                return ObjectType;
}
fixpoint PyClass PyClass_module_0classA(){
                return PyClass("module_0classA", PyClass_ObjectType, nil);
}
"""
from nagini_contracts.contracts import *
from typing import List, Tuple

class classA:
        def __init__(self, arg1: Tuple[int, int], arg2: int) -> None:
                self.attr1 = arg1
                self.attr2 = arg2


@ContractOnly
@Native
def method(x: classA) -> int:
        """
        requires PyExc(none, none) &*&
        pyobj_hasval(args, PyTuple_v(cons(pair(?x__ptr, PyClass_t(PyClass_module_0classA())), nil))) &*&
        pyobj_hasval(x__ptr, PyClassInstance_v(PyClass_module_0classA())) &*&
        pyobj_hasattr(x__ptr, "attr2", ?x_DOT_attr2__ptr) &*&
        pyobj_hasval(x_DOT_attr2__ptr, PyLong_v(?x_DOT_attr2__val));

        ensures PyExc(none, none) &*&
        pyobj_hasval(args, PyTuple_v(cons(pair(x__ptr, PyClass_t(PyClass_module_0classA())), nil))) &*&
        pyobj_hasval(x__ptr, PyClassInstance_v(PyClass_module_0classA())) &*&
        pyobj_hasval(result, PyLong_v(?result__val)) &*&
        pyobj_hasattr(x__ptr, "attr2", ?NEW_x_DOT_attr2__ptr) &*&
        pyobj_hasval(NEW_x_DOT_attr2__ptr, PyLong_v(?NEW_x_DOT_attr2__val)) &*&
        (NEW_x_DOT_attr2__val == x_DOT_attr2__val);
        """
        Requires(Acc(x.attr2))
        Ensures(Acc(x.attr2) and x.attr2 == Old(x.attr2))


@ContractOnly
@Native
def method2(x: classA) -> int:
        """
        requires PyExc(none, none) &*&
        pyobj_hasval(args, PyTuple_v(cons(pair(?x__ptr, PyClass_t(PyClass_module_0classA())), nil))) &*&
        pyobj_hasval(x__ptr, PyClassInstance_v(PyClass_module_0classA())) &*&
        pyobj_hasattr(x__ptr, "attr1", ?x_DOT_attr1__ptr) &*&
        pyobj_hasval(x_DOT_attr1__ptr, PyTuple_v(cons(pair(?x_DOT_attr1_AT0__ptr, PyLong_t), cons(pair(?x_DOT_attr1_AT1__ptr, PyLong_t), nil)))) &*&
        pyobj_hasval(x_DOT_attr1_AT0__ptr, PyLong_v(?x_DOT_attr1_AT0__val)) &*&
        pyobj_hasval(x_DOT_attr1_AT1__ptr, PyLong_v(?x_DOT_attr1_AT1__val));

        ensures PyExc(none, none) &*&
        pyobj_hasval(args, PyTuple_v(cons(pair(x__ptr, PyClass_t(PyClass_module_0classA())), nil))) &*&
        pyobj_hasval(x__ptr, PyClassInstance_v(PyClass_module_0classA())) &*&
        pyobj_hasval(result, PyLong_v(?result__val)) &*&
        pyobj_hasattr(x__ptr, "attr1", ?NEW_x_DOT_attr1__ptr) &*&
        pyobj_hasval(NEW_x_DOT_attr1__ptr, PyTuple_v(cons(pair(?NEW_x_DOT_attr1_AT0__ptr, PyLong_t), cons(pair(?NEW_x_DOT_attr1_AT1__ptr, PyLong_t), nil)))) &*&
        pyobj_hasval(NEW_x_DOT_attr1_AT0__ptr, PyLong_v(?NEW_x_DOT_attr1_AT0__val)) &*&
        pyobj_hasval(NEW_x_DOT_attr1_AT1__ptr, PyLong_v(?NEW_x_DOT_attr1_AT1__val)) &*&
        ((NEW_x_DOT_attr1_AT0__val == x_DOT_attr1_AT0__val) && (NEW_x_DOT_attr1_AT1__val == x_DOT_attr1_AT1__val));
        """
        Requires(Acc(x.attr1))
        Ensures(Acc(x.attr1))
        Ensures(x.attr1 == Old(x.attr1))

@ContractOnly
@Native
def method3(x: classA) -> classA:
        """
        requires PyExc(none, none) &*&
        pyobj_hasval(args, PyTuple_v(cons(pair(?x__ptr, PyClass_t(PyClass_module_0classA())), nil))) &*&
        pyobj_hasval(x__ptr, PyClassInstance_v(PyClass_module_0classA())) &*&
        pyobj_hasattr(x__ptr, "attr2", ?x_DOT_attr2__ptr) &*&
        pyobj_hasval(x_DOT_attr2__ptr, PyLong_v(?x_DOT_attr2__val));

        ensures PyExc(none, none) &*&
        pyobj_hasval(args, PyTuple_v(cons(pair(x__ptr, PyClass_t(PyClass_module_0classA())), nil))) &*&
        pyobj_hasval(x__ptr, PyClassInstance_v(PyClass_module_0classA())) &*&
        pyobj_hasval(result, PyClassInstance_v(PyClass_module_0classA())) &*&
        pyobj_hasattr(x__ptr, "attr2", ?NEW_x_DOT_attr2__ptr) &*&
        pyobj_hasval(NEW_x_DOT_attr2__ptr, PyLong_v(?NEW_x_DOT_attr2__val)) &*&
        (NEW_x_DOT_attr2__val == x_DOT_attr2__val) &*&
        pyobj_hasattr(result, "attr2", ?NEW_result_DOT_attr2__ptr) &*&
        pyobj_hasval(NEW_result_DOT_attr2__ptr, PyLong_v(?NEW_result_DOT_attr2__val));
        """
        Requires(Acc(x.attr2))
        Ensures(Acc(x.attr2) and x.attr2 == Old(x.attr2))
        Ensures(Acc(Result().attr2))