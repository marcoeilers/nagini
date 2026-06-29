#ifndef VF_PY_OBJ_METH_H
#define VF_PY_OBJ_METH_H
#include "defs/Cdefs.c"
#include "defs/vfdefs/VFdefs.c"

// TODO: maybe define enough things to support this thing
// int PyObject_Print(PyObject *o, FILE *fp, int flags);
int PyObject_HasAttr(PyObject *o, PyObject *attr_name);
/*@
    requires hasRef(o, ?ownO) &*& hasRef(attr_name, ?ownA) &*&
        pyobj_hasval(o, ?o_val) &*&
        pyobj_hasval(attr_name, PyUnicode_v(?attr_name_val)) &*&
        pyobj_maysetattr(o, attr_name_val, ?zut);
@*/
/*@
    ensures hasRef(o, ownO) &*& hasRef(attr_name, ownA) &*&
        pyobj_hasval(o, o_val) &*&
        pyobj_hasval(attr_name, PyUnicode_v(attr_name_val)) &*&
        pyobj_maysetattr(o, attr_name_val, zut) &*&
        result == 1;
        @*/
int PyObject_HasAttrString(PyObject *o, const char *attr_name);
/*@
    requires hasRef(o, ?ownO) &*&
        pyobj_hasval(o, ?o_val) &*&
        [?f]string(attr_name, ?attr_name_val) &*&
        pyobj_maysetattr(o, attr_name_val, ?zut);
@*/
/*@
    ensures hasRef(o, ownO) &*&
        pyobj_hasval(o, o_val) &*&
        [f]string(attr_name, attr_name_val) &*&
        pyobj_maysetattr(o, attr_name_val, zut) &*&
        result == 1;
        @*/
PyObject *PyObject_GetAttr(PyObject *o, PyObject *attr_name);
/*@
    requires PyExc(?e, ?t) &*&
        hasRef(o, ?ownO) &*& hasRef(attr_name, ?ownA) &*&
        pyobj_hasval(o, ?o_val) &*&
        pyobj_hasval(attr_name, PyUnicode_v(?attr_name_val)) &*&
        [?f]pyobj_hasattr(o, attr_name_val, ?o_attr_ptr) &*&
        pyobj_hasval(o_attr_ptr, ?o_attr_val);
@*/
/*@
    ensures PyExc(?e_new, ?t_new) &*&
        hasRef(o, ownO) &*& hasRef(attr_name, ownA) &*&
        pyobj_hasval(o, o_val) &*&
        pyobj_hasval(o_attr_ptr, o_attr_val) &*&
        pyobj_hasval(attr_name, PyUnicode_v(attr_name_val)) &*&
        [f]pyobj_hasattr(o, attr_name_val, o_attr_ptr) &*&
        (e_new == e)?(
            result!=NULL &*&
            pyobj_hasval(result, _) &*&
            hasRef(result, true) &*&
            result==o_attr_ptr
        ):(
            result == NULL &*&
            t_new !=t &*& (t_new == some(MemoryError) || t_new == some(RuntimeError))
        );
@*/
// Returns a new (owned) reference to the attribute value on success, hence
// hasRef(result, true). Interacting with o requires holding some reference.
PyObject *PyObject_GetAttrString(PyObject *o, const char *attr_name);
/*@
    requires PyExc(?e, ?t) &*&
        hasRef(o, ?own) &*&
        pyobj_hasval(o, ?o_val) &*&
        [?p]string(attr_name, ?attr_name_val) &*&
        [?f]pyobj_hasattr(o, attr_name_val, ?o_attr_ptr) &*&
        [f]pyobj_hasval(o_attr_ptr, ?o_attr_val);
@*/
/*@
    ensures PyExc(?e_new, ?t_new) &*&
        hasRef(o, own) &*&
        pyobj_hasval(o, o_val) &*&
        [p]string(attr_name, attr_name_val) &*&
        [f]pyobj_hasattr(o, attr_name_val, o_attr_ptr) &*&
        [f]pyobj_hasval(o_attr_ptr, o_attr_val) &*&
        (result == NULL)?(
            e_new != e &*& e_new == some(_) &*&
            (t_new == some(MemoryError) || t_new == some(RuntimeError))
        ):(
            e_new == e &*& t_new == t &*&
            hasRef(result, true) &*&
            result==o_attr_ptr
        );
@*/
int PyObject_SetAttr(PyObject *o, PyObject *attr_name, PyObject *v);
/*@requires  PyExc(?e, ?t) &*&
        hasRef(o, ?ownO) &*& hasRef(attr_name, ?ownA) &*& hasRef(v, ?ownV) &*&
        pyobj_hasval(attr_name, PyUnicode_v(?attr_name_val)) &*&
        pyobj_hasval(v, ?v_val) &*&
        pyobj_hasval(o, _) &*&
        pyobj_hasattr(o, attr_name_val, ?o_attr_ptr) &*&
        pyobj_hasval(o_attr_ptr, ?o_attr_val);
        @*/
/*@ensures PyExc(?e_new, ?t_new) &*&
        hasRef(o, ownO) &*& hasRef(attr_name, ownA) &*& hasRef(v, ownV) &*&
        pyobj_hasval(attr_name, PyUnicode_v(attr_name_val)) &*&
        pyobj_hasval(v, v_val) &*&
        (result == 0)?(
            e_new == e &*& t_new == t &*&
            pyobj_hasattr(o, attr_name_val, v) &*&
            pyobj_hasval(v, v_val)
        ):(
            result == -1 &*&
            e_new != e &*& e_new == some(_) &*& t_new == some(_) &*&
            pyobj_hasattr(o, attr_name_val, o_attr_ptr) &*&
            pyobj_hasval(o_attr_ptr, o_attr_val) &*&
            t_new !=t &*& (t_new == some(MemoryError) || t_new == some(RuntimeError))
        );
@*/
// Stores v in o's attribute. CPython INCREFs v internally and DECREFs the old
// value, so from the caller's view neither o's nor v's reference is consumed:
// both are required and returned (SetAttrString does not steal v).
int PyObject_SetAttrString(PyObject *o, const char *attr_name, PyObject *v);
/*@
    requires  PyExc(?e, ?t) &*&
        hasRef(o, ?ownO) &*& hasRef(v, ?ownV) &*&
        [?f]string(attr_name, ?attr_name_val) &*&
        pyobj_hasval(v, ?v_val) &*&
        pyobj_hasval(o, ?o_val) &*&
        pyobj_hasattr(o, attr_name_val, ?o_attr_ptr);
@*/
/*@
    ensures PyExc(?e_new, ?t_new) &*&
        hasRef(o, ownO) &*& hasRef(v, ownV) &*&
        [f]string(attr_name, attr_name_val) &*&
        pyobj_hasval(o, o_val) &*&
        pyobj_hasval(v, v_val) &*&
        (result == 0)?(
            e_new == e &*& t_new == t &*&
            pyobj_hasattr(o, attr_name_val, v)
        ):(
            result == -1 &*&
            e_new != e &*& e_new == some(_) &*& t_new == some(_) &*&
            pyobj_hasattr(o, attr_name_val, o_attr_ptr) &*&
            t_new !=t &*& (t_new == some(MemoryError) || t_new == some(RuntimeError))
        );
@*/
int PyObject_DelAttr(PyObject *o, PyObject *attr_name);
/*@
    requires PyExc(?e, ?t) &*&
        hasRef(o, ?ownO) &*& hasRef(attr_name, ?ownA) &*&
        pyobj_hasval(o, ?o_val) &*&
        pyobj_hasval(attr_name, PyUnicode_v(?attr_name_val)) &*&
        pyobj_hasattr(o, attr_name_val, ?o_attr_ptr) &*&
        pyobj_hasval(o_attr_ptr, ?o_attr_val);
@*/
/*@
        ensures PyExc(?e_new, ?t_new) &*&
            hasRef(o, ownO) &*& hasRef(attr_name, ownA) &*&
            pyobj_hasval(o, o_val) &*&
            pyobj_hasval(attr_name, PyUnicode_v(attr_name_val)) &*&
            (e_new == e)?(
                result == 0 &*&
                pyobj_maycreateattr(o, attr_name_val)):
            (
                result == -1 &*&
                pyobj_hasattr(o, attr_name_val, o_attr_ptr) &*&
                pyobj_hasval(o_attr_ptr, o_attr_val) &*&
                t_new !=t &*& (t_new == some(MemoryError) || t_new == some(RuntimeError))
            );
@*/

int PyObject_DelAttrString(PyObject *o, const char *attr_name);
/*@
    requires PyExc(?e, ?t) &*&
        hasRef(o, ?ownO) &*&
        pyobj_hasval(o, ?o_val) &*&
        [?f]string(attr_name, ?attr_name_val) &*&
        pyobj_hasattr(o, attr_name_val, ?o_attr_ptr) &*&
        pyobj_hasval(o_attr_ptr, ?o_attr_val);
@*/
/*@
        ensures PyExc(?e_new, ?t_new) &*&
            hasRef(o, ownO) &*&
            pyobj_hasval(o, o_val) &*&
            [f]string(attr_name, attr_name_val) &*&
            (e_new == e)?(
                result == 0 &*&
                pyobj_maycreateattr(o, attr_name_val)):
            (
                result == -1 &*&
                pyobj_hasattr(o, attr_name_val, o_attr_ptr) &*&
                pyobj_hasval(o_attr_ptr, o_attr_val) &*&
                t_new !=t &*& (t_new == some(MemoryError) || t_new == some(RuntimeError))
            );
@*/
// Python Object Comparison
// TODO: this may require a pyclass instance to contain all the fields of the instance and their types
// then: require all attributes to be owned
// then: check if all attributes are equal
PyObject *PyObject_RichCompare(PyObject *o1, PyObject *o2, int opid);
//@requires false;
//@ensures false;
int PyObject_RichCompareBool(PyObject *o1, PyObject *o2, int opid);
//@requires false;
//@ensures false;
PyObject *PyObject_Format(PyObject *obj, PyObject *format_spec);
//@requires false;
//@ensures false;
PyObject *PyObject_Repr(PyObject *o);
//@requires false;
//@ensures false;
PyObject *PyObject_ASCII(PyObject *o);
//@requires false;
//@ensures false;
PyObject *PyObject_Str(PyObject *o);
//@requires false;
//@ensures false;
PyObject *PyObject_Bytes(PyObject *o);
//@requires false;
//@ensures false;
int PyObject_IsSubclass(PyObject *derived, PyObject *cls);
/*@
    requires hasRef(derived, ?ownDerived) &*& hasRef(cls, ?ownCls) &*&
        pyobj_hasval(derived, PyType_v(?derived_type)) &*&
        pyobj_hasval(cls, PyType_v(?cls_type));
@*/
/*@
    ensures hasRef(derived, ownDerived) &*& hasRef(cls, ownCls) &*&
        pyobj_hasval(derived, PyType_v(derived_type)) &*&
        pyobj_hasval(cls, PyType_v(cls_type)) &*&
        result == (issubtype(derived_type, cls_type)?1:0);
@*/

static int PyObject_IsInstance(PyObject *inst, PyObject *cls);
/*@
    requires
        hasRef(inst, ?ownInst) &*& hasRef(cls, ?ownCls) &*&
        pyobj_hasval(inst, ?instval) &*&
        pyobj_hasval(cls, ?clsval) &*&
        clsval==PyType_v(?cls_type);
@*/
/*@ensures
        hasRef(inst, ownInst) &*& hasRef(cls, ownCls) &*&
        pyobj_hasval(inst, instval) &*&
        pyobj_hasval(cls, clsval)  &*&
        result == (isinstance(instval, cls_type)?1:0);
@*/
#endif