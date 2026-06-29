#ifndef VF_PY_DEFS_H
#define VF_PY_DEFS_H
#include "../Cdefs.c"

// The type to represent Python classes
// TODO: define a recursive fixpoint to return the complete list of attributes of a class
// PYOBJ VALUES
/*@
inductive PyObj_Val =
    PyBool_v(bool) |
    PyLong_v(int) |
    PyFloat_v(double) |
    PyUnicode_v(list<char>) |
    PyClassInstance_v(PyClass) |
    PyType_v(PyObj_Type) |
    PyList_v(PyObj_Type) |
    PyTuple_v(list< pair<PyObject *, PyObj_Type> >) |
    PyNone_v;
predicate pyobj_hasval(PyObject* pyobj; PyObj_Val v);
predicate pyobj_hasval_or_null(PyObject* pyobj; option<PyObj_Val> v) =
    pyobj == NULL ? v == none :
    pyobj != NULL &*& pyobj_hasval(pyobj, ?x) &*& v == some(x);
@*/
// PYOBJ TYPES
/*@
inductive PyObj_Type =
    PyType_t |
    PyNone_t |
    PyLong_t | PyBool_t | PyFloat_t | PyComplex_t |
    PyUnicode_t |
    PyList_t (PyObj_Type) |
    PyTuple_t (list<PyObj_Type>) |
    PyClass_t(PyClass);
fixpoint PyObj_Type pyobj_typeof(PyObj_Val v) { //PyObj_Val → PyObj_Type
    switch(v) {
        case PyBool_v(x):
            return PyBool_t;
        case PyLong_v(x):
            return PyLong_t;
        case PyFloat_v(x):
            return PyFloat_t;
        case PyUnicode_v(x):
            return PyUnicode_t;
        case PyClassInstance_v(x):
            return PyClass_t(x);
        case PyType_v(x):
            return PyType_t;
        case PyTuple_v(x):
            return PyTuple_t(map(snd, x));
        case PyList_v(x):
            return PyList_t(x);
        case PyNone_v:
            return PyNone_t;
    }
}
predicate map_pyobj_hasval(list< PyObject*> l, list<PyObj_Val> v) =
    switch (l)
    {
        case nil: return v == nil;
        case cons(x, xs):
            return pyobj_hasval(x, ?v1) &*& map_pyobj_hasval(xs, ?v2) &*& v == cons(v1, v2);
    };
@*/
// PYOBJ ATTRIBUTES
/*@
predicate pyobj_hasattr(PyObject* i, list<char> n; PyObject* out);
predicate pyobj_maysetattr(PyObject* i, list<char> n, option<PyObject*> out)= switch(out) {
        case none: return pyobj_maycreateattr(i, n);
        case some(x): return pyobj_hasattr(i, n, x);
    };
predicate pyobj_maycreateattr(PyObject* i, list<char> n);

@*/
// PYOBJ CONTENT
/*@
inductive PyObj_Content = List(list<PyObject*>);//TODO: one day, add dict in the induct_type?
predicate pyobj_hascontent(PyObject* pyobj, PyObj_Content c);
@*/
// PYOBJ REFERENCES (reference counting / ownership)
/*@
// Ownership of one reference to the object *o points to. owned == true for a
// directly owned (new) reference, owned == false for a borrowed one. Unlike
// pyobj_hasval (pure, duplicable value knowledge) this is a genuine,
// non-duplicable resource: each instance represents exactly one held reference,
// so leaks and use-after-free become verification errors.
predicate hasRef(PyObject *o, bool owned);

// Iterated separating conjunction, used to hold the borrowed references to all
// elements of a tuple while the tuple's own reference is temporarily consumed.
predicate bigstar<T>(predicate(T) p, list<T> avail);
lemma void bigstar_extract<T>(predicate(T) p, T value);
    requires bigstar<T>(p, ?avail) &*& true == mem(value, avail);
    ensures bigstar<T>(p, remove(value, avail)) &*& p(value);
// No !mem(value, avail) precondition: bigstar is a list-based (multiset)
// iterated separating conjunction, so prepending another p(value) is always
// sound even when value already occurs in avail (e.g. a tuple holding the same
// object — such as a cached small int — at two positions).
lemma void bigstar_inject<T>(predicate(T) p, T value);
    requires bigstar<T>(p, ?avail) &*& p(value);
    ensures bigstar<T>(p, cons(value, avail));

predicate_ctor hasBorrowedRef()(PyObject *o) = hasRef(o, false);

// The right to exchange the borrowed references to a tuple's elements back for
// the reference to the tuple itself (see borrowRefs/returnRefs). Tuples need
// this because the C API has no PyTuple_GetItemRef; lists use PyList_GetItemRef
// (which returns a new reference) instead, so they need no analogous machinery.
predicate borrowedTupleRefs(PyObject *t, list<pair<PyObject *, PyObj_Type> > vls, bool owned);

// Two objects holding different values are necessarily distinct objects:
// pyobj_hasval is precise (functional), so equal pointers would force equal
// values. Sound; used to discharge the distinctness side conditions of the
// tuple-borrow machinery when the element types differ.
lemma void pyobj_hasval_distinct(PyObject *p1, PyObject *p2);
    requires pyobj_hasval(p1, ?v1) &*& pyobj_hasval(p2, ?v2) &*& v1 != v2;
    ensures  pyobj_hasval(p1, v1) &*& pyobj_hasval(p2, v2) &*& p1 != p2;

// pyobj_hasval is pure, immutable value knowledge and may be freely duplicated.
// Any positive fraction lets you assert the value, so from any fraction we can
// produce an additional full copy. (Ownership of the object is tracked
// separately by hasRef, so duplicating the value carries no permission.) Sound
// for a precise/immutable predicate.
lemma void pyobj_hasval_dup(PyObject *p);
    requires [?f]pyobj_hasval(p, ?v);
    ensures  [f]pyobj_hasval(p, v) &*& pyobj_hasval(p, v);

// Dual of pyobj_hasval_dup: pure value knowledge may also be discarded (any
// fraction). Forgetting an immutable fact is always sound. Preferable to the
// built-in `leak`, which parks the chunk in VeriFast's leaked set (and can thus
// hide a genuine, unintended leak) rather than truly consuming it.
lemma void pyobj_hasval_drop(PyObject *p);
    requires [?f]pyobj_hasval(p, ?v);
    ensures  true;
@*/
// FORALL PREDICATES
/*@
predicate pyobj_hasPyLongval(PyObject* pyobj, int v) = pyobj_hasval(pyobj, PyLong_v(v));
predicate pyobj_hasPyBoolval(PyObject* pyobj, bool v) = pyobj_hasval(pyobj, PyBool_v(v));
predicate pyobj_hasPyFloatval(PyObject* pyobj, double v) = pyobj_hasval(pyobj, PyFloat_v(v));
predicate pyobj_hasPyUnicodeval(PyObject* pyobj, list<char> v) = pyobj_hasval(pyobj, PyUnicode_v(v));
predicate_ctor pyobj_hasPyClassInstanceval(PyClass v)(PyObject* pyobj, unit) = pyobj_hasval(pyobj, PyClassInstance_v(v));
predicate_ctor pyobj_hasPyTypeval( PyObj_Type v)(PyObject* pyobj) = pyobj_hasval(pyobj, PyType_v(v));
predicate_ctor pyobj_hasPyListval(PyObj_Type v)(PyObject* pyobj, unit) = pyobj_hasval(pyobj, PyList_v(v));
predicate pyobj_hasPyTupleval(PyObject* pyobj, list< pair<PyObject *, PyObj_Type> > v) = pyobj_hasval(pyobj, PyTuple_v(v));
predicate pyobj_hasPyNoneval(PyObject* pyobj, unit) = pyobj_hasval(pyobj, PyNone_v);

inductive list_forallcond = True | inrange(int a, int b, int c) | lt(int a) | gt(int a) | lte(int a) | gte(int a) | fixp(fixpoint(int, bool) f) | neg(list_forallcond c) | and(list_forallcond c1, list_forallcond c2) | or(list_forallcond c1, list_forallcond c2);
fixpoint bool list_forallcondeval(list_forallcond c, int x){
    switch(c){
        case True: return true;
        case inrange(a, b, c_): return a<=x && x<b && (x-a)%c_==0;
        case lt(a): return x<a;
        case gt(a): return x>a;
        case lte(a): return x<=a;
        case gte(a): return x>=a;
        case fixp(f): return f(x);
        case neg(c_): return !list_forallcondeval(c_, x);
        case and(c1, c2): return list_forallcondeval(c1, x) && list_forallcondeval(c2, x);
        case or(c1, c2): return list_forallcondeval(c1, x) || list_forallcondeval(c2, x);
    }
}
inductive attr_access_type = hasAttr(list<char>) | maySetAttr(list<char>) | mayCreateAttr(list<char>);
predicate_ctor attr_binary_pred(attr_access_type p) (PyObject* obj, PyObject *attr) = switch (p) {
    case hasAttr(x): return pyobj_hasattr(obj, x, attr);
    case maySetAttr(x): return pyobj_maysetattr(obj, x, ?v) &*& (v == none?true:v==some(attr));
    case mayCreateAttr(x): return pyobj_maycreateattr(obj, x);
};
predicate list_forallpred<intype, outtype>(list<pair<intype, outtype> > l, predicate(intype, outtype) p, list_forallcond cond, list<int> out);@*/

// TODO: parameterize out PyObj_Val
/*@
// map(fst, .) commutes with update (standard list fact, provable by induction).
// A plain lemma (not lemma_auto): an auto version with `requires true` fires far
// too eagerly and cripples solver performance.
lemma void map_fst_update<intype, outtype>(int idx, pair<intype, outtype> x, list<pair<intype, outtype> > l);
    requires true;
    ensures map(fst, update(idx, x, l)) == update(idx, fst(x), map(fst, l));
lemma_auto void retrieve_from_update<intype, outtype>(int idx, list<pair<intype, outtype> > l);
    requires 0 <= idx && idx < length(l);
    ensures update(idx, pair(fst(nth(idx, l)), snd(nth(idx, l))), l) == l;
lemma void list_forallpred_extract<intype, outtype>(list<pair<intype, outtype> > l, predicate(intype, outtype) p, int idx);
    requires [?f]list_forallpred(l, p, ?cond, ?out) &*& !mem(idx, out) &*& idx<length(l) &*& 0<=idx &*& list_forallcondeval(cond, idx) == true;
    ensures [f]list_forallpred(l,p, cond, cons(idx, out)) &*& [f]p(fst(nth(idx, l)) , snd(nth(idx, l)));
lemma void list_forallpred_insert<intype, outtype>(list<pair<intype, outtype> > l, predicate(intype, outtype) p, int idx);
    requires [?f]list_forallpred(l, p, ?cond, ?out) &*& mem(idx, out)==true &*& [f]p(fst(nth(idx, l)), ?new_val);
    ensures [f]list_forallpred(update(idx, pair(fst(nth(idx, l)), new_val), l), p, cond, remove(idx, out));
// Like list_forallpred_insert, but replaces the element pointer too (not just
// its value). Used when a list slot is overwritten with a different object
// (e.g. PyList_SET_ITEM). idx must currently be extracted (in out).
lemma void list_forallpred_replace<intype, outtype>(list<pair<intype, outtype> > l, predicate(intype, outtype) p, int idx, intype newkey, outtype newval);
    requires [?f]list_forallpred(l, p, ?cond, ?out) &*& mem(idx, out)==true &*& [f]p(newkey, newval);
    ensures [f]list_forallpred(update(idx, pair(newkey, newval), l), p, cond, remove(idx, out));
@*/

//@ inductive PyClass = PyClass(list<char>, PyClass, list<PyObj_Type>) | ObjectType;
/*@
    //TODO:replace this with a pyobj_val type
    fixpoint PyClass PyClass_List(PyObj_Type t) { return PyClass("list", ObjectType, cons(t, nil)); }
@*/
/*@
fixpoint bool issubclass(PyClass cls1, PyClass cls2){
    switch(cls1){
        //TODO: support generic type subtyping
        case PyClass(name1, parent1, typelist):
            return cls1 == cls2 || issubclass(parent1, cls2);
        case ObjectType:
            return cls2 == cls1;
    }
}
@*/
/*
    TODO: what happens if t2 is of type TYPE?
    A priori, t1 then is a type no matter what subtype is contained in t2
    BUT now:
    what if t1 is a type[TYPE] and t2 is a type[INT]
    maybe isinstance should treat the case of Pyobj_val=Pyobjtype as a special case?
*/
/*@
    fixpoint bool issubtype(PyObj_Type t1, PyObj_Type t2){
        switch(t2){
            case PyClass_t(cls2):
                return switch(t1){
                    case PyClass_t(cls1):
                        return issubclass(cls1, cls2);
                    default:
                        return false;
                };
            default:
                return t1 == t2;
        }
    }
@*/
/*@
fixpoint bool isinstance(PyObj_Val v, PyObj_Type t){
    return issubtype(pyobj_typeof(v), t);
}
@*/

/*@ 
predicate gil_lock(PyGILState_STATE gstate);
predicate PyExc_Flag(option<PyObject*>);
predicate PyExc(option<PyObject*> e, option<PyClass> type) = PyExc_Flag(e)
    &*& switch (e) {
        case none: return type == none;
        case some(x): return type==some(?y) &*& pyobj_hasval(x, PyClassInstance_v(y));
    };
    fixpoint PyClass BaseException(){
        return PyClass("BaseException", ObjectType, nil);
    }
    fixpoint PyClass Exception(){
        return PyClass("Exception", BaseException, nil);
    }
    fixpoint PyClass ValueError(){
        return PyClass("ValueError", Exception, nil);
    }
    fixpoint PyClass OverflowError(){
        return PyClass("OverflowError", Exception, nil);
    }
    fixpoint PyClass MemoryError(){
        return PyClass("MemoryError", Exception, nil);
    }
    fixpoint PyClass RuntimeError(){
        return PyClass("RuntimeError", Exception, nil);
    }
    fixpoint PyClass TypeError(){
        return PyClass("TypeError", Exception, nil);
    }
    fixpoint PyClass AttributeError(){
        return PyClass("AttributeError", Exception, nil);
    }
@*/

/*@
fixpoint list<t> slice<t>(list<t> l, int low, int high) {
    switch(l) {
        case nil: return nil;
        case cons(x,xs):
            return low <= 0 ? high <= 0 ? nil :
                cons(x, slice(xs, low-1, high-1)) :
                slice(xs, low-1, high-1);
    }
}
fixpoint t equiv<t,k>(k);


@*/
void m1(PyObject *obj)
//@ requires pyobj_maycreateattr(obj, "attr_name");
//@ ensures pyobj_maysetattr(obj, "attr_name", none);
{
    //@ close pyobj_maysetattr(obj, "attr_name", none);
}
void m2(PyObject *obj)
//@ requires pyobj_maysetattr(obj, "attr_name", none);
//@ ensures pyobj_maycreateattr(obj, "attr_name");
{
    //@ open pyobj_maysetattr(obj, "attr_name", none);
}
void m3(PyObject *obj)
//@ requires pyobj_maysetattr(obj, "attr_name", some(?v));
//@ ensures pyobj_hasattr(obj, "attr_name", v);
{
    //@ open pyobj_maysetattr(obj, "attr_name", some(v));
}
#endif