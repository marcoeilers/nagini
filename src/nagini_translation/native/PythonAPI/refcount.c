#ifndef VF_PY_REFCOUNT_H
#define VF_PY_REFCOUNT_H
#include "defs/vfdefs/VFdefs.c"
#include "defs/Cdefs.c"
// Incrementing the reference count produces a new owned reference. Holding any
// reference (owned or borrowed) proves the object is still alive, which is what
// lets us legitimately create another one.
void Py_INCREF(PyObject *obj);
//@ requires hasRef(obj, ?o);
//@ ensures  hasRef(obj, o) &*& hasRef(obj, true);
// Decrementing consumes one owned reference. It must not be called on a
// borrowed reference, hence the owned == true requirement.
void Py_DECREF(PyObject *obj);
//@ requires hasRef(obj, true);
//@ ensures  true;
#endif