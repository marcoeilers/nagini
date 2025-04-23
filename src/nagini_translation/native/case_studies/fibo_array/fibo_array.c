#ifdef COMPILING FOR PYTHON
#include <Python.h>
#else
#include "../vfpy/PythonAPI/vfpy.c"
#endif
/*@
fixpoint PyClass PyClass_ObjectType(){
    return ObjectType;
}
fixpoint int PURE_fibo(int VALUEONLY_n__val){
     return ((VALUEONLY_n__val == 0) ? 1 : ((VALUEONLY_n__val == 1) ? 1 : ((VALUEONLY_n__val < 0) ? 1 : (PURE_fibo((VALUEONLY_n__val - 1)) + PURE_fibo((VALUEONLY_n__val - 2))))));
}
@*/
static PyObject * 
GMPy_MPZ_Function_Bincoef(PyObject *self, PyObject *args)
/*@
requires PyExc(none, none) &*&
pyobj_hasval(args, PyTuple_v(cons(pair(?n__ptr, PyLong_t), cons(pair(?l__ptr, PyList_t(PyLong_t)), nil)))) &*&
pyobj_hasval(n__ptr, PyLong_v(?n__val)) &*&
pyobj_hasval(l__ptr, PyList_v(PyLong_t)) &*&
(n__val >= 0);
@*/
/*@
ensures PyExc(none, none) &*&
pyobj_hasval(args, PyTuple_v(cons(pair(n__ptr, PyLong_t), cons(pair(l__ptr, PyList_t(PyLong_t)), nil)))) &*&
pyobj_hasval(n__ptr, PyLong_v(n__val)) &*&
pyobj_hasval(l__ptr, PyList_v(PyLong_t)) &*&
pyobj_hasval(result, PyNone_v) &*&
pyobj_hascontent(l__ptr, List(?NEW_l__content__ptr)) &*&
list_forallpred(?NEW_l__content, pyobj_hasPyLongval, True, nil) &*&
(map(fst, NEW_l__content) == NEW_l__content__ptr) &*&
(some(map(snd, NEW_l__content)) == some(?NEW_l__content__val)) &*&
forall_(int i__val; (((i__val >= 0) && (i__val < length(NEW_l__content__val))) ? (nth(i__val, NEW_l__content__val) == PURE_fibo(i__val)) : true));
@*/
{}