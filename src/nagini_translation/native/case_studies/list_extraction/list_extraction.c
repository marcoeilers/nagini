#ifdef COMPILING FOR PYTHON
//#include <Python.h>
#else
#include "../../PythonAPI/vfpy.c"
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
list_extraction(PyObject *self, PyObject *args)
/*@
requires PyExc(none, none) &*&
gil_lock(?gstate) &*&
hasRef(args, false) &*&
pyobj_hasval(args, PyTuple_v(cons(pair(?l__ptr, PyList_t(PyLong_t)), cons(pair(?i__ptr, PyLong_t), nil)))) &*&
pyobj_hasval(l__ptr, PyList_v(PyLong_t)) &*&
pyobj_hasval(i__ptr, PyLong_v(?i__val)) &*&
pyobj_hascontent(l__ptr, List(?l__content__ptr)) &*&
list_forallpred(?l__content, pyobj_hasPyLongval, True, nil) &*&
(map(fst, l__content) == l__content__ptr) &*&
(some(map(snd, l__content)) == some(?l__content__val)) &*&
(((length(l__content__val) > i__val) && (i__val >= 0)) && (length(l__content__val) < 100));
@*/
/*@
ensures PyExc(none, none) &*&
gil_lock(gstate) &*&
hasRef(args, false) &*&
hasRef(result, true) &*&
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
@*/
{
    PyObject * l = PyTuple_GetItem(args, 0);
    PyObject * i = PyTuple_GetItem(args, 1);

    // Borrow references to the two arguments so we can read them.
    borrowRefs(args);
    //@ bigstar_extract(hasBorrowedRef(), l__ptr);
    //@ open hasBorrowedRef()(l__ptr);
    //@ bigstar_extract(hasBorrowedRef(), i__ptr);
    //@ open hasBorrowedRef()(i__ptr);

    int i_val = PyLong_AsInt(i);

    // PyList_GetItemRef returns a NEW reference to the element, so no manual
    // Py_INCREF / borrow machinery is needed: we directly own l_i.
    PyObject * l_i = PyList_GetItemRef(l, i_val);

    // Extract the element's value out of the list's forallpred (to satisfy the
    // postcondition's pyobj_hasval(result, ...)); duplicate it (pure knowledge)
    // and put one copy back so the list's forallpred is left intact.
    //@ list_forallpred_extract(l__content, pyobj_hasPyLongval, i_val);
    //@ open pyobj_hasPyLongval(l_i, ?l_i_val);
    //@ pyobj_hasval_dup(l_i);
    //@ close pyobj_hasPyLongval(l_i, l_i_val);
    //@ list_forallpred_insert(l__content, pyobj_hasPyLongval, i_val);

    // Return the borrowed argument references and recover hasRef(args).
    //@ close hasBorrowedRef()(i__ptr);
    //@ bigstar_inject(hasBorrowedRef(), i__ptr);
    //@ close hasBorrowedRef()(l__ptr);
    //@ bigstar_inject(hasBorrowedRef(), l__ptr);
    returnRefs(args);

    return l_i;
}
