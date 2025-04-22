from fractions import Fraction
import nagini_translation.native.vf.vf as vf
from nagini_translation.native.vf.nag import *
from typing import TypeVar, Tuple, Type, List
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


class PyList(PyObj_v):

    def __init__(self, t: PyObj_t):
        __PyObj_t = PyObj_t("PyList_t($)")
        self.t = t

    def __str__(self):
        return "PyList_v("+str(self.t)+")"

    def PyObj_t(self) -> PyObj_t:
        return self.__PyObj_t.replace("$", str(self.t))


class PyLong(PyObj_v):
    __PyObj_t = PyObj_t("PyLong_t")

    def __init__(self, value: int):
        self.value = value

    def __str__(self):
        return "PyLong_v("+str(self.value)+")"

    def PyObj_t(self) -> PyObj_t:
        return PyLong.__PyObj_t


class PyFloat(PyObj_v):
    __PyObj_t = PyObj_t("PyFloat_t")

    def __init__(self, value: float):
        self.value = value

    def __str__(self):
        return "PyFloat_v("+str(self.value)+")"

    def PyObj_t(self) -> PyObj_t:
        return PyFloat.__PyObj_t


class PyBool(PyObj_v):
    __PyObj_t = PyObj_t("PyBool_t")

    def __init__(self, value: bool):
        self.value = value

    def __str__(self):
        return "PyBool_v("+str(self.value)+")"

    def PyObj_t(self) -> PyObj_t:
        return PyBool.__PyObj_t


class PyClass(vf.Inductive, ABC):
    def __init__(self, name: str, type_vars: List[PyObj_t]):
        self.name = name
        self.type_vars = type_vars

    def __str__(self):
        return "PyClass_"+self.name+"("+", ".join(map(str, self.type_vars))+")"


class PyUnicode(PyObj_v):
    __PyObj_t = PyObj_t("PyUnicode_t")

    def __init__(self, value: str):
        self.value = value

    def __str__(self):
        return "PyUnicode_v("+str(self.value)+")"

    def PyObj_t(self) -> PyObj_t:
        return PyUnicode.__PyObj_t


class PyNone(PyObj_v):
    __PyObj_t = PyObj_t("PyNone_t")

    def __init__(self):
        pass

    def __str__(self):
        return "PyNone_v"

    def PyObj_t(self) -> PyObj_t:
        return PyNone.__PyObj_t


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
        super().__init__("pyobj_hasval", ptr, value, frac=frac)
#    def __str__(self):
#        return "pyobj_hasval("+str(self.ptr)+", "+str(self.value)+")"


class PyObj_HasContent(vf.PredicateFact):
    def __init__(self, ptr: vf.Expr[PyObjPtr], value: vf.Expr[vf.List[PyObj_v]], frac=Fraction(1)):
        super().__init__("pyobj_hascontent", ptr, value, frac=frac)


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
