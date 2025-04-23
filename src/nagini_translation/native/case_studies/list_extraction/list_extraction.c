
/*--END OF ENV--*/
#ifdef COMPILING FOR PYTHON
//#include <Python.h>
#else
#include "../vfpy/PythonAPI/vfpy.c"
#endif
/*@
fixpoint PyClass PyClass_ObjectType(){
    return ObjectType;
}
@*/
/*--END OF ENV--*/
/*@
lemma_auto void nth_of_map<t, k> (fixpoint (t, k) f, list<t> l, int i);
requires 0<=i && i<length(l);
ensures nth(i, map(f, l)) == f(nth(i, l));
@*/
static PyObject * 
List_extraction(PyObject *self, PyObject *args)
/*@

requires PyExc(none, none) &*&
pyobj_hasval(args, PyTuple_v(cons(pair(?l__ptr, PyList_t(PyLong_t)), cons(pair(?i__ptr, PyLong_t), nil)))) &*&
pyobj_hasval(l__ptr, PyList_v(PyLong_t)) &*&
pyobj_hasval(i__ptr, PyLong_v(?i__val)) &*&
pyobj_hascontent(l__ptr, List(?l__content__ptr)) &*&
list_forallpred(?l__content, pyobj_hasPyLongval, True, nil) &*&
(map(fst, l__content) == l__content__ptr) &*&
(some(map(snd, l__content)) == some(?l__content__val)) &*&
(length(l__content__val) > i__val) &*&
(i__val >= 0) &*&
(length(l__content__val) <= 100);
@*/
/*@
ensures PyExc(none, none) &*&
pyobj_hasval(args, PyTuple_v(cons(pair(l__ptr, PyList_t(PyLong_t)), cons(pair(i__ptr, PyLong_t), nil)))) &*&
pyobj_hasval(l__ptr, PyList_v(PyLong_t)) &*&
pyobj_hasval(i__ptr, PyLong_v(i__val)) &*&
pyobj_hasval(result, PyLong_v(?result__val)) &*&
pyobj_hascontent(l__ptr, List(?NEW_l__content__ptr)) &*&
list_forallpred(?NEW_l__content, pyobj_hasPyLongval, True, nil) &*&
(map(fst, NEW_l__content) == NEW_l__content__ptr) &*&
(some(map(snd, NEW_l__content)) == some(?NEW_l__content__val)) &*&
(length(NEW_l__content__val) == length(l__content__val)) &*&
forall_(int j__val; (((j__val >= 0) && (j__val < length(NEW_l__content__val))) ? (nth(j__val, NEW_l__content__ptr) == nth(j__val, l__content__ptr)) : true)) &*&
(result == nth(i__val, l__content__ptr));
@*/{
    PyObject * l = PyTuple_GetItem(args, 0);
    PyObject * i = PyTuple_GetItem(args, 1);
    int i_val = PyLong_AsInt(i);
    PyObject * l_i = PyList_GetItem(l, i_val);
    //@ list_forallpred_extract(l__content, pyobj_hasPyLongval, i_val);
    //@ open pyobj_hasPyLongval(l_i, ?l_i_val);
    Py_INCREF(l_i);
    //@ close pyobj_hasPyLongval(l_i, l_i_val);
    //@ list_forallpred_insert(l__content, pyobj_hasPyLongval, i_val);
    //@ assert list_forallpred(l__content, pyobj_hasPyLongval, True, nil);
    return l_i;
}