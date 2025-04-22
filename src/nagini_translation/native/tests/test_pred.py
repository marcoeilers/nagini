"""
fixpoint PyClass PyClass_ObjectType(){
                return ObjectType;
}
fixpoint PyClass PyClass_module_0A(){
                return PyClass("module_0A", PyClass_ObjectType, nil);
}
predicate PRED_pred1() = true;
predicate PRED_pred2(PyObject * x__ptr, PyClass x__val, PyObject * f__ptr, float f__val) = pyobj_hasattr(x__ptr, "a", ?x_DOT_a__ptr) &*&
pyobj_hasval(x_DOT_a__ptr, PyLong_v(?x_DOT_a__val)) &*&
pyobj_maycreateattr(x__ptr, "b") &*&
pyobj_maysetattr(x__ptr, "c", _) &*&
(x_DOT_a__val == 14);
predicate PRED_pred3(PyObject * x__ptr, PyClass x__val, PyObject * y__ptr, int y__val, PyObject *  z__ptr, float z__val) = pyobj_hasattr(x__ptr, "a", ?x_DOT_a__ptr) &*&
pyobj_hasval(x_DOT_a__ptr, PyLong_v(?x_DOT_a__val)) &*&
(x_DOT_a__val == 14) &*&
PRED_pred1();
"""
from nagini_contracts.contracts import *


class A:
        def __init__(self) -> None:
                self.a = 12
                Ensures(Acc(self.a))
                Ensures(MayCreate(self, 'b'))

        def set(self, v: int) -> None:
                Requires(MaySet(self, 'b'))
                self.b = v
                Ensures(Acc(self.b) and self.b == v)

        def set2(self, v: int) -> None:
                Requires(MayCreate(self, 'b'))
                self.b = v
                Ensures(Acc(self.b))


@Predicate
def pred1() -> bool:
        return True


@Predicate
def pred2(x: A, f: float) -> bool:
        return Acc(x.a) and MayCreate(x, 'b') and MaySet(x, 'c') and x.a == 14


@Predicate
def pred3(x: A, y: int, z: float) -> bool:
        return Acc(x.a) and x.a == 14 and pred1()


@Native
@ContractOnly
def test1() -> int:
        """
        requires PyExc(none, none) &*&
        pyobj_hasval(args, PyTuple_v(nil)) &*&
        true;

        ensures PyExc(none, none) &*&
        pyobj_hasval(args, PyTuple_v(nil)) &*&
        pyobj_hasval(result, PyLong_v(?result__val)) &*&
        true;
        """
        Requires(True)
        Ensures(True)


@Native
@ContractOnly
def test2(a: A, b: int) -> int:
        """
        requires PyExc(none, none) &*&
        pyobj_hasval(args, PyTuple_v(cons(pair(?a__ptr, PyClass_t(PyClass_module_0A())), cons(pair(?b__ptr, PyLong_t), nil)))) &*&
        pyobj_hasval(a__ptr, PyClassInstance_v(PyClass_module_0A())) &*&
        pyobj_hasval(b__ptr, PyLong_v(?b__val)) &*&
        PRED_pred2(a__ptr, a__val, b__ptr, b__val);

        ensures PyExc(none, none) &*&
        pyobj_hasval(args, PyTuple_v(cons(pair(a__ptr, PyClass_t(PyClass_module_0A())), cons(pair(b__ptr, PyLong_t), nil)))) &*&
        pyobj_hasval(a__ptr, PyClassInstance_v(PyClass_module_0A())) &*&
        pyobj_hasval(b__ptr, PyLong_v(b__val)) &*&
        pyobj_hasval(result, PyLong_v(?result__val)) &*&
        PRED_pred3(a__ptr, a__val, b__ptr, b__val, result, result__val);
        """
        Requires(pred2(a, b))
        Ensures(pred3(a, b, Result()))
