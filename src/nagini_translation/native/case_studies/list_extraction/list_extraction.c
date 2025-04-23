
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
Attr_extraction(PyObject *self, PyObject *args)
/*@
requires PyExc(none, none) &*&
pyobj_hasval(args, PyTuple_v(cons(pair(?l__ptr, PyList_t(PyLong_t)), nil))) &*&
pyobj_hasval(l__ptr, PyList_v(PyLong_t)) &*&
pyobj_hascontent(l__ptr, List(?l__content__ptr)) &*&
list_forallpred(?l__content, pyobj_hasPyLongval, True, nil) &*&
(map(fst, l__content) == l__content__ptr) &*&
(some(map(snd, l__content)) == some(?l__content__val)) &*&
(length(l__content__val) > 0);
@*/
/*@
ensures PyExc(none, none) &*&
pyobj_hasval(args, PyTuple_v(cons(pair(l__ptr, PyList_t(PyLong_t)), nil))) &*&
pyobj_hasval(l__ptr, PyList_v(PyLong_t)) &*&
pyobj_hasval(result, PyLong_v(?result__val)) &*&
pyobj_hascontent(l__ptr, List(?NEW_l__content__ptr)) &*&
list_forallpred(?NEW_l__content, pyobj_hasPyLongval, True, nil) &*&
(map(fst, NEW_l__content) == NEW_l__content__ptr) &*&
(some(map(snd, NEW_l__content)) == some(?NEW_l__content__val)) &*&
(length(NEW_l__content__val) == length(l__content__val)) &*&
forall_(int i__val; (((i__val > 0) && (i__val < (length(NEW_l__content__val) - 1))) ? (nth(i__val, NEW_l__content__ptr) == nth(i__val, l__content__ptr)) : true)) &*&
(nth((length(NEW_l__content__val) - 1), NEW_l__content__ptr) == nth(0, l__content__ptr)) &*&
(nth(0, NEW_l__content__ptr) == nth((length(l__content__val) - 1), l__content__ptr)) &*&
(result__val == ((length(NEW_l__content__val) == 1) ? 1 : 0));
@*/{
    
}