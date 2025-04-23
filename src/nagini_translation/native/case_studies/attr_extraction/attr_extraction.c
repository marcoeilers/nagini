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
/*--END OF ENV--*/
static PyObject * 
Attr_extraction(PyObject *self, PyObject *args)/*@
requires PyExc(none, none) &*&
pyobj_hasval(args, PyTuple_v(cons(pair(?n__ptr, PyClass_t(PyClass_module_0A())), cons(pair(?i__ptr, PyLong_t), nil)))) &*&
pyobj_hasval(n__ptr, PyClassInstance_v(PyClass_module_0A())) &*&
pyobj_hasval(i__ptr, PyLong_v(?i__val)) &*&
pyobj_hasattr(n__ptr, "y", ?n_DOT_y__ptr) &*&
pyobj_hasval(n_DOT_y__ptr, PyLong_v(?n_DOT_y__val));
@*/
/*@
ensures PyExc(none, none) &*&
pyobj_hasval(args, PyTuple_v(cons(pair(n__ptr, PyClass_t(PyClass_module_0A())), cons(pair(i__ptr, PyLong_t), nil)))) &*&
pyobj_hasval(n__ptr, PyClassInstance_v(PyClass_module_0A())) &*&
pyobj_hasval(i__ptr, PyLong_v(i__val)) &*&
pyobj_hasval(result, PyLong_v(?result__val)) &*&
pyobj_hasattr(n__ptr, "y", ?NEW_n_DOT_y__ptr) &*&
pyobj_hasval(NEW_n_DOT_y__ptr, PyLong_v(?NEW_n_DOT_y__val)) &*&
(NEW_n_DOT_y__ptr == i__ptr) &*&
(result == n_DOT_y__ptr);
@*/{
    PyObject * n = PyTuple_GetItem(args, 0);
    PyObject * i = PyTuple_GetItem(args, 1);
    const char * attr_name = "y";
    //@assert [?f]string(attr_name, "y");
    //@assert pyobj_hasval(n, _);
    //@assert PyExc(none, none);
    PyObject * n_DOT_y = PyObject_GetAttrString(n, attr_name);
    //@assert n_DOT_y == NULL?PyExc(some(_), some(_)):PyExc(none, none);
    while(n_DOT_y == NULL)
/*@invariant
    PyExc(?e_ptr, ?t_ptr) &*&
    pyobj_hasval(args, PyTuple_v(cons(pair(n__ptr, PyClass_t(PyClass_module_0A())), cons(pair(i__ptr, PyLong_t), nil)))) &*&
    pyobj_hasval(n__ptr, PyClassInstance_v(PyClass_module_0A())) &*&
    pyobj_hasval(i__ptr, PyLong_v(i__val)) &*&
    pyobj_hasattr(n__ptr, "y", n_DOT_y__ptr) &*&
    pyobj_hasval(n_DOT_y__ptr, PyLong_v(n_DOT_y__val)) &*&
    [f]string(attr_name, "y") &*&
    (n_DOT_y == NULL)?
        (e_ptr==some(_) &*& t_ptr==some(_)):
        (pyobj_hasval(n_DOT_y__ptr, PyLong_v(n_DOT_y__val))&*& n_DOT_y__ptr == n_DOT_y);
@*/
    {
        n_DOT_y = PyObject_GetAttrString(n, attr_name);
    }
    PyErr_Clear();
    int r = PyObject_SetAttrString(n, attr_name, i);
    while(r == -1)
/*@invariant
    PyExc(?e_ptr_2, ?t_ptr_2) &*&
    pyobj_hasval(args, PyTuple_v(cons(pair(n__ptr, PyClass_t(PyClass_module_0A())), cons(pair(i__ptr, PyLong_t), nil)))) &*&
    pyobj_hasval(n__ptr, PyClassInstance_v(PyClass_module_0A())) &*&
    pyobj_hasval(i__ptr, PyLong_v(i__val)) &*&
    pyobj_hasattr(n__ptr, "y", ?new_n_DOT_y__ptr) &*&
    pyobj_hasval(new_n_DOT_y__ptr, PyLong_v(?new_n_DOT_y__val)) &*&
    (r == -1)?
        (new_n_DOT_y__ptr == n_DOT_y__ptr):
        (new_n_DOT_y__ptr == i &*& e_ptr_2 == none &*& t_ptr_2 == none);
@*/
    {
        PyErr_Clear();
    }
    return n_DOT_y;
}

