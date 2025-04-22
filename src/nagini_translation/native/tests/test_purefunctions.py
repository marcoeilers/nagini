"""
        fixpoint PyClass PyClass_ObjectType(){
                return ObjectType;
}

//WARNING: Pure function purefunction has a predicate in its precondition. => Not translated

fixpoint int PURE_purefunction1(PyObject* i__ptr, int i__vall){
                 return ((i__val > 0) ? (18 + 1) : ((i__val < 0) ? 0 : (18 * 2)));
}

predicate PRED_mypredicate(PyObject* i__ptr, int i__val) = (i__val > 0);
"""
from nagini_contracts.contracts import *


@Predicate
def mypredicate(i: int) -> bool:
        return i > 0


@Pure
def purefunction(i: int) -> int:
        Requires(i > 0)
        Requires(mypredicate(i))
        y = 18
        if (i > 0):
                y = y + 1
        elif (i < 0):
                return 0
        else:
                y = y * 2
                return y
        return y


@Pure
def purefunction1(i: int) -> int:
        Requires(i > 0)
        y = 18
        if (i > 0):
                y = y + 1
        elif (i < 0):
                return 0
        else:
                y = y * 2
                return y
        return y


@ContractOnly
@Native
def mytest(i: int) -> int:
        """
        requires PyExc(none, none) &*&
        pyobj_hasvalue(args, PyTuple_v(cons(pair(?i__ptr, PyLong_t), nil))) &*&
        pyobj_hasvalue(i__ptr, PyLong_v(?i__val)) &*&
        (PURE_purefunction1(i__ptr, i__val) > 0);

        ensures PyExc(none, none) &*&
        pyobj_hasvalue(args, PyTuple_v(cons(pair(i__ptr, PyLong_t), nil))) &*&
        pyobj_hasvalue(i__ptr, PyLong_v(i__val)) &*&
        pyobj_hasvalue(result, PyLong_v(?result__val));
        """
        #Requires(purefunction(i) > 0)
        Requires(purefunction1(i) > 0)
