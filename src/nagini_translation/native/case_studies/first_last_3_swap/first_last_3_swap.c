#ifdef COMPILING FOR PYTHON
//#include <Python.h>
#else
#include "../../PythonAPI/vfpy.c"
#endif
/*@
fixpoint PyClass PyClass_ObjectType(){
    return ObjectType;
}
fixpoint PyClass PyClass_module_0A(){
    return PyClass("module_0A", PyClass_ObjectType, nil);
}
@*/
/*--END OF ENV--*/
/*@
lemma_auto void nth_of_map<t, k> (fixpoint (t, k) f, list<t> l, int i);
requires 0<=i && i<length(l);
ensures nth(i, map(f, l)) == f(nth(i, l));
@*/
static PyObject *
first_last_swap(PyObject *self, PyObject *args)
/*@
requires PyExc(none, none) &*&
gil_lock(?gstate) &*&
hasRef(args, false) &*&
pyobj_hasval(args, PyTuple_v(cons(pair(?n__ptr, PyClass_t(PyClass_module_0A())), cons(pair(?l__ptr, PyList_t(PyLong_t)), nil)))) &*&
pyobj_hasval(n__ptr, PyClassInstance_v(PyClass_module_0A())) &*&
pyobj_hasval(l__ptr, PyList_v(PyLong_t)) &*&
[1/2]pyobj_hasattr(n__ptr, "y", ?n_DOT_y__ptr) &*&
[1/2]pyobj_hasval(n_DOT_y__ptr, PyLong_v(?n_DOT_y__val)) &*&
pyobj_hasattr(n__ptr, "x", ?n_DOT_x__ptr) &*&
pyobj_hasval(n_DOT_x__ptr, PyLong_v(?n_DOT_x__val)) &*&
pyobj_hascontent(l__ptr, List(?l__content__ptr)) &*&
list_forallpred(?l__content, pyobj_hasPyLongval, True, nil) &*&
(map(fst, l__content) == l__content__ptr) &*&
(some(map(snd, l__content)) == some(?l__content__val)) &*&
(length(l__content__val) > 0);
@*/
/*@
ensures PyExc(none, none) &*&
gil_lock(gstate) &*&
hasRef(args, false) &*&
hasRef(result, true) &*&
pyobj_hasval(args, PyTuple_v(cons(pair(n__ptr, PyClass_t(PyClass_module_0A())), cons(pair(l__ptr, PyList_t(PyLong_t)), nil)))) &*&
pyobj_hasval(n__ptr, PyClassInstance_v(PyClass_module_0A())) &*&
pyobj_hasval(l__ptr, PyList_v(PyLong_t)) &*&
pyobj_hasval(result, PyLong_v(?result__val)) &*&
[1/2]pyobj_hasattr(n__ptr, "y", ?NEW_n_DOT_y__ptr) &*&
[1/2]pyobj_hasval(NEW_n_DOT_y__ptr, PyLong_v(?NEW_n_DOT_y__val)) &*&
pyobj_hasattr(n__ptr, "x", ?NEW_n_DOT_x__ptr) &*&
pyobj_hasval(NEW_n_DOT_x__ptr, PyLong_v(?NEW_n_DOT_x__val)) &*&
pyobj_hascontent(l__ptr, List(?NEW_l__content__ptr)) &*&
list_forallpred(?NEW_l__content, pyobj_hasPyLongval, True, nil) &*&
(map(fst, NEW_l__content) == NEW_l__content__ptr) &*&
(some(map(snd, NEW_l__content)) == some(?NEW_l__content__val)) &*&
(length(NEW_l__content__val) == length(l__content__val)) &*&
forall_(int i__val; (((i__val >= 0) && (i__val < (length(NEW_l__content__val) - 1))) ? (nth(i__val, NEW_l__content__ptr) == nth(i__val, l__content__ptr)) : true)) &*&
(nth((length(NEW_l__content__val) - 1), NEW_l__content__ptr) == n_DOT_y__ptr) &*&
(NEW_n_DOT_x__ptr == nth((length(l__content__val) - 1), l__content__ptr)) &*&
(result__val == length(NEW_l__content__val));
@*/
{
    PyObject * n = PyTuple_GetItem(args, 0);
    PyObject * l = PyTuple_GetItem(args, 1);

    // Borrow references to the two arguments so we can use them.
    borrowRefs(args);
    //@ bigstar_extract(hasBorrowedRef(), n__ptr);
    //@ open hasBorrowedRef()(n__ptr);
    //@ bigstar_extract(hasBorrowedRef(), l__ptr);
    //@ open hasBorrowedRef()(l__ptr);

    // Read n.y (only 1/2 permission, read-only): a new owned reference to it.
    const char * y_name = "y";
    PyObject * n_DOT_y = PyObject_GetAttrString(n, y_name);
    while (n_DOT_y == NULL)
/*@
    invariant PyExc(?e_ptr, ?t_ptr) &*&
    hasRef(n, false) &*&
    pyobj_hasval(n__ptr, PyClassInstance_v(PyClass_module_0A())) &*&
    [_]string(y_name, "y") &*&
    [1/2]pyobj_hasattr(n__ptr, "y", n_DOT_y__ptr) &*&
    [1/2]pyobj_hasval(n_DOT_y__ptr, PyLong_v(n_DOT_y__val)) &*&
    (n_DOT_y == NULL)?
        (e_ptr==some(_) &*& t_ptr==some(_)):
        (hasRef(n_DOT_y, true) &*& n_DOT_y == n_DOT_y__ptr);
@*/
    {
        n_DOT_y = PyObject_GetAttrString(n, y_name);
    }
    PyErr_Clear();

    ssize_t len = PyList_Size(l);

    // New owned reference to the old last element.
    PyObject * l_last = PyList_GetItemRef(l, len - 1);

    // Take the old last element's value out of the list (we'll store it in n.x).
    //@ list_forallpred_extract(l__content, pyobj_hasPyLongval, len - 1);
    //@ open pyobj_hasPyLongval(l_last, ?l_last_val);

    // We need a full value copy of n.y to (a) hand to SET_ITEM and (b) put into
    // the list's forallpred; the 1/2 we hold is enough since values are pure.
    //@ pyobj_hasval_dup(n_DOT_y);

    // l[last] = n.y (raw store, steals n_DOT_y; pointer level only).
    PyList_SET_ITEM(l, len - 1, n_DOT_y);

    // Re-establish the list's value invariant: slot len-1 now holds n_DOT_y.
    //@ close pyobj_hasPyLongval(n_DOT_y, n_DOT_y__val);
    //@ list_forallpred_replace(l__content, pyobj_hasPyLongval, len - 1, n_DOT_y, n_DOT_y__val);

    // n.x = old last element (full permission, so this write is allowed).
    const char * x_name = "x";
    int rc = PyObject_SetAttrString(n, x_name, l_last);
    while (rc == -1)
/*@
    invariant PyExc(?e_ptr2, ?t_ptr2) &*&
    pyobj_hasattr(n__ptr, "x", ?cur_x) &*&
    (rc == -1)?
        (cur_x == n_DOT_x__ptr):
        (cur_x == l_last &*& e_ptr2 == none &*& t_ptr2 == none);
@*/
    {
        PyErr_Clear();
    }
    PyErr_Clear();

    // Release our leftover owned reference to the old last element (n.x now
    // holds its own reference to it).
    Py_DECREF(l_last);

    // result = len
    PyObject * r = PyLong_FromSsize_t(len);
    while (r == NULL)
/*@
    invariant PyExc(?e_ptr3, ?t_ptr3) &*&
    (r == NULL)?
        (e_ptr3 == some(_) &*& t_ptr3 == some(_)):
        (hasRef(r, true) &*& pyobj_hasval(r, PyLong_v(len)));
@*/
    {
        r = PyLong_FromSsize_t(len);
    }
    PyErr_Clear();

    // The old n.x value is now stale knowledge we no longer need.
    //@ pyobj_hasval_drop(n_DOT_x__ptr);

    // Relate the updated list's pointer list to its content for the postcondition.
    //@ map_fst_update(len - 1, pair(n_DOT_y, n_DOT_y__val), l__content);

    // Return the borrowed argument references.
    //@ close hasBorrowedRef()(l__ptr);
    //@ bigstar_inject(hasBorrowedRef(), l__ptr);
    //@ close hasBorrowedRef()(n__ptr);
    //@ bigstar_inject(hasBorrowedRef(), n__ptr);
    returnRefs(args);

    return r;
}
