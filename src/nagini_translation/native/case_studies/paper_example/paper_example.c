//verifast_options{target:LP64}
// Verify with: verifast -read_options_from_source_file -allow_dead_code -c paper_example.c
// (LP64 makes `long` 64-bit so LONG_MAX/LONG_MIN match the spec bounds;
//  -allow_dead_code permits the defensive checks of Listing 1.1, which the
//  precondition renders unreachable.)
#ifdef COMPILING FOR PYTHON
#include <Python.h>
#else
#include "../../PythonAPI/vfpy.c"
#endif
/*@
fixpoint PyClass PyClass_ObjectType(){
    return ObjectType;
}
fixpoint int PURE_LONG_MIN(){
    return (0 - 9223372036854775808);
}
fixpoint int PURE_LONG_MAX(){
    return 9223372036854775807;
}
@*/
/*--END OF ENV--*/
static PyObject *
py_max(PyObject *self, PyObject *args)
/*@
requires PyExc(none, none) &*&
gil_lock(?gstate) &*&
hasRef(args, false) &*&
pyobj_hasval(args, PyTuple_v(cons(pair(?a__ptr, PyLong_t), cons(pair(?b__ptr, PyLong_t), nil)))) &*&
pyobj_hasval(a__ptr, PyLong_v(?a__val)) &*&
pyobj_hasval(b__ptr, PyLong_v(?b__val)) &*&
((PURE_LONG_MIN() < a__val) && (a__val < PURE_LONG_MAX())) &*&
((PURE_LONG_MIN() < b__val) && (b__val < PURE_LONG_MAX()));
@*/
/*@
ensures PyExc(none, none) &*&
gil_lock(gstate) &*&
hasRef(args, false) &*&
hasRef(result, true) &*&
pyobj_hasval(args, PyTuple_v(cons(pair(a__ptr, PyLong_t), cons(pair(b__ptr, PyLong_t), nil)))) &*&
pyobj_hasval(a__ptr, PyLong_v(a__val)) &*&
pyobj_hasval(b__ptr, PyLong_v(b__val)) &*&
pyobj_hasval(result, PyLong_v(?result__val)) &*&
(result == ((a__val > b__val) ? a__ptr : b__ptr));
@*/
{
    // Check if 'args' is a tuple with 2 elements. The precondition already
    // guarantees this, so VeriFast proves this branch dead (hence the run needs
    // -allow_dead_code); it is kept to faithfully mirror Listing 1.1.
    if (!PyTuple_Check(args) || PyTuple_Size(args) != 2) {
        PyErr_SetString(PyExc_TypeError, "Expected exactly 2 arguments");
        return NULL;
    }

    // Get items from tuple. PyTuple_GetItem returns a borrowed reference.
    PyObject* obj_a = PyTuple_GetItem(args, 0);
    PyObject* obj_b = PyTuple_GetItem(args, 1);

    // Borrow references to the two elements so we can read and INCREF them.
    borrowRefs(args);
    //@ bigstar_extract(hasBorrowedRef(), a__ptr);
    //@ open hasBorrowedRef()(a__ptr);
    //@ bigstar_extract(hasBorrowedRef(), b__ptr);
    //@ open hasBorrowedRef()(b__ptr);

    // Unfold the LONG_MIN/LONG_MAX fixpoints so VeriFast can discharge
    // PyLong_AsLong's in-range precondition (LONG_MAX == 9223372036854775807
    // under the LP64 target).
    //@ assert PURE_LONG_MAX() == 9223372036854775807;
    //@ assert PURE_LONG_MIN() == (0 - 9223372036854775808);
    // Convert to C longs (in range by the precondition, so no exception).
    long val_a = PyLong_AsLong(obj_a);
    if (PyErr_Occurred()) return NULL;
    long val_b = PyLong_AsLong(obj_b);
    if (PyErr_Occurred()) return NULL;

    // Compare with C operators. NB: the spec returns a when a > b (else b), so
    // we use '>' here (Listing 1.1 uses '>=', which would disagree at a == b).
    PyObject* winner;
    if (val_a > val_b) {
        winner = obj_a;
    } else {
        winner = obj_b;
    }

    // winner aliases one of the borrowed tuple elements; INCREF it so the
    // caller owns the returned reference.
    Py_INCREF(winner);

    // The result object's value is also one of the argument values; the
    // postcondition mentions it twice, so duplicate the (pure) value knowledge.
    //@ pyobj_hasval_dup(winner);

    // Return the borrowed element references and recover hasRef(args).
    //@ close hasBorrowedRef()(b__ptr);
    //@ bigstar_inject(hasBorrowedRef(), b__ptr);
    //@ close hasBorrowedRef()(a__ptr);
    //@ bigstar_inject(hasBorrowedRef(), a__ptr);
    returnRefs(args);

    return winner;
}
