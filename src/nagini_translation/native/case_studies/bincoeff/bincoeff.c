#ifdef COMPILING FOR PYTHON
#include <Python.h>
#include <gmp.h>
#else
#include "mpz_include.c"
#include "../../PythonAPI/vfpy.c"
#endif
/*@
fixpoint PyClass PyClass_ObjectType(){
    return ObjectType;
}
fixpoint int PURE_bincoeff(int VALUEONLY_n__val, int VALUEONLY_k__val)
    decreases VALUEONLY_n__val;
{
     return (VALUEONLY_n__val <= 0) ? ((VALUEONLY_k__val == 0) ? 1 : 0) : ((VALUEONLY_k__val == 0 || VALUEONLY_n__val == VALUEONLY_k__val) ? 1 : (PURE_bincoeff((VALUEONLY_n__val - 1), (VALUEONLY_k__val - 1)) + PURE_bincoeff((VALUEONLY_n__val - 1), VALUEONLY_k__val)));
}
@*/
/*--END OF ENV--*/
/*@
lemma_auto void bin_mpz__2__PURE_bincoeff(unsigned int n, unsigned int k);
  requires true;
  ensures PURE_bincoeff(n, k) == bin_mpz(n, k);
@*/


static PyObject *
compute_bincoeff(PyObject *self, PyObject *args)
/*@
requires PyExc(none, none) &*&
gil_lock(?gstate) &*&
hasRef(args, false) &*&
pyobj_hasval(args, PyTuple_v(cons(pair(?n__ptr, PyLong_t), cons(pair(?k__ptr, PyLong_t), nil)))) &*&
pyobj_hasval(n__ptr, PyLong_v(?n__val)) &*&
pyobj_hasval(k__ptr, PyLong_v(?k__val)) &*&
((((n__val >= 0) && (k__val >= 0)) && (k__val <= n__val)) && (n__val <= 63));
@*/
/*@
ensures PyExc(none, none) &*&
gil_lock(gstate) &*&
hasRef(args, false) &*&
hasRef(result, true) &*&
pyobj_hasval(args, PyTuple_v(cons(pair(n__ptr, PyLong_t), cons(pair(k__ptr, PyLong_t), nil)))) &*&
pyobj_hasval(n__ptr, PyLong_v(n__val)) &*&
pyobj_hasval(k__ptr, PyLong_v(k__val)) &*&
pyobj_hasval(result, PyLong_v(?result__val)) &*&
(result__val == PURE_bincoeff(n__val, k__val));
@*/
{
    unsigned long n, k;
    struct __mpz_struct x_s = {0, 0, NULL};

    // Read the (borrowed) argument pointers while we still hold hasRef(args).
    PyObject *n_obj = PyTuple_GetItem(args, 0);
    PyObject *k_obj = PyTuple_GetItem(args, 1);

    // borrowRefs consumes hasRef(args) and hands out a borrowed reference to
    // each element, which PyLong_AsUnsignedLong needs to read them. The two
    // arguments may alias (e.g. compute_bincoeff(5,5), where CPython caches the
    // small int), which the (multiset) bigstar machinery handles fine.
    borrowRefs(args);
    //@ bigstar_extract(hasBorrowedRef(), n__ptr);
    //@ open hasBorrowedRef()(n__ptr);
    //@ bigstar_extract(hasBorrowedRef(), k__ptr);
    //@ open hasBorrowedRef()(k__ptr);

    n = PyLong_AsUnsignedLong(n_obj);
    k = PyLong_AsUnsignedLong(k_obj);

    // Give the borrowed element references back and recover hasRef(args).
    //@ close hasBorrowedRef()(k__ptr);
    //@ bigstar_inject(hasBorrowedRef(), k__ptr);
    //@ close hasBorrowedRef()(n__ptr);
    //@ bigstar_inject(hasBorrowedRef(), n__ptr);
    returnRefs(args);

    mpz_t x = &x_s; // Declare the variable (not a pointer!)
    mpz_init(x);    // Initialize the variable
    mpz_bin_uiui(x, n, k);
    unsigned long res = mpz_get_ui(x);
    mpz_clear(x);
    PyObject *r = PyLong_FromUnsignedLong(res);
    while (r == NULL)
/*@
    invariant PyExc(?e_ptr, ?t_ptr) &*&
    pyobj_hasval(args, PyTuple_v(cons(pair(n__ptr, PyLong_t), cons(pair(k__ptr, PyLong_t), nil)))) &*&
    pyobj_hasval(n__ptr, PyLong_v(n__val)) &*&
    pyobj_hasval(k__ptr, PyLong_v(k__val)) &*&
    (r == NULL)?
        (e_ptr==some(_) &*& t_ptr==some(_)):
        (hasRef(r, true) &*& pyobj_hasval(r, PyLong_v(res)));
@*/
    {
        r = PyLong_FromUnsignedLong(res);
    }
    PyErr_Clear();
    return r;
}
