"""
fixpoint PyClass PyClass_ObjectType(){
                return ObjectType;
}
fixpoint PyClass PyClass_module_0classA(){
                return PyClass("module_0classA", PyClass_ObjectType, nil);
}
"""
from nagini_contracts.contracts import *
from typing import List
class classA:
        def __init__(self, arg: int) -> None:
                self.attr = arg

@ContractOnly
@Native
def test_listpred(l: List[int]) -> int:
        """
        requires PyExc(none, none) &*&
        pyobj_hasval(args, PyTuple_v(cons(pair(?l__ptr, PyList_t(PyLong_t)), nil))) &*&
        pyobj_hasval(l__ptr, PyList_v(PyLong_t)) &*&
        pyobj_hascontent(l__ptr, ?l__content__ptr) &*&
        forall_predfact(?l__content,  pyobj_hasPyLongval, True, nil) &*&
        (map(fst, l__content) == l__content__ptr) &*&
        (some(map(snd, l__content)) == some(?l__content__val));

        ensures PyExc(none, none) &*&
        pyobj_hasval(args, PyTuple_v(cons(pair(l__ptr, PyList_t(PyLong_t)), nil))) &*&
        pyobj_hasval(l__ptr, PyList_v(PyLong_t)) &*&
        pyobj_hasval(result, PyLong_v(?result__val)) &*&
        pyobj_hascontent(l__ptr, ?NEW_l__content__ptr) &*&
        forall_predfact(?NEW_l__content,  pyobj_hasPyLongval, True, nil) &*&
        (map(fst, NEW_l__content) == NEW_l__content__ptr) &*&
        (some(map(snd, NEW_l__content)) == some(?NEW_l__content__val));
        """
        Requires(list_pred(l))
        Ensures(list_pred(l))
        
@ContractOnly
@Native
def test_listpred2(l: List[int]) -> int:
        """
        requires PyExc(none, none) &*&
        pyobj_hasval(args, PyTuple_v(cons(pair(?l__ptr, PyList_t(PyLong_t)), nil))) &*&
        pyobj_hasval(l__ptr, PyList_v(PyLong_t)) &*&
        [1/3]pyobj_hascontent(l__ptr, ?l__content__ptr) &*&
        [1/3]forall_predfact(?l__content,  pyobj_hasPyLongval, True, nil) &*&
        (map(fst, l__content) == l__content__ptr) &*&
        (some(map(snd, l__content)) == some(?l__content__val));

        ensures PyExc(none, none) &*&
        pyobj_hasval(args, PyTuple_v(cons(pair(l__ptr, PyList_t(PyLong_t)), nil))) &*&
        pyobj_hasval(l__ptr, PyList_v(PyLong_t)) &*&
        pyobj_hasval(result, PyLong_v(?result__val)) &*&
        [1/3]pyobj_hascontent(l__ptr, ?NEW_l__content__ptr) &*&
        [1/3]forall_predfact(?NEW_l__content,  pyobj_hasPyLongval, True, nil) &*&
        (map(fst, NEW_l__content) == NEW_l__content__ptr) &*&
        (some(map(snd, NEW_l__content)) == some(?NEW_l__content__val));
        """
        Requires(Acc(list_pred(l), 1/3))
        Ensures(Acc(list_pred(l), 1/3))

@ContractOnly
@Native
def test_length(l: List[classA]) -> int:
        """
        requires PyExc(none, none) &*&
        pyobj_hasval(args, PyTuple_v(cons(pair(?l__ptr, PyList_t(PyClass_t(PyClass_module_0classA()))), nil))) &*&
        pyobj_hasval(l__ptr, PyList_v(PyClass_t(PyClass_module_0classA()))) &*&
        [1/3]pyobj_hascontent(l__ptr, ?l__content__ptr) &*&
        [1/3]forall_predfact(?l__content, pyobj_hasPyClassInstanceval(PyClass_module_0classA()), True, nil) &*&
        (map(fst, l__content) == l__content__ptr) &*&
        (some(map(snd, l__content)) == some(?l__content__val)) &*&
        (length(l__content__val) > 200);

        ensures PyExc(none, none) &*&
        pyobj_hasval(args, PyTuple_v(cons(pair(l__ptr, PyList_t(PyClass_t(PyClass_module_0classA()))), nil))) &*&
        pyobj_hasval(l__ptr, PyList_v(PyClass_t(PyClass_module_0classA()))) &*&
        pyobj_hasval(result, PyLong_v(?result__val)) &*&
        [1/3]pyobj_hascontent(l__ptr, ?NEW_l__content__ptr) &*&
        [1/3]forall_predfact(?NEW_l__content, pyobj_hasPyClassInstanceval(PyClass_module_0classA()), True, nil) &*&
        (map(fst, NEW_l__content) == NEW_l__content__ptr) &*&
        (some(map(snd, NEW_l__content)) == some(?NEW_l__content__val)) &*&
        ((length(l__content__val) + 1) == length(NEW_l__content__val));
        """
        Requires(Acc(list_pred(l), 1/3) and 
                         len(l) > 200)
        Ensures(Acc(list_pred(l), 1/3) and Old(len(l))+1 == len(l))