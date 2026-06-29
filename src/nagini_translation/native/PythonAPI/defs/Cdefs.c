#ifndef C_PY_DEFS_H
#define C_PY_DEFS_H
#include <stddef.h>
#include <stdbool.h>
#include <unistd.h>
#include <math.h>
// TODO: redefine Py_ssize_t to support being signed
typedef ssize_t Py_ssize_t;
typedef int PyGILState_STATE;
typedef struct pyobjstruct
{
} PyObject;
// typedef struct pycomplexstruct PyComplex;
static PyObject _Py_NoneStruct;
#define Py_None (&_Py_NoneStruct)
#define Py_RETURN_TRUE return  Py_INCREF(Py_True), Py_True
#define Py_RETURN_FALSE return Py_INCREF(Py_False), Py_False
PyObject *Py_True;
PyObject *Py_False;
#define DBL_MIN 2.2250738585072014e-308
#define DBL_MAX 1.7976931348623157e+308
#define SSIZE_MAX 9223372036854775807
#define SSIZE_MIN -9223372036854775807
#define SIZE_MAX 18446744073709551615
#define SIZE_MIN 0
#endif