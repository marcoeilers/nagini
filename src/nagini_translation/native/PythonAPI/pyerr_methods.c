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
#endif