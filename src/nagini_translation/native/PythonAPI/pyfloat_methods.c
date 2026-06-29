#ifndef VF_PY_FLOAT_METHODS_H
#define VF_PY_FLOAT_METHODS_H
#include "defs/Cdefs.c"
#include "defs/vfdefs/VFdefs.c"
#include <math.h>
//idea: use real type to model float and double values
//idea: this will give elements to be able to convert to other value types https://github.com/verifast/verifast/blob/master/bin/vf__floating_point.h
/*@
@*/
int PyFloat_Check(PyObject *o);
//@ requires hasRef(o, ?own_o) &*& pyobj_hasval(o, ?v);
//@ ensures hasRef(o, own_o) &*& pyobj_hasval(o, v) &*& pyobj_typeof(v) == PyFloat_t;
int PyFloat_CheckExact(PyObject *p);
//@ requires hasRef(p, ?own_p) &*& pyobj_hasval(p, ?v);
//@ ensures hasRef(p, own_p) &*& pyobj_hasval(p, v) &*& pyobj_typeof(v) == PyFloat_t;
PyObject *PyFloat_FromDouble(double v);
//@ requires PyExc(?e, ?t);
/*@ ensures PyExc(?e_new, ?t_new) &*&
        (e_new == e)?
        (t_new == t &*& pyobj_hasval(result, PyFloat_v(v)) &*& hasRef(result, true) &*& result != NULL) :
        (t_new == some(MemoryError) &*& result == NULL);
@*/

double PyFloat_AsDouble(PyObject *pyfloat);
//@ requires hasRef(pyfloat, ?own_pyfloat) &*& pyobj_hasval(pyfloat, PyFloat_v(?v));
//@ ensures hasRef(pyfloat, own_pyfloat) &*& pyobj_hasval(pyfloat, PyFloat_v(v)) &*& result == v;
double PyFloat_AS_DOUBLE(PyObject *pyfloat);
//@ requires hasRef(pyfloat, ?own_pyfloat) &*& pyobj_hasval(pyfloat, PyFloat_v(?v));
//@ ensures hasRef(pyfloat, own_pyfloat) &*& pyobj_hasval(pyfloat, PyFloat_v(v)) &*& result == v;
double PyFloat_GetMax();
//@ requires false;
//@ ensures DBL_MAX==equiv(result);
double PyFloat_GetMin();
//@ requires true;
//@ ensures equiv(result) == DBL_MIN;
//NOTE: in the following, le is a boolean value that indicates whether the byte order is little-endian
/*TODO: 
    for now, these methods are inaccurtely specified
    to specify their content correctly, we need a char-float conversion system.
    If this system is ever found to be implemented, try to complete the specs here.
*/
int PyFloat_Pack2(double x, unsigned char *p, int le);
//@ requires p[0..1] |-> ?p_val &*& false;
//@ ensures p[0..1] |-> p_val;
int PyFloat_Pack4(double x, unsigned char *p, int le);
//@ requires p[0..3] |-> ?p_val &*& false;
//@ ensures p[0..3] |-> p_val;
int PyFloat_Pack8(double x, unsigned char *p, int le);
//@ requires p[0..7] |-> ?p_val &*& false;
//@ ensures p[0..7] |-> p_val;
int PyFloat_Unpack2(const unsigned char *p, int le);
//@ requires p[0..1] |-> ?p_val &*& false;
//@ ensures p[0..1] |-> p_val;
int PyFloat_Unpack4(const unsigned char *p, int le);
//@ requires p[0..3] |-> ?p_val &*& false;
//@ ensures p[0..3] |-> p_val;
int PyFloat_Unpack8(const unsigned char *p, int le);
//@ requires p[0..7] |-> ?p_val &*& false;
//@ ensures p[0..7] |-> p_val;

#endif