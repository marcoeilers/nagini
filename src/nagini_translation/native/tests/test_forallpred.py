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
def test_forallAcc1(l: List[classA]) -> int:
        """
        requires PyExc(none, none) &*&
        pyobj_hasval(args, PyTuple_v(cons(pair(?l__ptr, PyList_t(PyClass_t(PyClass_module_0classA()))), nil))) &*&
        pyobj_hasval(l__ptr, PyList_v(PyClass_t(PyClass_module_0classA()))) &*&
        pyobj_hascontent(l__ptr, List(?l__content__ptr)) &*&
        list_forallpredfact(?l__content, pyobj_hasPyClassInstanceval(PyClass_module_0classA()), True, nil) &*&
        (map(fst, l__content) == l__content__ptr) &*&
        (some(map(snd, l__content)) == some(?l__content__val)) &*&
        list_forallpredfact(?l__content_DOT_attr_attrptr2ptr, attr_binary_pred(hasAttr("attr")), and(gte(0), lt(length(l__content__val))), nil) &*&
        (map(fst, l__content_DOT_attr_attrptr2ptr) == l__content__ptr) &*&
        list_forallpredfact(?l__content_DOT_attr, pyobj_hasPyClassInstanceval(PyClass_module_0classA()), True, nil) &*&
        (some(map(snd, l__content_DOT_attr_attrptr2ptr)) == some(?l__content_DOT_attr__ptr)) &*&
        (map(fst, l__content_DOT_attr) == l__content_DOT_attr__ptr) &*&
        (some(map(snd, l__content_DOT_attr)) == some(?l__content_DOT_attr__val));

        ensures PyExc(none, none) &*&
        pyobj_hasval(args, PyTuple_v(cons(pair(l__ptr, PyList_t(PyClass_t(PyClass_module_0classA()))), nil))) &*&
        pyobj_hasval(l__ptr, PyList_v(PyClass_t(PyClass_module_0classA()))) &*&
        pyobj_hasval(result, PyLong_v(?result__val)) &*&
        pyobj_hascontent(l__ptr, List(?NEW_l__content__ptr)) &*&
        list_forallpredfact(?NEW_l__content, pyobj_hasPyClassInstanceval(PyClass_module_0classA()), True, nil) &*&
        (map(fst, NEW_l__content) == NEW_l__content__ptr) &*&
        (some(map(snd, NEW_l__content)) == some(?NEW_l__content__val));
        """
        Requires(list_pred(l) and Forall(int,
                                                                         lambda i: Implies(i >= 0 and i < len(l), Acc(l[i].attr))))
        Ensures(list_pred(l))

@ContractOnly
@Native
def test_forallAcc2(l: List[classA], j: int) -> int:
        """
        requires PyExc(none, none) &*&
        pyobj_hasval(args, PyTuple_v(cons(pair(?l__ptr, PyList_t(PyClass_t(PyClass_module_0classA()))), cons(pair(?j__ptr, PyLong_t), nil)))) &*&
        pyobj_hasval(l__ptr, PyList_v(PyClass_t(PyClass_module_0classA()))) &*&
        pyobj_hasval(j__ptr, PyLong_v(?j__val)) &*&
        pyobj_hascontent(l__ptr, List(?l__content__ptr)) &*&
        list_forallpredfact(?l__content, pyobj_hasPyClassInstanceval(PyClass_module_0classA()), True, nil) &*&
        (map(fst, l__content) == l__content__ptr) &*&
        (some(map(snd, l__content)) == some(?l__content__val)) &*&
        [1/2]list_forallpredfact(?l__content_DOT_attr_attrptr2ptr, attr_binary_pred(hasAttr("attr")), and(gte(0), lt(length(l__content__val))), nil) &*&
        (map(fst, l__content_DOT_attr_attrptr2ptr) == l__content__ptr) &*&
        [1/2]list_forallpredfact(?l__content_DOT_attr, pyobj_hasPyClassInstanceval(PyClass_module_0classA()), True, nil) &*&
        (some(map(snd, l__content_DOT_attr_attrptr2ptr)) == some(?l__content_DOT_attr__ptr)) &*&
        (map(fst, l__content_DOT_attr) == l__content_DOT_attr__ptr) &*&
        (some(map(snd, l__content_DOT_attr)) == some(?l__content_DOT_attr__val)) &*&
        ((nth(j__val, l__content_DOT_attr__ptr) == j__ptr) || (nth(j__val, l__content_DOT_attr__val) != j__val));

        ensures PyExc(none, none) &*&
        pyobj_hasval(args, PyTuple_v(cons(pair(l__ptr, PyList_t(PyClass_t(PyClass_module_0classA()))), cons(pair(j__ptr, PyLong_t), nil)))) &*&
        pyobj_hasval(l__ptr, PyList_v(PyClass_t(PyClass_module_0classA()))) &*&
        pyobj_hasval(j__ptr, PyLong_v(j__val)) &*&
        pyobj_hasval(result, PyLong_v(?result__val)) &*&
        pyobj_hascontent(l__ptr, List(?NEW_l__content__ptr)) &*&
        list_forallpredfact(?NEW_l__content, pyobj_hasPyClassInstanceval(PyClass_module_0classA()), True, nil) &*&
        (map(fst, NEW_l__content) == NEW_l__content__ptr) &*&
        (some(map(snd, NEW_l__content)) == some(?NEW_l__content__val));
        """
        Requires(list_pred(l) and Forall(int,
                                                                         lambda i: Implies(i >= 0 and i < len(l), Acc(l[i].attr, 1/2))) and (l[j].attr is j or l[j].attr != j))
        Ensures(list_pred(l))

@ContractOnly
@Native
def test_forallAcc3(l: List[classA]) -> int:
        """
        requires PyExc(none, none) &*&
        pyobj_hasval(args, PyTuple_v(cons(pair(?l__ptr, PyList_t(PyClass_t(PyClass_module_0classA()))), nil))) &*&
        pyobj_hasval(l__ptr, PyList_v(PyClass_t(PyClass_module_0classA()))) &*&
        pyobj_hascontent(l__ptr, List(?l__content__ptr)) &*&
        list_forallpredfact(?l__content, pyobj_hasPyClassInstanceval(PyClass_module_0classA()), True, nil) &*&
        (map(fst, l__content) == l__content__ptr) &*&
        (some(map(snd, l__content)) == some(?l__content__val)) &*&
        list_forallpredfact(?l__content_DOT_attr_attrptr2ptr, attr_binary_pred(hasAttr("attr")), and(gte(0), lte(length(l__content__val))), nil) &*&
        (map(fst, l__content_DOT_attr_attrptr2ptr) == l__content__ptr) &*&
        list_forallpredfact(?l__content_DOT_attr, pyobj_hasPyClassInstanceval(PyClass_module_0classA()), True, nil) &*&
        (some(map(snd, l__content_DOT_attr_attrptr2ptr)) == some(?l__content_DOT_attr__ptr)) &*&
        (map(fst, l__content_DOT_attr) == l__content_DOT_attr__ptr) &*&
        (some(map(snd, l__content_DOT_attr)) == some(?l__content_DOT_attr__val));

        ensures PyExc(none, none) &*&
        pyobj_hasval(args, PyTuple_v(cons(pair(l__ptr, PyList_t(PyClass_t(PyClass_module_0classA()))), nil))) &*&
        pyobj_hasval(l__ptr, PyList_v(PyClass_t(PyClass_module_0classA()))) &*&
        pyobj_hasval(result, PyLong_v(?result__val)) &*&
        pyobj_hascontent(l__ptr, List(?NEW_l__content__ptr)) &*&
        list_forallpredfact(?NEW_l__content, pyobj_hasPyClassInstanceval(PyClass_module_0classA()), True, nil) &*&
        (map(fst, NEW_l__content) == NEW_l__content__ptr) &*&
        (some(map(snd, NEW_l__content)) == some(?NEW_l__content__val));
        """
        Requires(list_pred(l) and Forall(l, lambda el: Acc(el.attr)))
        Ensures(list_pred(l))

@ContractOnly
@Native
def test_forallAcc4(l: List[classA], j: int) -> int:
        """
        requires PyExc(none, none) &*&
        pyobj_hasval(args, PyTuple_v(cons(pair(?l__ptr, PyList_t(PyClass_t(PyClass_module_0classA()))), cons(pair(?j__ptr, PyLong_t), nil)))) &*&
        pyobj_hasval(l__ptr, PyList_v(PyClass_t(PyClass_module_0classA()))) &*&
        pyobj_hasval(j__ptr, PyLong_v(?j__val)) &*&
        pyobj_hascontent(l__ptr, List(?l__content__ptr)) &*&
        list_forallpredfact(?l__content, pyobj_hasPyClassInstanceval(PyClass_module_0classA()), True, nil) &*&
        (map(fst, l__content) == l__content__ptr) &*&
        (some(map(snd, l__content)) == some(?l__content__val)) &*&
        list_forallpredfact(?l__content_DOT_attr_attrptr2ptr, attr_binary_pred(hasAttr("attr")), and(gte(0), lte(length(l__content__val))), nil) &*&
        (map(fst, l__content_DOT_attr_attrptr2ptr) == l__content__ptr) &*&
        list_forallpredfact(?l__content_DOT_attr, pyobj_hasPyClassInstanceval(PyClass_module_0classA()), True, nil) &*&
        (some(map(snd, l__content_DOT_attr_attrptr2ptr)) == some(?l__content_DOT_attr__ptr)) &*&
        (map(fst, l__content_DOT_attr) == l__content_DOT_attr__ptr) &*&
        (some(map(snd, l__content_DOT_attr)) == some(?l__content_DOT_attr__val)) &*&
        (nth(j__val, l__content_DOT_attr__val) > 0);

        ensures PyExc(none, none) &*&
        pyobj_hasval(args, PyTuple_v(cons(pair(l__ptr, PyList_t(PyClass_t(PyClass_module_0classA()))), cons(pair(j__ptr, PyLong_t), nil)))) &*&
        pyobj_hasval(l__ptr, PyList_v(PyClass_t(PyClass_module_0classA()))) &*&
        pyobj_hasval(j__ptr, PyLong_v(j__val)) &*&
        pyobj_hasval(result, PyLong_v(?result__val)) &*&
        pyobj_hascontent(l__ptr, List(?NEW_l__content__ptr)) &*&
        list_forallpredfact(?NEW_l__content, pyobj_hasPyClassInstanceval(PyClass_module_0classA()), True, nil) &*&
        (map(fst, NEW_l__content) == NEW_l__content__ptr) &*&
        (some(map(snd, NEW_l__content)) == some(?NEW_l__content__val));
        """
        Requires(list_pred(l) and Forall(
                l, lambda el: Acc(el.attr)) and l[j].attr > 0)
        Ensures(list_pred(l))

@ContractOnly
@Native
def test_forallAcc5(l: List[classA],) -> int:
        """
        requires PyExc(none, none) &*&
        pyobj_hasval(args, PyTuple_v(cons(pair(?l__ptr, PyList_t(PyClass_t(PyClass_module_0classA()))), nil))) &*&
        pyobj_hasval(l__ptr, PyList_v(PyClass_t(PyClass_module_0classA()))) &*&
        pyobj_hascontent(l__ptr, List(?l__content__ptr)) &*&
        list_forallpredfact(?l__content, pyobj_hasPyClassInstanceval(PyClass_module_0classA()), True, nil) &*&
        (map(fst, l__content) == l__content__ptr) &*&
        (some(map(snd, l__content)) == some(?l__content__val)) &*&
        list_forallpredfact(?l__content_DOT_attr_attrptr2ptr, attr_binary_pred(hasAttr("attr")), and(gte(0), lte(length(l__content__val))), nil) &*&
        (map(fst, l__content_DOT_attr_attrptr2ptr) == l__content__ptr) &*&
        list_forallpredfact(?l__content_DOT_attr, pyobj_hasPyClassInstanceval(PyClass_module_0classA()), True, nil) &*&
        (some(map(snd, l__content_DOT_attr_attrptr2ptr)) == some(?l__content_DOT_attr__ptr)) &*&
        (map(fst, l__content_DOT_attr) == l__content_DOT_attr__ptr) &*&
        (some(map(snd, l__content_DOT_attr)) == some(?l__content_DOT_attr__val));

        ensures PyExc(none, none) &*&
        pyobj_hasval(args, PyTuple_v(cons(pair(l__ptr, PyList_t(PyClass_t(PyClass_module_0classA()))), nil))) &*&
        pyobj_hasval(l__ptr, PyList_v(PyClass_t(PyClass_module_0classA()))) &*&
        pyobj_hasval(result, PyLong_v(?result__val)) &*&
        pyobj_hascontent(l__ptr, List(?NEW_l__content__ptr)) &*&
        list_forallpredfact(?NEW_l__content, pyobj_hasPyClassInstanceval(PyClass_module_0classA()), True, nil) &*&
        (map(fst, NEW_l__content) == NEW_l__content__ptr) &*&
        (some(map(snd, NEW_l__content)) == some(?NEW_l__content__val));
        """
        Requires(list_pred(l) and Forall(l, lambda el: Acc(el.attr)))
        Ensures(list_pred(l))
