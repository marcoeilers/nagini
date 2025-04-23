/// inspired by GMPy_MPZ_Function_Bincoef
#ifdef COMPILING FOR PYTHON
#include <Python.h>
#include <gmp.h>
#else
#include "mpz_include.c"
#include "../vfpy/PythonAPI/vfpy.c"
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
GMPy_MPZ_Function_Bincoef(PyObject *self, PyObject *args)
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
result__val == PURE_bincoeff(n__val, k__val);
@*/

{
    //@ assert n__val <= 63;
    //@ assert ULONG_MAX > 63;
    PyObject *obj_n = PyTuple_GetItem(args, 0);

    unsigned long n, k;
    struct __mpz_struct x_s = {0, 0, NULL};
    mpz_t x = &x_s; // Declare the variable (not a pointer!)
    mpz_init(x);    // Initialize the variable

    PyGILState_STATE gstate = PyGILState_Ensure();
    n = PyLong_AsUnsignedLong(PyTuple_GetItem(args, 0));
    PyObject *obj_k = PyTuple_GetItem(args, 1);
    k = PyLong_AsUnsignedLong(obj_k);
    mpz_bin_uiui(x, n, k);
    unsigned long res = mpz_get_ui(x);
    mpz_clear(x); // Clear the variable*/
    //@ assert PyExc(none, none);
    // 
    PyObject *r = NULL;
    r = PyLong_FromUnsignedLong(res);
    while(!PyErr_Occurred())
    //@ invariant true;
    {
        r = PyLong_FromUnsignedLong(res);
        if(r != NULL){
            PyErr_Clear();
            break;
        }
    } 
    PyGILState_Release(gstate);
    PyErr_Clear();
    return r;
}