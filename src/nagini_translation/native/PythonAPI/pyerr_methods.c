#ifndef VF_PY_ERR_METH_H
#define VF_PY_ERR_METH_H
#include "defs/Cdefs.c"
#include "defs/vfdefs/VFdefs.c"
void PyErr_Clear();
//@ requires PyExc(?ptr, ?type);
//@ ensures PyExc(none, none);
PyObject *PyErr_Occurred();
//@ requires PyExc(?ptr, ?type) &*& gil_lock(?gil);
/*@ ensures PyExc(ptr, type) &*& gil_lock(gil) &*&
    switch (ptr) {
        case none: return type == none &*& result == NULL;
        case some(x): return result !=NULL &*& type==some(?y) &*& some(result) == ptr;
    };
@*/

// Standard exception type singletons (borrowed, statically alive).
PyObject *PyExc_TypeError;
PyObject *PyExc_ValueError;

// Raises an exception of the given type with the given message, setting the
// global error indicator.
void PyErr_SetString(PyObject *type, const char *message);
//@ requires PyExc(?e, ?t) &*& [?f]string(message, ?m);
//@ ensures PyExc(some(_), some(_)) &*& [f]string(message, m);
#endif