#ifndef VF_PY_TUPLE_METH_H
#define VF_PY_TUPLE_METH_H
#include "defs/Cdefs.c"
#include "defs/vfdefs/VFdefs.c"

// Ghost operations for temporarily borrowing references from a tuple.
// borrowRefs consumes the tuple's own reference and produces a borrowed
// reference to each element (as a bigstar over the element pointers).
// returnRefs reassembles those borrowed references and gives back the tuple
// reference. This guarantees the borrowed element references are only usable
// while the tuple itself is kept alive.
void borrowRefs(PyObject *t);
//@ requires pyobj_hasval(t, PyTuple_v(?vls)) &*& hasRef(t, ?o);
//@ ensures  pyobj_hasval(t, PyTuple_v(vls)) &*& borrowedTupleRefs(t, vls, o) &*& bigstar(hasBorrowedRef(), map(fst, vls));

void returnRefs(PyObject *t);
//@ requires pyobj_hasval(t, PyTuple_v(?vls)) &*& borrowedTupleRefs(t, vls, ?o) &*& bigstar(hasBorrowedRef(), map(fst, vls));
//@ ensures  pyobj_hasval(t, PyTuple_v(vls)) &*& hasRef(t, o);

int PyTuple_Check(PyObject *p);
//@ requires hasRef(p, ?o) &*& pyobj_hasval(p, ?v);
/*@ ensures hasRef(p, o) &*& pyobj_hasval(p, v) &*& result == switch(v) {
    case PyTuple_v(x): return true;
    default: return false;
}; @*/
int PyTuple_CheckExact(PyObject *p);
//@ requires hasRef(p, ?o) &*& pyobj_hasval(p, ?v);
/*@ ensures hasRef(p, o) &*& pyobj_hasval(p, v) &*& result == switch(v) {
    case PyTuple_v(x): return true;
    default: return false;
}; @*/

PyObject * PyTuple_New(Py_ssize_t len);
/*@
predicate PyObjPtr_of_vararg(vararg va; PyObject* x) =
    switch(va) {
    case vararg_int(size, v):  return false &*& x == NULL;
    case vararg_uint(size, y): return false &*& x == NULL;
    case vararg_pointer(p):  return x==p;
    case vararg_double(p):  return false &*& x == NULL;
    };

predicate PyObjPtrs_of_varargs(list<vararg> va; list<PyObject*> out) =
    switch(va) {
    case nil: return out == {};
    case cons(x,xs):
        return  PyObjPtr_of_vararg(x,?o) &*& PyObjPtrs_of_varargs(xs,?rest)
            &*& out == cons(o,rest);
    };
@*/
PyObject *PyTuple_Pack(Py_ssize_t n, ...);
/*@ requires PyExc(?exc_old, ?t_old) &*&
    PyObjPtrs_of_varargs(?va,?ptrlst)
    &*& length(ptrlst) == n &*& 
    map_pyobj_hasval(ptrlst, ?pyobjv_lst);
    @*/
/*@ ensures 
    PyExc(?exc_new, ?t_new) &*& 
    PyObjPtrs_of_varargs(va, ptrlst)
    &*& map_pyobj_hasval(ptrlst, pyobjv_lst)
    &*& pyobj_hasval(result, PyTuple_v(?tuple_lst))
    &*& exc_new == exc_old ?
    (t_new==t_old &*& hasRef(result, true) &*& map_pyobj_hasval(ptrlst, pyobjv_lst) &*& map(fst, tuple_lst) == ptrlst &*& map(pyobj_typeof, pyobjv_lst) == map(snd, tuple_lst)):
    (result == NULL &*& t_new==some(MemoryError));
    @*/
Py_ssize_t PyTuple_Size(PyObject *p);
//@ requires hasRef(p, ?o) &*& pyobj_hasval(p, PyTuple_v(?lst));
//@ ensures hasRef(p, o) &*& pyobj_hasval(p, PyTuple_v(lst)) &*& result == length(lst);
Py_ssize_t PyTuple_GET_SIZE(PyObject *p);
//@ requires hasRef(p, ?o) &*& pyobj_hasval(p, PyTuple_v(?lst));
//@ ensures hasRef(p, o) &*& pyobj_hasval(p, PyTuple_v(lst)) &*& result == length(lst);
// Returns a borrowed reference: the caller gets the element pointer but no
// hasRef for it. To actually use the element, borrow its reference from the
// tuple via borrowRefs.
PyObject * PyTuple_GetItem(PyObject *p, Py_ssize_t pos);
//@ requires hasRef(p, ?o) &*& pyobj_hasval(p, PyTuple_v(?lst)) &*& 0 <= pos &*& pos < length(lst);
//@ ensures hasRef(p, o) &*& pyobj_hasval(p, PyTuple_v(lst)) &*& result==fst(nth(pos, lst));
PyObject * PyTuple_GET_ITEM(PyObject *p, Py_ssize_t pos);
//@ requires hasRef(p, ?o) &*& pyobj_hasval(p, PyTuple_v(?lst)) &*& 0 <= pos &*& pos < length(lst) &*& pyobj_hasval(fst(nth(pos, lst)), ?v);
//@ ensures hasRef(p, o) &*& pyobj_hasval(p, PyTuple_v(lst)) &*& result==fst(nth(pos, lst)) &*& pyobj_hasval(result, v) &*& pyobj_hasval(result, v) &*& pyobj_typeof(v) == snd(nth(pos, lst));
PyObject * PyTuple_GetSlice(PyObject *p, Py_ssize_t low, Py_ssize_t high);
/*@ requires hasRef(p, ?o) &*& pyobj_hasval(p, PyTuple_v(?lst)) &*& 0 <= low &*& low <= high &*& high <= length(lst) &*&
    map_pyobj_hasval(map(fst, lst), ?v) &*& map(pyobj_typeof, v) == map(snd, lst);
@*/
/*@ ensures hasRef(p, o) &*& pyobj_hasval(p, PyTuple_v(lst)) &*& hasRef(result, true) &*& pyobj_hasval(result, PyTuple_v(slice(lst, low, high))) &*&
    map_pyobj_hasval(map(fst, slice(lst, low, high)), ?v2) &*& v2 == slice(v, low, high);
@*/
int PyTuple_SetItem(PyObject *p, Py_ssize_t pos, PyObject *o);
//@ requires false;
//@ ensures false; 
void PyTuple_SET_ITEM(PyObject *p, Py_ssize_t pos, PyObject *o);
//@ requires false;
//@ ensures false;
int _PyTuple_Resize(PyObject **p, Py_ssize_t newsize);
//@ requires false;
//@ ensures false;
#endif