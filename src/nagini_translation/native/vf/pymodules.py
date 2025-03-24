from fractions import Fraction
import nagini_translation.native.vf.vf as vf
from typing import TypeVar, Tuple, Type
from abc import ABC, abstractmethod

ValueT = TypeVar("ValueT", bound="vf.Value")


class PyObj_t(vf.Inductive, ABC):
    def __init__(self, label: str):
        self.label = label

    def __str__(self):
        return self.label


class PyObj_v(vf.Inductive, ABC):
    @abstractmethod
    def PyObj_t(self) -> PyObj_t:
        pass


class PyLong(PyObj_v):
    __PyObj_t = PyObj_t("PyLong_t")

    def __init__(self, value: int):
        self.value = value

    def __str__(self):
        return "PyLong_v("+str(self.value)+")"

    def PyObj_t(self) -> PyObj_t:
        return PyLong.__PyObj_t


class PyClass(vf.Inductive, ABC):
    def __init__(self, name: str):
        self.name = name
    def __str__(self):
        return "PyClass_"+self.name+""
class PyClass_List(PyClass):
    def __init__(self):
        super().__init__("List")

class PyClass_t(PyObj_t):
    def __init__(self, type: PyClass):
        self.type = type

    def __str__(self):
        return "PyClass_t("+str(self.type)+")"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, PyClass_t) and self.type == other.type


class PyClassInstance(PyObj_v):
    def __init__(self, type: PyClass):
        self.type = type

    def __str__(self):
        return "PyClassInstance_v("+str(self.type)+")"

    def PyObj_t(self) -> PyObj_t:
        return PyClass_t(self.type)


class PyObjPtr(vf.Ptr):
    pass


class PyObj_HasVal(vf.PredicateFact):
    def __init__(self, ptr: vf.Expr[PyObjPtr], value: vf.Expr[PyObj_v], frac=Fraction(1)):
        super().__init__("pyobj_hasvalue", ptr, value, frac=frac)
#    def __str__(self):
#        return "pyobj_hasvalue("+str(self.ptr)+", "+str(self.value)+")"


class PyObj_HasAttr(vf.PredicateFact):
    def __init__(self, obj: vf.Expr[PyObjPtr], attrName: str, attrValue: vf.Expr[PyObjPtr], frac=Fraction(1)):
        super().__init__("pyobj_hasattr", obj, "\""+attrName+"\"", attrValue, frac=frac)

class PyObj_MayCreate(vf.PredicateFact):
    def __init__(self, obj: vf.Expr[PyObjPtr], attrName: str, frac=Fraction(1)):
       super().__init__("pyobj_maycreateattr", obj, "\""+attrName+"\"", frac=frac)

class PyObj_MaySet(vf.PredicateFact):
    def __init__(self, obj: vf.Expr[PyObjPtr], attrName: str, attrValue: vf.Option[PyObjPtr], frac=Fraction(1)):
        super().__init__("pyobj_maysetattr", obj, "\""+attrName+"\"", attrValue, frac=frac)

class PyTuple(PyObj_v):
    # TODO: a pointer is represented as a an expression here, but could it be refined as a val? decude whe we'll define the class ptr
    def __init__(self, items: vf.List[vf.Pair[PyObjPtr, PyObj_t]]):
        self.items = items

    def PyObj_t(self) -> PyObj_t:
        return None

    def __str__(self):
        return "PyTuple_v("+str(self.items)+")"


class PyTuple_t(PyObj_t):
    def __init__(self, items: vf.List[PyObj_t]):
        self.items = items

    def __str__(self):
        return "PyTuple_t("+str(self.items)+")"
