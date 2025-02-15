from nagini_translation.native.vf.standard.pred import Pred
from nagini_translation.native.vf.standard.value import ValueT, Value
from nagini_translation.native.vf.standard.literal import Ptr, Char
from nagini_translation.native.vf.standard.inductive import List, Pair, Inductive
from nagini_translation.native.vf.standard.expr import Expr
from typing import TypeVar, Tuple, Type
from abc import ABC


class PyObj_v(Inductive, ABC):
    pass
class PyLong(PyObj_v):
    def __init__(self, value: int):
        self.value = value

    def __str__(self):
        return "PyLong_v("+str(self.value)+")"
class PyObj_t(Inductive, Type[PyObj_v]):
    #TODO: review this declaration: is really what we want?
    pass
class PyObj_Ptr(Ptr):
    pass
PyObjPtrT = TypeVar('PyObjPtrT', bound=PyObj_Ptr)

PyObj_HasVal = Pred[Tuple[PyObjPtrT, ValueT]]("pyobj_hasval")
PyObj_HasAttr = Pred[Tuple[PyObjPtrT, List[Char], PyObjPtrT]]("pyobj_hasattr")



class PyTuple(PyObj_v):
    # TODO: a pointer is represented as a an expression here, but could it be refined as a val? decude whe we'll define the class ptr
    def __init__(self, items: List[Pair[Expr, PyObj_t]]):
        self.items = items

    def __str__(self):
        return "PyTuple_v("+(",\n\t".join(map(str, self.items)))+")"


class PyClass(Inductive, ABC):
    def __init__(self, name: str, parent: "PyClass"):
        self.name = name
        self.parent = parent

    def __str__(self):
        return "PyClass(\""+self.name+"\", "+(str(self.parent) if self.parent != None else "ObjectType")+")"


class PyClass_t(PyObj_t):
    def __init__(self, type: PyClass):
        self.type = type

    def __str__(self):
        return "PyClass_t("+str(self.type)+")"


class PyClassInstance(PyObj_v):
    def __init__(self, type: PyClass):
        self.type = type

    def __str__(self):
        return "PyClassInstance_v("+str(self.type)+")"