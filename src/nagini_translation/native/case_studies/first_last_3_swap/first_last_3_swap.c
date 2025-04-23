#ifdef COMPILING FOR PYTHON
//#include <Python.h>
#else
#include "../vfpy/PythonAPI/vfpy.c"
#endif
/*@
fixpoint PyClass PyClass_ObjectType(){
    return ObjectType;
}
fixpoint PyClass PyClass_module_0A(){
    return PyClass("module_0A", PyClass_ObjectType, nil);
}
@*/
/*@
lemma_auto void nth_of_map<t, k> (fixpoint (t, k) f, list<t> l, int i);
requires 0<=i && i<length(l);
ensures nth(i, map(f, l)) == f(nth(i, l));
@*/
/*--END OF ENV--*/
static PyObject * 
GMPy_MPZ_Function_Bincoef(PyObject *self, PyObject *args)/*@
requires PyExc(none, none) &*&
pyobj_hasval(args, PyTuple_v(cons(pair(?n__ptr, PyClass_t(PyClass_module_0A())), cons(pair(?l__ptr, PyList_t(PyLong_t)), nil)))) &*&
pyobj_hasval(n__ptr, PyClassInstance_v(PyClass_module_0A())) &*&
pyobj_hasval(l__ptr, PyList_v(PyLong_t)) &*&
[1/2]pyobj_hasattr(n__ptr, "y", ?n_DOT_y__ptr) &*&
[1/2]pyobj_hasval(n_DOT_y__ptr, PyLong_v(?n_DOT_y__val)) &*&
pyobj_hascontent(l__ptr, List(?l__content__ptr)) &*&
list_forallpred(?l__content, pyobj_hasPyLongval, True, nil) &*&
(map(fst, l__content) == l__content__ptr) &*&
(some(map(snd, l__content)) == some(?l__content__val)) &*&
(length(l__content__val) > 0);
@*/
/*@
ensures PyExc(none, none) &*&
pyobj_hasval(args, PyTuple_v(cons(pair(n__ptr, PyClass_t(PyClass_module_0A())), cons(pair(l__ptr, PyList_t(PyLong_t)), nil)))) &*&
pyobj_hasval(n__ptr, PyClassInstance_v(PyClass_module_0A())) &*&
pyobj_hasval(l__ptr, PyList_v(PyLong_t)) &*&
pyobj_hasval(result, PyLong_v(?result__val)) &*&
[1/2]pyobj_hasattr(n__ptr, "y", ?NEW_n_DOT_y__ptr) &*&
[1/2]pyobj_hasval(NEW_n_DOT_y__ptr, PyLong_v(?NEW_n_DOT_y__val)) &*&
pyobj_hascontent(l__ptr, List(?NEW_l__content__ptr)) &*&
list_forallpred(?NEW_l__content, pyobj_hasPyLongval, True, nil) &*&
(map(fst, NEW_l__content) == NEW_l__content__ptr) &*&
(some(map(snd, NEW_l__content)) == some(?NEW_l__content__val)) &*&
(length(NEW_l__content__val) == length(l__content__val)) &*&
forall_(int i__val; (((i__val >= 0) && (i__val < (length(NEW_l__content__val) - 1))) ? (nth(i__val, NEW_l__content__ptr) == nth(i__val, l__content__ptr)) : true)) &*&
(nth((length(NEW_l__content__val) - 1), NEW_l__content__ptr) == n_DOT_y__ptr) &*&
(NEW_n_DOT_y__ptr == nth((length(l__content__val) - 1), l__content__ptr)) &*&
(result__val == length(NEW_l__content__val));
@*/{
    PyObject * n = PyTuple_GetItem(args, 0);
    PyObject * l = PyTuple_GetItem(args, 1);
    char * attr_name = "y";
    //@assert [?f]string(attr_name, "y");
    //@assert pyobj_hasval(n, _);
    //@assert PyExc(none, none);
    PyObject * n_DOT_y = PyObject_GetAttrString(n, attr_name);
    //@assert n_DOT_y == NULL?PyExc(some(_), some(_)):PyExc(none, none);
    //@assert l==l__ptr;
    while(n_DOT_y == NULL)
/*@
    invariant PyExc(?e_ptr, ?t_ptr) &*&
    pyobj_hasval(n__ptr, PyClassInstance_v(PyClass_module_0A())) &*&
    [f]string(attr_name, "y") &*&
    [1/2]pyobj_hasattr(n__ptr, "y", n_DOT_y__ptr) &*&
    [1/2]pyobj_hasval(n_DOT_y__ptr, PyLong_v(n_DOT_y__val)) &*&
    pyobj_hascontent(l__ptr, List(l__content__ptr)) &*&
    list_forallpred(l__content, pyobj_hasPyLongval, True, nil) &*&
    (n_DOT_y == NULL)?
        (e_ptr==some(_) &*& t_ptr==some(_)):
        (pyobj_hasval(n_DOT_y__ptr, PyLong_v(n_DOT_y__val))&*& n_DOT_y__ptr == n_DOT_y);
@*/
    {
        n_DOT_y = PyObject_GetAttrString(n, attr_name);
    }
    PyErr_Clear();
    ssize_t len=PyList_Size(l);
    //@list_forallpred_extract(l__content, pyobj_hasPyLongval, len-1);
    //@open pyobj_hasPyLongval(nth(len-1, map(fst, l__content)), _);
    PyObject * l_last = PyList_GetItem(l, len-1);
    Py_INCREF(l_last);
    PyObject *r = PyLong_FromSsize_t(len);
    PyList_SET_ITEM(l, len-1, n_DOT_y);
    //@close pyobj_hasPyLongval(nth(len-1, map(fst, l__content)), _);
    //@list_forallpred_insert(l__content, pyobj_hasPyLongval, len-1);

    //@list_forallpred_extract(l__content, pyobj_hasPyLongval, len-1);
    while (r == NULL) 
/*@
    invariant PyExc(?e_ptr2, ?t_ptr2) &*&
    (r == NULL)?
        e_ptr2==some(_) &*& t_ptr2==some(_):
        pyobj_hasval(r, PyLong_v(len));
@*/
    {
        r = PyLong_FromSsize_t(len);
    }
    PyErr_Clear();
    return r;
}

