"""
fixpoint PyClass PyClass_ObjectType(){
        return ObjectType;
}
fixpoint PyClass PyClass_module_0classA(){
        return PyClass("module_0classA", PyClass_ObjectType);
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
    requires pyobj_hasvalue(args, PyTuple_v(cons(pair(?l__ptr, PyClass_t(FAILED PYTYPE TRANSLATION)), nil))) &*&
    pyobj_hasvalue(l__ptr, PyClass_List) &*&
    pyobj_hascontent(l__ptr, ?l__content__ptr) &*&
    forall_predfact(?l__content, pyobj_hasval, True, PyLong_wrap, nil) &*&
    (map(fst, l__content) == l__content__ptr) &*&
    (some(map(snd, l__content)) == some(?l__content__val));

    ensures pyobj_hasvalue(args, PyTuple_v(cons(pair(l__ptr, PyClass_t(FAILED PYTYPE TRANSLATION)), nil))) &*&
    pyobj_hasvalue(l__ptr, PyClass_List) &*&
    pyobj_hasvalue(result, PyLong_v(?result__val)) &*&
    pyobj_hascontent(l__ptr, ?NEW_l__content__ptr) &*&
    forall_predfact(?NEW_l__content, pyobj_hasval, True, PyLong_wrap, nil) &*&
    (map(fst, NEW_l__content) == NEW_l__content__ptr) &*&
    (some(map(snd, NEW_l__content)) == some(?NEW_l__content__val));
    """
    Requires(list_pred(l))
    Ensures(list_pred(l))
    
@ContractOnly
@Native
def test_listpred2(l: List[int]) -> int:
    """
    requires pyobj_hasvalue(args, PyTuple_v(cons(pair(?l__ptr, PyClass_t(FAILED PYTYPE TRANSLATION)), nil))) &*&
    pyobj_hasvalue(l__ptr, PyClass_List) &*&
    [1/3]pyobj_hascontent(l__ptr, ?l__content__ptr) &*&
    [1/3]forall_predfact(?l__content, pyobj_hasval, True, PyLong_wrap, nil) &*&
    (map(fst, l__content) == l__content__ptr) &*&
    (some(map(snd, l__content)) == some(?l__content__val));

    ensures pyobj_hasvalue(args, PyTuple_v(cons(pair(l__ptr, PyClass_t(FAILED PYTYPE TRANSLATION)), nil))) &*&
    pyobj_hasvalue(l__ptr, PyClass_List) &*&
    pyobj_hasvalue(result, PyLong_v(?result__val)) &*&
    [1/3]pyobj_hascontent(l__ptr, ?NEW_l__content__ptr) &*&
    [1/3]forall_predfact(?NEW_l__content, pyobj_hasval, True, PyLong_wrap, nil) &*&
    (map(fst, NEW_l__content) == NEW_l__content__ptr) &*&
    (some(map(snd, NEW_l__content)) == some(?NEW_l__content__val));
    """
    Requires(Acc(list_pred(l), 1/3))
    Ensures(Acc(list_pred(l), 1/3))

@ContractOnly
@Native
def test_length(l: List[classA]) -> int:
    """
    """
    Requires(Acc(list_pred(l), 1/3) and 
             len(l) > 200)
    Ensures(Acc(list_pred(l), 1/3) and Old(len(l))+1 == len(l))