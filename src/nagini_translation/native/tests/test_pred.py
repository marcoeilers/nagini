"""
fixpoint PyClass PyClass_ObjectType(){
                return ObjectType;
}
fixpoint PyClass PyClass_module_0A(){
                return PyClass("module_0A", PyClass_ObjectType);
}
predicate PRED_pred1() = true;
predicate PRED_pred2(x__ptr, x__val, f__ptr, f__val) = pyobj_hasattr(x__ptr, "a", ?x_DOT_a__ptr) &*&
pyobj_hasvalue(x_DOT_a__ptr, PyLong_v(?x_DOT_a__val)) &*&
pyobj_maycreateattr(x__ptr, "b") &*&
pyobj_maysetattr(x__ptr, "c", _) &*&
(x_DOT_a__val == 14);
predicate PRED_pred3(x__ptr, x__val, y__ptr, y__val, z__ptr, z__val) = pyobj_hasattr(x__ptr, "a", ?x_DOT_a__ptr) &*&
pyobj_hasvalue(x_DOT_a__ptr, PyLong_v(?x_DOT_a__val)) &*&
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
        requires pyobj_hasvalue(args, PyTuple_v(nil)) &*&
        true;

        ensures pyobj_hasvalue(args, PyTuple_v(nil)) &*&
        pyobj_hasvalue(result, PyLong_v(?result__val)) &*&
        true;
        """
        Requires(True)
        Ensures(True)


@Native
@ContractOnly
def test2(a: A, b: int) -> int:
        """
        requires pyobj_hasvalue(args, PyTuple_v(cons(pair(?a__ptr, PyClass_t(PyClass_module_0A)), cons(pair(?b__ptr, PyLong_t), nil)))) &*&
        pyobj_hasvalue(a__ptr, PyClassInstance_v(PyClass_module_0A)) &*&
        pyobj_hasvalue(b__ptr, PyLong_v(?b__val)) &*&
        PRED_pred2(a__ptr, a__val, b__ptr, b__val);

        ensures pyobj_hasvalue(args, PyTuple_v(cons(pair(a__ptr, PyClass_t(PyClass_module_0A)), cons(pair(b__ptr, PyLong_t), nil)))) &*&
        pyobj_hasvalue(a__ptr, PyClassInstance_v(PyClass_module_0A)) &*&
        pyobj_hasvalue(b__ptr, PyLong_v(b__val)) &*&
        pyobj_hasvalue(result, PyLong_v(?result__val)) &*&
        PRED_pred3(a__ptr, a__val, b__ptr, b__val, result, result__val);
        """
        Requires(pred2(a, b))
        Ensures(pred3(a, b, Result()))
