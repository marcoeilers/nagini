/*
 * Compilable CPython extension module for the bincoeff case study.
 *
 * This file packages the *verified* compute_bincoeff function (see bincoeff.c,
 * which is checked by VeriFast against the formalized CPython C API) as a real,
 * importable Python module. Compared to bincoeff.c it adds:
 *   - the CPython module boilerplate at the bottom,
 *   - a placeholder implementation of the GMP `mpz` integer API (a real build
 *     would instead #include <gmp.h> and link against GMP), and
 *   - no-op definitions of the ghost operations borrowRefs/returnRefs, which
 *     exist only for the VeriFast proof and have no runtime effect.
 *
 * The VeriFast annotations are ordinary C comments, so the verified function
 * body below is byte-for-byte the one that is verified.
 *
 * Build:  python setup.py build_ext --inplace
 * Use:    import bincoeff_native; bincoeff_native.compute_bincoeff(n, k)
 */
#include <Python.h>
#include <stdlib.h>

/* ------------------------------------------------------------------ */
/* Placeholder for the GMP `mpz` API (trusted/axiomatized in           */
/* mpz_include.c during verification; a real build links against GMP). */
/* ------------------------------------------------------------------ */
typedef unsigned long int mp_limb_t;
struct __mpz_struct {
    int _mp_alloc;
    int _mp_size;
    mp_limb_t *_mp_d;
};
typedef struct __mpz_struct *mpz_t;

static void mpz_init(mpz_t x) {
    x->_mp_d = (mp_limb_t *) malloc(sizeof(mp_limb_t));
    x->_mp_d[0] = 0;
    x->_mp_alloc = 1;
    x->_mp_size = 0;
}

static void mpz_clear(mpz_t x) {
    free(x->_mp_d);
    x->_mp_d = NULL;
}

/* C(n, k) via the multiplicative formula (placeholder for mpz_bin_uiui). */
static void mpz_bin_uiui(mpz_t res, unsigned long n, unsigned long k) {
    unsigned long long r = 1;
    if (k > n) {
        r = 0;
    } else {
        if (k > n - k) {
            k = n - k;
        }
        for (unsigned long i = 0; i < k; i++) {
            r = r * (n - i) / (i + 1);
        }
    }
    res->_mp_d[0] = (mp_limb_t) r;
    res->_mp_size = (r != 0) ? 1 : 0;
}

static unsigned long mpz_get_ui(mpz_t x) {
    return (unsigned long) x->_mp_d[0];
}

/* ------------------------------------------------------------------ */
/* Ghost operations: used only by the VeriFast proof, no-ops at runtime */
/* ------------------------------------------------------------------ */
static void borrowRefs(PyObject *t) { (void) t; }
static void returnRefs(PyObject *t) { (void) t; }

/* ------------------------------------------------------------------ */
/* The verified function, verbatim from bincoeff.c.                    */
/* ------------------------------------------------------------------ */
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

/* ------------------------------------------------------------------ */
/* CPython module boilerplate.                                         */
/* ------------------------------------------------------------------ */
static PyMethodDef BincoeffMethods[] = {
    {"compute_bincoeff", (PyCFunction) compute_bincoeff, METH_VARARGS,
     "compute_bincoeff(n, k): the binomial coefficient C(n, k)."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef bincoeffmodule = {
    PyModuleDef_HEAD_INIT,
    "bincoeff_native",
    "Verified binomial-coefficient C extension (placeholder GMP).",
    -1,
    BincoeffMethods
};

PyMODINIT_FUNC
PyInit_bincoeff_native(void) {
    return PyModule_Create(&bincoeffmodule);
}
