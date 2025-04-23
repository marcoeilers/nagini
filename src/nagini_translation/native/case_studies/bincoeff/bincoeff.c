/// inspired by GMPy_MPZ_Function_Bincoef
#ifdef COMPILING FOR PYTHON
#include <Python.h>
#include <gmp.h>
#else
#include "mpz_include.c"
#endif
static PyObject *
GMPy_MPZ_Function_Bincoef(PyObject *self, PyObject *const *args)
{
    unsigned long n, k;
    mpz_t x;     // Declare the variable (not a pointer!)
    mpz_init(x); // Initialize the variable
    k = PyLong_AsUnsignedLong(PyTuple_GET_ITEM(args, 1));
    if (k == (unsigned long)(-1) && PyErr_Occurred())
    {
        return NULL;
    }

    n = PyLong_AsUnsignedLong(PyTuple_GET_ITEM(args, 0));
    if (n == (unsigned long)(-1) && PyErr_Occurred())
    {
        return NULL;
    }
    mpz_bin_uiui(x, n, k);
    long res = mpz_get_ui(x);
    //todo check for overflow
    //if overflow, return NULL; and raise exception? no... unsupported...
    mpz_clear(x); // Clear the variable
    return PyLong_FromUnsignedLong(res);
}