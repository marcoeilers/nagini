#ifndef VF_PY_LIST_METH_H
#define VF_PY_LIST_METH_H
#include "defs/Cdefs.c"
#include "defs/vfdefs/VFdefs.c"
int PyList_Check(PyObject *p);
//@ requires hasRef(p, ?o) &*& pyobj_hasval(p, ?v);
/*@ ensures hasRef(p, o) &*& pyobj_hasval(p, v) &*& result == switch(v) {
    case PyList_v(x): return true;
    default: return false;
}; @*/
int PyList_CheckExact(PyObject *p);
//@ requires hasRef(p, ?o) &*& pyobj_hasval(p, ?v);
/*@ ensures hasRef(p, o) &*& pyobj_hasval(p, v) &*& result == switch(v) {
    case PyList_v(x): return true;
    default: return false;
}; @*/
PyObject *PyList_New(Py_ssize_t len);
//@ requires false;
//@ ensures false;
Py_ssize_t PyList_Size(PyObject *list);
//@ requires hasRef(list, ?o) &*& pyobj_hasval(list, PyList_v(?t)) &*& pyobj_hascontent(list, List(?c));
//@ ensures hasRef(list, o) &*& pyobj_hasval(list, PyList_v(t)) &*& pyobj_hascontent(list, List(c)) &*& result == length(c);
Py_ssize_t PyList_GET_SIZE(PyObject *list);
//@ requires hasRef(list, ?o) &*& pyobj_hasval(list, PyList_v(?t)) &*& pyobj_hascontent(list, List(?c));
//@ ensures hasRef(list, o) &*& pyobj_hasval(list, PyList_v(t)) &*& pyobj_hascontent(list, List(c)) &*& result == length(c);
PyObject *PyList_GetItem(PyObject *list, Py_ssize_t index);
//@ requires hasRef(list, ?o) &*& pyobj_hasval(list, PyList_v(?t)) &*& pyobj_hascontent(list, List(?c)) &*& 0 <= index &*& index < length(c);
//@ ensures hasRef(list, o) &*& pyobj_hasval(list, PyList_v(t)) &*& pyobj_hascontent(list, List(c)) &*& result == nth(index, c);
// Returns a NEW (strong) reference to the element, unlike the borrowed-reference
// PyList_GetItem above, hence hasRef(result, true).
PyObject *PyList_GetItemRef(PyObject *list, Py_ssize_t index);
//@ requires hasRef(list, ?o) &*& pyobj_hasval(list, PyList_v(?t)) &*& pyobj_hascontent(list, List(?c)) &*& 0 <= index &*& index < length(c);
//@ ensures hasRef(list, o) &*& pyobj_hasval(list, PyList_v(t)) &*& pyobj_hascontent(list, List(c)) &*& result == nth(index, c) &*& hasRef(result, true);
PyObject *PyList_GET_ITEM(PyObject *list, Py_ssize_t i);
//@ requires hasRef(list, ?o) &*& pyobj_hasval(list, PyList_v(?t)) &*& pyobj_hascontent(list, List(?c)) &*& 0 <= i &*& i < length(c);
//@ ensures hasRef(list, o) &*& pyobj_hasval(list, PyList_v(t)) &*& pyobj_hascontent(list, List(c)) &*& result == nth(i, c);
int PyList_SetItem(PyObject *list, Py_ssize_t index, PyObject *item);
/*@ requires hasRef(list, ?o) &*& hasRef(item, true) &*&
    pyobj_hasval(list, PyList_v(?t)) &*&
    pyobj_hascontent(list, List(?c)) &*&
    0 <= index &*& index < length(c) &*&
    list_forallpred(?pairlist, pyobj_hasval, True, ?out) &*&
    map(fst, pairlist) == c &*&
    forall_(int i; 0 > i || i > length(pairlist) || pyobj_typeof(snd(nth(i, pairlist)))==t) &*&
    pyobj_hasval(item, ?v) &*& isinstance(v, t) == true &*&
    mem(index, out) == false;
    @*/
/*@ ensures hasRef(list, o) &*& pyobj_hasval(list, PyList_v(t)) &*&
    pyobj_hascontent(list, List(update(index, item, c))) &*&
    list_forallpred(update(index, pair(item, v), pairlist), pyobj_hasval, True, out);
@*/
// PyList_SET_ITEM is the raw-store macro: it overwrites slot i with o (stealing
// o's reference) and does NOT touch the old element's reference count. We model
// only the pointer-level content here and leave the value/type invariant
// (list_forallpred) to the caller, who re-establishes it after the store. The
// [fo]pyobj_hasval(o, v) + isinstance check enforces that o matches the list's
// element type at the store point.
void PyList_SET_ITEM(PyObject *list, Py_ssize_t i, PyObject *o);
/*@ requires hasRef(list, ?lo) &*& hasRef(o, true) &*&
    pyobj_hasval(list, PyList_v(?t)) &*&
    pyobj_hascontent(list, List(?c)) &*&
    0 <= i &*& i< length(c) &*&
    [?fo]pyobj_hasval(o, ?v) &*& isinstance(v, t) == true ;
    @*/
/*@ ensures hasRef(list, lo) &*& pyobj_hasval(list, PyList_v(t)) &*&
    pyobj_hascontent(list, List(update(i, o, c))) &*&
    [fo]pyobj_hasval(o, v);
@*/
int PyList_Insert(PyObject *list, Py_ssize_t index, PyObject *item);
/*@
    requires hasRef(list, ?o) &*& hasRef(item, ?own_item) &*&
    PyExc(?e, ?type) &*&
    pyobj_hasval(list, PyList_v(?t)) &*&
    pyobj_hascontent(list, List(?c)) &*&
    0 <= index &*& index <= length(c) &*&
    list_forallpred(?pairlist, pyobj_hasval, True, ?out) &*&
    map(fst, pairlist) == c &*&
    forall_(int i; 0 > i || i > length(pairlist) || pyobj_typeof(snd(nth(i, pairlist)))==t) &*&
    pyobj_hasval(item, ?v) &*& isinstance(v, t) == true;
@*/
/*@
    ensures hasRef(list, o) &*& hasRef(item, own_item) &*&
    PyExc(?e_new, ?type_new) &*&
    (e_new == e)?
    (type_new==type &*&
    result==0 &*&
    pyobj_hasval(list, PyList_v(t)) &*&
    pyobj_hascontent(list, List(append(take(index, c), cons(item, drop(index, c))))) &*&
    list_forallpred(append(take(index, pairlist), cons(pair(item, v), drop(index, pairlist))), pyobj_hasval, True, out)):
    (type_new==some(MemoryError) &*& result == -1 &*&
    pyobj_hascontent(list, List(c)) &*&
    list_forallpred(pairlist, pyobj_hasval, True, out));
@*/
int PyList_Append(PyObject *list, PyObject *item);
/*@ requires hasRef(list, ?o) &*& hasRef(item, ?own_item) &*&
    PyExc(?e, ?type) &*&
    pyobj_hasval(list, PyList_v(?t)) &*&
    pyobj_hascontent(list, List(?c)) &*&
    list_forallpred(?pairlist, pyobj_hasval, True, ?out) &*&
    map(fst, pairlist) == c &*&
    forall_(int i; 0 > i || i > length(pairlist) || pyobj_typeof(snd(nth(i, pairlist)))==t) &*&
    pyobj_hasval(item, ?v) &*& isinstance(v, t) == true;
    @*/
/*@ ensures
    hasRef(list, o) &*& hasRef(item, own_item) &*&
    PyExc(?e_new, ?type_new) &*&
    (e_new == e)?
    (type_new==type &*&
    result==0 &*&
    pyobj_hasval(list, PyList_v(t)) &*&
    pyobj_hascontent(list, List(append(c, cons(item, nil)))) &*&
    list_forallpred(append(pairlist, cons(pair(item, v), nil)), pyobj_hasval, True, out)):
    (type_new==some(MemoryError) &*& result == -1 &*&
    pyobj_hascontent(list, List(c)) &*&
    list_forallpred(pairlist, pyobj_hasval, True, out));
@*/
PyObject *PyList_GetSlice(PyObject *list, Py_ssize_t low, Py_ssize_t high);
/*@ requires hasRef(list, ?o) &*&
    PyExc(?e, ?type) &*&
    pyobj_hasval(list, PyList_v(?t)) &*&
    pyobj_hascontent(list, List(?c)) &*&
    0 <= low &*& low <= high &*& high <= length(c) &*&
    list_forallpred(?pairlist, pyobj_hasval, True, ?out) &*&
    map(fst, pairlist) == c &*&
    forall_(int i; 0 > i || i > length(pairlist) || pyobj_typeof(snd(nth(i, pairlist)))==t);
    @*/
/*@ ensures
    hasRef(list, o) &*&
    PyExc(?e_new, ?type_new) &*&
    pyobj_hasval(list, PyList_v(t)) &*&
    pyobj_hascontent(list, List(c)) &*&
    list_forallpred(pairlist, pyobj_hasval, True, out) &*&
    map(fst, pairlist) == c &*&
    forall_(int i; 0 > i || i > length(pairlist) || pyobj_typeof(snd(nth(i, pairlist)))==t) &*&
    (e_new == e)?
    (type_new==type &*&
    result != NULL &*&
    hasRef(result, true) &*&
    pyobj_hasval(result, PyList_v(t)) &*&
    pyobj_hascontent(result, List(slice(c, low, high))) &*&
    list_forallpred(slice(pairlist, low, high), pyobj_hasval, True, out) &*&
    map(fst, slice(pairlist, low, high)) == slice(c, low, high) &*&
    forall_(int i; 0 > i || i > length(pairlist) || pyobj_typeof(snd(nth(i, pairlist)))==t)):
    (type_new==some(MemoryError) &*& result == NULL &*&
    pyobj_hascontent(list, List(c)) &*&
    list_forallpred(pairlist, pyobj_hasval, True, out));
@*/
    
int PyList_SetSlice(PyObject *list, Py_ssize_t low, Py_ssize_t high, PyObject *itemlist);
/*@ requires hasRef(list, ?o) &*& hasRef(itemlist, ?own_itemlist) &*&
    PyExc(?e, ?type) &*&
    pyobj_hasval(list, PyList_v(?t)) &*&
    pyobj_hascontent(list, List(?c)) &*&
    0 <= low &*& low <= high &*& high <= length(c) &*&
    list_forallpred(?pairlist, pyobj_hasval, True, ?out) &*&
    map(fst, pairlist) == c &*&
    forall_(int i; 0 > i || i > length(pairlist) || pyobj_typeof(snd(nth(i, pairlist)))==t) &*&
    pyobj_hasval(itemlist, PyList_v(?t2)) &*& issubtype(t2, t)==true &*&
    pyobj_hascontent(itemlist, List(?c2)) &*&
    length(c2) >= high - low &*&
    list_forallpred(?pairlist2, pyobj_hasval, True, ?out2) &*&
    map(fst, pairlist2) == c2 &*&
    forall_(int j; 0 > j || j > length(pairlist2) || pyobj_typeof(snd(nth(j, pairlist2)))==t2);
@*/
/*@ ensures
    hasRef(list, o) &*& hasRef(itemlist, own_itemlist) &*&
    PyExc(?e_new, ?type_new) &*&
    (e_new == e)?
    (type_new==type &*&
    result==0 &*&
    pyobj_hasval(list, PyList_v(t)) &*&
    pyobj_hascontent(list, List(append(take(low, c), append(c2, drop(high, c))))) &*&
    list_forallpred(append(take(low, pairlist), append(pairlist2, drop(high, pairlist))), pyobj_hasval, True, out)):
    (type_new==some(MemoryError) &*& result == -1 &*&
    pyobj_hascontent(list, List(c)) &*&
    list_forallpred(pairlist, pyobj_hasval, True, out)) &*&
    pyobj_hascontent(itemlist, List(c2)) &*&
    list_forallpred(pairlist2, pyobj_hasval, True, out2) &*&
    map(fst, pairlist2) == c2;
@*/
int PyList_Extend(PyObject *list, PyObject *iterable);
/*@ requires hasRef(list, ?o) &*& hasRef(iterable, ?own_iterable) &*&
    PyExc(?e, ?type) &*&
    pyobj_hasval(list, PyList_v(?t)) &*&
    pyobj_hascontent(list, List(?c)) &*&
    list_forallpred(?pairlist, pyobj_hasval, True, ?out) &*&
    map(fst, pairlist) == c &*&
    forall_(int i; 0 > i || i > length(pairlist) || pyobj_typeof(snd(nth(i, pairlist)))==t) &*&
    pyobj_hasval(iterable, PyList_v(?t2)) &*& issubtype(t2, t)==true &*&
    pyobj_hascontent(iterable, List(?c2)) &*&
    list_forallpred(?pairlist2, pyobj_hasval, True, ?out2) &*&
    map(fst, pairlist2) == c2 &*&
    forall_(int j; 0 > j || j > length(pairlist2) || pyobj_typeof(snd(nth(j, pairlist2)))==t2);
@*/
/*@ ensures
    hasRef(list, o) &*& hasRef(iterable, own_iterable) &*&
    PyExc(?e_new, ?type_new) &*&
    (e_new == e)?
    (type_new==type &*&
    result==0 &*&
    pyobj_hasval(list, PyList_v(t)) &*&
    pyobj_hascontent(list, List(append(c, c2))) &*&
    list_forallpred(append(pairlist, pairlist2), pyobj_hasval, True, out)):
    (type_new==some(MemoryError) &*& result == -1 &*&
    pyobj_hascontent(list, List(c)) &*&
    list_forallpred(pairlist, pyobj_hasval, True, out)) &*&
    pyobj_hascontent(iterable, List(c2)) &*&
    list_forallpred(pairlist2, pyobj_hasval, True, out2) &*&
    map(fst, pairlist2) == c2;
@*/
int PyList_Clear(PyObject *list);
/*@ requires hasRef(list, ?o) &*&
    PyExc(?e, ?type) &*&
    pyobj_hasval(list, PyList_v(?t)) &*&
    pyobj_hascontent(list, List(?c)) &*&
    list_forallpred(?pairlist, pyobj_hasval, True, ?out) &*&
    map(fst, pairlist) == c &*&
    forall_(int i; 0 > i || i > length(pairlist) || pyobj_typeof(snd(nth(i, pairlist)))==t);
    @*/
/*@ ensures
    hasRef(list, o) &*&
    PyExc(?e_new, ?type_new) &*&
    (e_new == e)?
    (type_new==type &*&
    result==0 &*&
    pyobj_hasval(list, PyList_v(t)) &*&
    pyobj_hascontent(list, List(nil)) &*&
    list_forallpred(nil, pyobj_hasval, True, out)):
    (type_new==some(MemoryError) &*& result == -1 &*&
    pyobj_hascontent(list, List(c)) &*&
    list_forallpred(pairlist, pyobj_hasval, True, out));
@*/
int PyList_Sort(PyObject *list);
//@ requires false;
//@ ensures false;
int PyList_Reverse(PyObject *list);
/*@ requires hasRef(list, ?o) &*&
    PyExc(?e, ?type) &*&
    pyobj_hasval(list, PyList_v(?t)) &*&
    pyobj_hascontent(list, List(?c)) &*&
    list_forallpred(?pairlist, pyobj_hasval, True, ?out) &*&
    map(fst, pairlist) == c &*&
    forall_(int i; 0 > i || i > length(pairlist) || pyobj_typeof(snd(nth(i, pairlist)))==t);
    @*/
/*@ ensures
    hasRef(list, o) &*&
    PyExc(?e_new, ?type_new) &*&
    (e_new == e)?
    (type_new==type &*&
    result==0 &*&
    pyobj_hasval(list, PyList_v(t)) &*&
    pyobj_hascontent(list, List(reverse(c)))) &*&
    list_forallpred(reverse(pairlist), pyobj_hasval, True, out):
    (type_new==some(MemoryError) &*& result == -1 &*&
    pyobj_hascontent(list, List(c)) &*&
    list_forallpred(pairlist, pyobj_hasval, True, out));
@*/
PyObject *PyList_AsTuple(PyObject *list); // recall that Tuples are supposed to be immutable
/*@ requires hasRef(list, ?o) &*&
    PyExc(?e, ?type) &*&
    pyobj_hasval(list, PyList_v(?t)) &*&
    pyobj_hascontent(list, List(?c)) &*&
    list_forallpred(?pairlist, pyobj_hasval, True, ?out) &*&
    map(fst, pairlist) == c &*&
    forall_(int i; 0 > i || i > length(pairlist) || pyobj_typeof(snd(nth(i, pairlist)))==t);
@*/
/*@ ensures hasRef(list, o) &*&
    PyExc(?e_new, ?type_new) &*&
    pyobj_hasval(list, PyList_v(t)) &*&
    pyobj_hascontent(list, List(c)) &*&
    list_forallpred(pairlist, pyobj_hasval, True, out) &*&
    map(fst, pairlist) == c &*&
    forall_(int i; 0 > i || i > length(pairlist) || pyobj_typeof(snd(nth(i, pairlist)))==t) &*&
    (e_new == e)?
    (type_new==type &*&
    result != NULL &*&
    hasRef(result, true) &*&
    pyobj_hasval(result, PyTuple_v(?t2)) &*&
    map(fst,t2)==map(fst, pairlist) &*&
    map_pyobj_hasval(map(fst,t2), map(snd, pairlist)) &*&
    forall_(int i; 0 > i || i > length(pairlist) || snd(nth(i, t2))==t)
    ):
    (type_new==some(MemoryError) &*& result == NULL);

@*/
#endif