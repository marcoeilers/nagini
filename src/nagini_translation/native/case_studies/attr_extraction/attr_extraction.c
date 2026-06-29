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
static PyObject *
replace_and_get(PyObject *self, PyObject *args)/*@
requires PyExc(none, none) &*&
gil_lock(?gstate) &*&
hasRef(args, false) &*&
pyobj_hasval(args, PyTuple_v(cons(pair(?n__ptr, PyClass_t(PyClass_module_0A())), cons(pair(?i__ptr, PyLong_t), nil)))) &*&
pyobj_hasval(n__ptr, PyClassInstance_v(PyClass_module_0A())) &*&
pyobj_hasval(i__ptr, PyLong_v(?i__val)) &*&
pyobj_hasattr(n__ptr, "y", ?n_DOT_y__ptr) &*&
pyobj_hasval(n_DOT_y__ptr, PyLong_v(?n_DOT_y__val));
@*/
/*@
ensures PyExc(none, none) &*&
gil_lock(gstate) &*&
hasRef(args, false) &*&
hasRef(result, true) &*&
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

    // The contract only hands us a borrowed reference to the args tuple. To use
    // the individual elements n and i we borrow their references from the tuple.
    borrowRefs(args);
    //@ bigstar_extract(hasBorrowedRef(), n);
    //@ open hasBorrowedRef()(n);
    //@ bigstar_extract(hasBorrowedRef(), i);
    //@ open hasBorrowedRef()(i);

    const char * attr_name = "y";
    PyObject * n_DOT_y = PyObject_GetAttrString(n, attr_name);
    while(n_DOT_y == NULL)
/*@invariant
    PyExc(?e_ptr, ?t_ptr) &*&
    hasRef(n, false) &*&
    pyobj_hasval(n__ptr, PyClassInstance_v(PyClass_module_0A())) &*&
    [_]string(attr_name, "y") &*&
    pyobj_hasattr(n__ptr, "y", n_DOT_y__ptr) &*&
    pyobj_hasval(n_DOT_y__ptr, PyLong_v(n_DOT_y__val)) &*&
    (n_DOT_y == NULL)?
        (e_ptr==some(_) &*& t_ptr==some(_)):
        (hasRef(n_DOT_y, true) &*& n_DOT_y == n_DOT_y__ptr);
@*/
    {
        n_DOT_y = PyObject_GetAttrString(n, attr_name);
    }

    PyErr_Clear();
    int r = PyObject_SetAttrString(n, attr_name, i);
    while(r == -1)
/*@invariant
    PyExc(?e_ptr_2, ?t_ptr_2) &*&
    pyobj_hasattr(n__ptr, "y", ?cur_attr) &*&
    (r == -1)?
        (cur_attr == n_DOT_y__ptr):
        (cur_attr == i__ptr &*& e_ptr_2 == none &*& t_ptr_2 == none);
@*/
    {
        PyErr_Clear();
    }

    // Return the borrowed element references to the tuple and recover the
    // tuple's own (borrowed) reference for the postcondition.
    //@ close hasBorrowedRef()(i);
    //@ bigstar_inject(hasBorrowedRef(), i);
    //@ close hasBorrowedRef()(n);
    //@ bigstar_inject(hasBorrowedRef(), n);
    returnRefs(args);

    // After the assignment n.y == i, so the new attribute value and the
    // argument i are the same object; the postcondition refers to its value
    // twice. pyobj_hasval is pure knowledge, so we duplicate it.
    //@ pyobj_hasval_dup(i);

    return n_DOT_y;
}
