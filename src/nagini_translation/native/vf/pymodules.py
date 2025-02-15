from nagini_translation.native.vf.standard.fact import PredicateFact
from nagini_translation.native.vf.standard.value import Value
from nagini_translation.native.vf.standard.literal import Ptr, Char
from nagini_translation.native.vf.standard.inductive import List, Pair, Inductive
from nagini_translation.native.vf.standard.expr import Expr
from nagini_translation.native.vf.standard.valueloc import ValueLocation
from typing import TypeVar, Tuple, Type
from abc import ABC

ValueT = TypeVar("ValueT", bound="Value")


class PyObj_v(Inductive, ABC):
    pass


class PyLong(PyObj_v):
    def __init__(self, value: int):
        self.value = value

    def __str__(self):
        return "PyLong_v("+str(self.value)+")"


class PyClass(Inductive, ABC):
    def __init__(self, name: str, parent: "PyClass"):
        self.name = name
        self.parent = parent

    def __str__(self):
        return "PyClass(\""+self.name+"\", "+(str(self.parent) if self.parent != None else "ObjectType")+")"


class PyClassInstance(PyObj_v):
    def __init__(self, type: PyClass):
        self.type = type

    def __str__(self):
        return "PyClassInstance_v("+str(self.type)+")"


class PyObj_t(Inductive, ABC):
    # TODO: review this declaration: is really what we want?
    pass


class PyClass_t(PyObj_t):
    def __init__(self, type: PyClass):
        self.type = type

    def __str__(self):
        return "PyClass_t("+str(self.type)+")"


class PyObjPtr(Ptr):
    pass


class PyObj_HasValue(PredicateFact):
    def __init__(self, ptr: Expr[PyObjPtr], value: Expr[PyObj_v]):
        self.ptrLoc = ValueLocation[PyObjPtr]()
        self.ptrLoc.setContent(ptr)
        self.valueLoc = ValueLocation[PyObj_v]()
        self.valueLoc.setContent(value)

    def __str__(self):
        return "pyobj_hasvalue("+str(self.ptrLoc.getContent())+", "+str(self.valueLoc.getContent())+")"


class PyObj_HasAttr(PredicateFact):
    def __init__(self, obj: Expr[PyObjPtr], attrName: Expr[Char], attrValue: Expr[PyObjPtr]):
        self.objLoc = ValueLocation[PyObjPtr]()
        self.objLoc.setContent(obj)
        self.attrNameLoc = ValueLocation[Char]()
        self.attrNameLoc.setContent(attrName)
        self.attrValueLoc = ValueLocation[PyObj_v]()
        self.attrValueLoc.setContent(attrValue)

    def __str__(self):
        return "pyobj_hasattr("+str(self.objLoc.getContent())+", "+str(self.attrNameLoc.getContent())+", "+str(self.attrValueLoc.getContent())+")"


class PyTuple(PyObj_v):
    # TODO: a pointer is represented as a an expression here, but could it be refined as a val? decude whe we'll define the class ptr
    def __init__(self, items: List[Pair[PyObjPtr, PyObj_t]]):
        pass
        # self.items =

    def __str__(self):
        return "PyTuple_v("+(",\n\t".join(map(str, self.items)))+")"
