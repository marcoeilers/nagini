"""
fixpoint PyClass PyClass_ObjectType(){
        return ObjectType;
}
fixpoint PyClass PyClass_module_0Super(PyObj_Type T, PyObj_Type V){
        return PyClass("module_0Super", PyClass_ObjectType, nil);
}
fixpoint PyClass PyClass_module_0Someclass(PyObj_Type T, PyObj_Type V, PyObj_Type W){
        return PyClass("module_0Someclass", PyClass_module_0Super(T, V), cons(W, nil));
}
"""
from nagini_contracts.contracts import *
from typing import List, TypeVar, Generic

T = TypeVar('T')
V = TypeVar('V', bound=int)
W = TypeVar('W')



class Super(Generic[T, V]):
    def __init__(self, t: T, v: V) -> None:
        Ensures(Acc(self.t) and self.t is t)  # type: ignore
        Ensures(Acc(self.v) and self.v is v)  # type: ignore
        self.t = t
        self.v = v
class Someclass(Generic[T, V, W], Super[T, V]):
    def __init__(self, t: T, v: V, w: W) -> None:
        Ensures(Acc(self.t) and self.t is t)  # type: ignore
        Ensures(Acc(self.v) and self.v is v)  # type: ignore
        super().__init__(t, v)
        self.t = t
        self.v = v
        self.w = w
@ContractOnly
@Native
def test_forallAcc1(l: List[Someclass[float, int, float]]) -> int:
        """
        requires PyExc(none, none) &*&
        pyobj_hasvalue(args, PyTuple_v(cons(pair(?l__ptr, PyList_t(PyClass_t(PyClass_module_0Someclass(PyFloat_t, PyLong_t, PyFloat_t)))), nil))) &*&
        pyobj_hasvalue(l__ptr, PyList_v(PyClass_t(PyClass_module_0Someclass(PyFloat_t, PyLong_t, PyFloat_t)))) &*&
        pyobj_hascontent(l__ptr, ?l__content__ptr) &*&
        forall_predfact(?l__content, pyobj_hasPyClassInstanceval(PyClass_module_0Someclass(PyFloat_t, PyLong_t, PyFloat_t)), True, nil) &*&
        (map(fst, l__content) == l__content__ptr) &*&
        (some(map(snd, l__content)) == some(?l__content__val)) &*&
        forall_predfact(?l__content_DOT_t_attrptr2ptr, attr_binary_pred(hasAttr("t")), and(gte(0), lt(length(l__content__val))), nil) &*&
        (map(fst, l__content_DOT_t_attrptr2ptr) == l__content__ptr) &*&
        forall_predfact(?l__content_DOT_t, pyobj_hasPyClassInstanceval(PyClass_module_0Someclass(PyFloat_t, PyLong_t, PyFloat_t)), True, nil) &*&
        (some(map(snd, l__content_DOT_t_attrptr2ptr)) == some(?l__content_DOT_t__ptr)) &*&
        (map(fst, l__content_DOT_t) == l__content_DOT_t__ptr) &*&
        (some(map(snd, l__content_DOT_t)) == some(?l__content_DOT_t__val));
         
        ensures PyExc(none, none) &*&
        pyobj_hasvalue(args, PyTuple_v(cons(pair(l__ptr, PyList_t(PyClass_t(PyClass_module_0Someclass(PyFloat_t, PyLong_t, PyFloat_t)))), nil))) &*&
        pyobj_hasvalue(l__ptr, PyList_v(PyClass_t(PyClass_module_0Someclass(PyFloat_t, PyLong_t, PyFloat_t)))) &*&
        pyobj_hasvalue(result, PyLong_v(?result__val)) &*&
        pyobj_hascontent(l__ptr, ?NEW_l__content__ptr) &*&
        forall_predfact(?NEW_l__content, pyobj_hasPyClassInstanceval(PyClass_module_0Someclass(PyFloat_t, PyLong_t, PyFloat_t)), True, nil) &*&
        (map(fst, NEW_l__content) == NEW_l__content__ptr) &*&
        (some(map(snd, NEW_l__content)) == some(?NEW_l__content__val));
        """
        Requires(list_pred(l) and Forall(int, lambda i: Implies(i >= 0 and i < len(l), Acc(l[i].t))))
        Ensures(list_pred(l))
