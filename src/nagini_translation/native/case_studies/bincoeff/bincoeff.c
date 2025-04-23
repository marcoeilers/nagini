/// inspired by GMPy_MPZ_Function_Bincoef
#ifdef COMPILING FOR PYTHON
#include <Python.h>
#include <gmp.h>
#else
#include "mpz_include.c"
#include "vfpy.c"
#endif

/*@
fixpoint PyClass PyClass_ObjectType(){
    return ObjectType;
}
fixpoint int PURE_bincoeff(int VALUEONLY_n__val, int VALUEONLY_k__val){
     return ((VALUEONLY_k__val == 0) ? 1 : ((VALUEONLY_n__val == VALUEONLY_k__val) ? 1 : (PURE_bincoeff((VALUEONLY_n__val - 1), (VALUEONLY_k__val - 1)) + PURE_bincoeff((VALUEONLY_n__val - 1), VALUEONLY_k__val))));
}
@*/
/*--END OF ENV--*/
static PyObject *
GMPy_MPZ_Function_Bincoef(PyObject *self, PyObject *const *args)
/*@
requires PyExc(none, none) &*&
pyobj_hasval(args, PyTuple_v(cons(pair(?n__ptr, PyLong_t), cons(pair(?k__ptr, PyLong_t), nil)))) &*&
pyobj_hasval(n__ptr, PyLong_v(?n__val)) &*&
pyobj_hasval(k__ptr, PyLong_v(?k__val)) &*&
((((n__val >= 0) && (k__val >= 0)) && (k__val <= n__val)) && (n__val <= 63));
@*/ 
/*@
ensures PyExc(none, none) &*&
pyobj_hasval(args, PyTuple_v(cons(pair(n__ptr, PyLong_t), cons(pair(k__ptr, PyLong_t), nil)))) &*&
pyobj_hasval(n__ptr, PyLong_v(n__val)) &*&
pyobj_hasval(k__ptr, PyLong_v(k__val)) &*&
pyobj_hasval(result, PyLong_v(?result__val)) &*&
(result__val == PURE_bincoeff(n__val, k__val));
@*/

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