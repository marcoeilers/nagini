#ifndef PyGILSTATE_H
#define PyGILSTATE_H
#include "defs/Cdefs.c"
#include "defs/vfdefs/VFdefs.c"
// Acquiring/releasing the GIL is forbidden under the current model: while the
// GIL is released another thread may run and deallocate objects we only hold
// borrowed references (hasRef(o, false)) to, which would make those borrowed
// references unsound. We therefore give these functions `requires false`.
PyGILState_STATE PyGILState_Ensure();
//@ requires false;
//@ ensures false;

void PyGILState_Release(PyGILState_STATE gstate);
//@ requires false;
//@ ensures false;

#endif