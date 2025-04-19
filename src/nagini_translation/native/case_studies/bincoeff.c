/// inspired by GMPy_MPZ_Function_Bincoef 
#include <Python.h>
#include <gmp.h>
#include "safe_mpz_alloc.c"
static PyObject *
GMPy_MPZ_Function_Bincoef(PyObject *self, PyObject * const *args)
{
    MPZ_Object *result = NULL, *tempx;
    unsigned long n, k;

    /*if (nargs != 2) {
        TYPE_ERROR("bincoef() requires two integer arguments");
        return NULL;
    }*/
   //this block can be safely ignored as it is now safe to assume that args tuple has length 2
   
    mpz_t x;            // Declare the variable (not a pointer!)
    if(mpz_safe_init(x)){
        return NULL;
    }
    k = PyLong_AsUnsignedLong(PyTuple_GET_ITEM(args, 1));
    if (k == (unsigned long)(-1) && PyErr_Occurred()) {
        return NULL;
    }

    n = PyLong_AsUnsignedLong(args[0]);
    if (n == (unsigned long)(-1) && PyErr_Occurred()) {
        PyErr_Clear();
    }
    else {
        /* Use mpz_bin_uiui which should be faster. */
        mpz_bin_uiui(result->z, n, k);
        return (PyObject*)result;
    }

    if (!(tempx = GMPy_MPZ_From_Integer(args[0], NULL))) {
        Py_DECREF((PyObject*)result);
        return NULL;
    }
    mpz_get_ui();
    mpz_bin_ui(result->z, tempx->z, k);
    Py_DECREF((PyObject*)tempx);
    return (PyObject*)result;
}