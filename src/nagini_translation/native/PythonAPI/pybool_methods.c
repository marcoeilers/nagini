#ifndef VF_PY_BOOL_METHODS_H
#define VF_PY_BOOL_METHODS_H
#include "defs/Cdefs.c"
#include "defs/vfdefs/VFdefs.c"
/*@
@*/
int PyBool_Check(PyObject *o);
//@ requires hasRef(o, ?own_o) &*& pyobj_hasval(o, ?v);
//@ ensures hasRef(o, own_o) &*& pyobj_hasval(o, v) &*& pyobj_typeof(v) == PyBool_t;
PyObject *PyBool_FromLong(long v);
//@ requires PyExc(?e, ?t);
/*@ ensures PyExc(?e_new, ?t_new) &*&
        (e_new == e)?
        (t_new == t &*& pyobj_hasval(result, PyBool_v(v==0)) &*& hasRef(result, true) &*& result != NULL) :
        (t_new == some(MemoryError) &*& result == NULL);
@*/
#endif