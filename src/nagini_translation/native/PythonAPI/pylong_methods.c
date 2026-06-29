#ifndef VF_PY_LONG_METH_H
#define VF_PY_LONG_METH_H
#include "defs/Cdefs.c"
#include "defs/vfdefs/VFdefs.c"


int PyLong_Check(const PyObject *p);
//@ requires hasRef(p, ?o) &*& pyobj_hasval(p, ?pyobj_p);
/*@ ensures hasRef(p, o) &*& result == ( (pyobj_typeof(pyobj_p)==PyLong_t)? 1 : 0 ) &*& pyobj_hasval(p, pyobj_p); @*/
int PyLong_CheckExact(const PyObject *p);
//@ requires hasRef(p, ?o) &*& pyobj_hasval(p, ?pyobj_p);
/*@ ensures hasRef(p, o) &*& result == ( (pyobj_typeof(pyobj_p)==PyLong_t)? 1 : 0 ) &*& pyobj_hasval(p, pyobj_p); @*/

PyObject *PyLong_FromLong(long x);
//@ requires PyExc(?e_old, ?t_old);
/*@ ensures PyExc(?e_new, ?t_new) &*&
    ((result == NULL)?
        (e_new != e_old &*& t_new!=t_old &*& e_new == some(_) &*&
            t_new == some(?t_new_val) &*&
            (t_new_val == MemoryError || t_new_val == RuntimeError)):
        (e_new == e_old &*& t_new==t_old &*& pyobj_hasval(result, PyLong_v(x)) &*& hasRef(result, true)));
@*/

PyObject *PyLong_FromUnsignedLong(unsigned long x);
//@ requires PyExc(?e_old, ?t_old);
/*@ ensures PyExc(?e_new, ?t_new) &*&
    ((result == NULL)?
        (e_new != e_old &*& t_new!=t_old &*& e_new == some(_) &*&
            t_new == some(?t_new_val) &*&
            (t_new_val == MemoryError || t_new_val == RuntimeError)):
        (e_new == e_old &*& t_new==t_old &*& pyobj_hasval(result, PyLong_v(x)) &*& hasRef(result, true)));
@*/


PyObject *PyLong_FromSsize_t(Py_ssize_t v);
/*@ requires PyExc(?e_old, ?t_old); @*/
/*@ ensures PyExc(?e_new, ?t_new) &*&
    (result == NULL)?
        (e_new != e_old &*& t_new != t_old &*& e_new == some(_) &*&
            t_new == some(?e_new_val) &*&
            (e_new_val == MemoryError || e_new_val == RuntimeError)):
        (e_new == e_old &*& t_new == t_old &*& pyobj_hasval(result, PyLong_v(v)) &*& hasRef(result, true));
@*/
PyObject *PyLong_FromSize_t(size_t v);
/*@ requires PyExc(?e_old, ?t_old); @*/
/*@ ensures PyExc(?e_new, ?t_new) &*&
    (result == NULL)?
        (e_new != e_old &*& t_new != t_old &*& e_new == some(_) &*&
            t_new == some(?e_new_val) &*&
            (e_new_val == MemoryError || e_new_val == RuntimeError)):
        (e_new == e_old &*& t_new == t_old &*& pyobj_hasval(result, PyLong_v(v)) &*& hasRef(result, true));
@*/
PyObject *PyLong_FromLongLong(long long v);
/*@ requires PyExc(?e_old, ?t_old); @*/
/*@ ensures PyExc(?e_new, ?t_new) &*&
    (result == NULL)?
        (e_new != e_old &*& t_new != t_old &*& e_new == some(_) &*&
            t_new == some(?e_new_val) &*&
            (e_new_val == MemoryError || e_new_val == RuntimeError)):
        (e_new == e_old &*& t_new == t_old &*& pyobj_hasval(result, PyLong_v(v)) &*& hasRef(result, true));
@*/
PyObject *PyLong_FromUnsignedLongLong(unsigned long long v);
/*@ requires PyExc(?e_old, ?t_old); @*/
/*@ ensures PyExc(?e_new, ?t_new) &*&
    (result == NULL)?
        (e_new != e_old &*& t_new != t_old &*& e_new == some(_) &*&
            t_new == some(?e_new_val) &*&
            (e_new_val == MemoryError || e_new_val == RuntimeError)):
        (e_new == e_old &*& t_new == t_old &*& pyobj_hasval(result, PyLong_v(v)) &*& hasRef(result, true));
@*/
PyObject *PyLong_FromDouble(double v);
//@ requires false;
/*@ ensures false; @*/
//TODO: map  is_decimal_digit(str_c)==true on the string
PyObject *PyLong_FromString(const char *str, char **pend, int base);
//@ requires base == 10 &*& [?f]string(str, ?c) &*& forall_(int i; i<0 || i>=length(c) || is_decimal_digit(nth(i, c))==true) &*& *pend |->_ ;
//@ ensures pyobj_hasval(result, PyLong_v(int_of_decimal(c))) &*& [f]string(str, c) &*& *pend |->str+length(c) &*& hasRef(result, true);
PyObject *PyLong_FromUnicodeObject(PyObject *u, int base);
//@ requires hasRef(u, ?o) &*& base == 10 &*& pyobj_hasval(u, PyUnicode_v(?v)) &*& forall_(int i; i<0 || i>=length(v) || is_decimal_digit(nth(i, v))==true);
/*@ ensures hasRef(u, o) &*& pyobj_hasval(u, PyUnicode_v(v)) &*& pyobj_hasval(result, PyLong_v(int_of_decimal(v))) &*& result != NULL &*& hasRef(result, true); @*/
PyObject *PyLong_FromVoidPtr(void *p);
//@ requires false;
/*@ ensures false; @*/
PyObject *PyLong_FromNativeBytes(const void *buffer, size_t n_bytes, int flags);
/*@ requires PyExc(?e_old, ?t_old) &*& 
n_bytes >= 0 &*& ((char *)buffer)[0..n_bytes] |-> ?bytes; @*/
/*@ ensures PyExc(?e_new, ?t_new) &*& n_bytes >= 0 &*& ((char *)buffer)[0..n_bytes] |-> bytes &*&
    (result == NULL)?
        (e_new != e_old &*& t_new != t_old &*& e_new == some(_) &*&
            t_new == some(?t_new_val) &*&
            (t_new_val == MemoryError || t_new_val == RuntimeError)):
        (e_new == e_old &*& t_new == t_old &*& pyobj_hasval(result, PyLong_v(equiv<int, pair< list<char>,int > >(pair(bytes, flags)))) &*& hasRef(result, true));
            @*/
PyObject *PyLong_FromUnsignedNativeBytes(const void *buffer, size_t n_bytes, int flags);
/*@ requires PyExc(?e_old, ?t_old) &*& 
n_bytes >= 0 &*& ((char *)buffer)[0..n_bytes] |-> ?bytes &*& forall_(int i; i<0 || i>=length(bytes) || is_decimal_digit(nth(i, bytes))==true); @*/
/*@ ensures PyExc(?e_new, ?t_new) &*& ((char *)buffer)[0..n_bytes] |-> bytes &*&
    (result == NULL)?
        (e_new != e_old &*& t_new != t_old &*& e_new == some(_) &*&
            t_new == some(?t_new_val) &*&
            (t_new_val == MemoryError || t_new_val == RuntimeError)):
        (e_new == e_old &*& t_new == t_old &*& pyobj_hasval(result, PyLong_v(equiv<int, pair< list<char>,int > >(pair(bytes, flags)))) &*& hasRef(result, true));
            @*/
long PyLong_AsLong(PyObject *p);
/*@ requires hasRef(p, ?o) &*& pyobj_hasval(p, PyLong_v(?v))
    &*& v <= LONG_MAX &*& v >= LONG_MIN;@*/
/*@ ensures hasRef(p, o) &*& pyobj_hasval(p, PyLong_v(v))
    &*& result == v;@*/
int PyLong_AsInt(PyObject *p);
/*@ requires hasRef(p, ?o) &*& pyobj_hasval(p, PyLong_v(?v))
    &*& v <= INT_MAX &*& v >= INT_MIN;@*/
/*@ ensures hasRef(p, o) &*& pyobj_hasval(p, PyLong_v(v))
    &*& result == v;@*/
long PyLong_AsLongAndOverflow(PyObject *obj, int *overflow);
/*@
    requires hasRef(obj, ?o) &*& pyobj_hasval(obj, PyLong_v(?v)) &*& *overflow |-> _;@*/
/*@ ensures hasRef(obj, o) &*& pyobj_hasval(obj, PyLong_v(v))
    &*& result == (LONG_MIN & v)
    &*& *overflow |-> ?resOF &*& resOF == ((v > LONG_MAX) || (v < LONG_MIN));@*/

long long PyLong_AsLongLong(PyObject *p);
/*@ requires hasRef(p, ?o) &*& pyobj_hasval(p, PyLong_v(?v))
    &*& v <= LLONG_MAX &*& v >= LLONG_MIN;@*/
/*@ ensures hasRef(p, o) &*& pyobj_hasval(p, PyLong_v(v))
    &*& result == v;@*/

unsigned long PyLong_AsUnsignedLong(PyObject *p);
/*@
    requires hasRef(p, ?o) &*& pyobj_hasval(p, PyLong_v(?v))
    &*& v <= ULONG_MAX &*& v >= 0;@*/
/*@ ensures hasRef(p, o) &*& pyobj_hasval(p, PyLong_v(v))
    &*& result == v;
@*/
long long PyLong_AsLongLongAndOverflow(PyObject *obj, int *overflow);
/*@
    requires hasRef(obj, ?o) &*& pyobj_hasval(obj, PyLong_v(?v)) &*& *overflow |-> _;@*/
/*@ ensures hasRef(obj, o) &*& pyobj_hasval(obj, PyLong_v(v))
    &*& result == (LLONG_MIN & v)
    &*& *overflow |-> ?resOF &*& resOF == ((v > LLONG_MAX) || (v < LLONG_MIN));@*/
Py_ssize_t PyLong_AsSsize_t(PyObject *p);
/*@
    requires hasRef(p, ?o) &*& pyobj_hasval(p, PyLong_v(?v))
    &*& v <= SSIZE_MAX &*& v >= SSIZE_MIN;@*/
/*@ ensures hasRef(p, o) &*& pyobj_hasval(p, PyLong_v(v))
    &*& result == v;
@*/
    
size_t PyLong_AsSize_t(PyObject *pylong);
/*@
    requires hasRef(pylong, ?o) &*& pyobj_hasval(pylong, PyLong_v(?v))
    &*& v <= SIZE_MAX &*& v >= 0;@*/
/*@ ensures hasRef(pylong, o) &*& pyobj_hasval(pylong, PyLong_v(v))
    &*& result == v;
@*/

unsigned long long PyLong_AsUnsignedLongLong(PyObject *p);
/*@
    requires hasRef(p, ?o) &*& pyobj_hasval(p, PyLong_v(?v))
    &*& v <= ULLONG_MAX &*& v >= 0
    &*& PyExc(?exc_old, ?type_old);@*/
/*@ ensures hasRef(p, o) &*& pyobj_hasval(p, PyLong_v(v))
    &*& result == v
    &*& PyExc(exc_old, type_old);@*/
unsigned long PyLong_AsUnsignedLongMask(PyObject *obj);
//@ requires hasRef(obj, ?o) &*& pyobj_hasval(obj, PyLong_v(?v));
/*@ ensures hasRef(obj, o) &*& pyobj_hasval(obj, PyLong_v(v))
    &*& result == (v & ULONG_MAX);@*/
    
unsigned long long PyLong_AsUnsignedLongLongMask(PyObject *obj);
//@ requires hasRef(obj, ?o) &*& pyobj_hasval(obj, PyLong_v(?v));
/*@ ensures hasRef(obj, o) &*& pyobj_hasval(obj, PyLong_v(v))
    &*& result == (v & ULLONG_MAX);@*/
    
double PyLong_AsDouble(PyObject *pylong);
//@ requires false;
//@ ensures false;
void *PyLong_AsVoidPtr(PyObject *pylong);
//@ requires hasRef(pylong, ?o) &*& pyobj_hasval(pylong, PyLong_v(?v));
//@ ensures hasRef(pylong, o) &*& pyobj_hasval(pylong, PyLong_v(v)) &*& result == (void *)(v & SIZE_MAX);
Py_ssize_t PyLong_AsNativeBytes(PyObject *pylong, void *buffer, Py_ssize_t n_bytes, int flags);
/*@ requires hasRef(pylong, ?o) &*& pyobj_hasval(pylong, PyLong_v(?v))
    &*& ((char *)buffer)[0..n_bytes] |-> _
    &*& n_bytes >= 0; @*/
/*@ ensures hasRef(pylong, o) &*& pyobj_hasval(pylong, PyLong_v(v))
    &*& ((char *)buffer)[0..n_bytes] |-> ?bytes
    &*& equiv<int, pair< list<char>,int > >(pair(bytes, flags)) == (v & ((1<<result)-1)); @*/
    
PyObject *PyLong_GetInfo();
//@ requires false;
//@ ensures false;

#endif