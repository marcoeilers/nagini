import nagini_translation.native.vf.vf as vf
from typing import TypeVar, Tuple, Type
from abc import ABC

ValueT = TypeVar("ValueT", bound="vf.Value")


class PyObj_v(vf.Inductive, ABC):
    pass


class PyLong(PyObj_v):
    def __init__(self, value: int):
        self.value = value

    def __str__(self):
        return "PyLong_v("+str(self.value)+")"


class PyClass(vf.Inductive, ABC):
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


class PyObj_t(vf.Inductive, ABC):
    pass


class PyClass_t(PyObj_t):
    def __init__(self, type: PyClass):
        self.type = type

    def __str__(self):
        return "PyClass_t("+str(self.type)+")"


class PyObjPtr(vf.Ptr):
    pass


class PyObj_HasValue(vf.PredicateFact):
    def __init__(self, ptr: vf.Expr[PyObjPtr], value: vf.Expr[PyObj_v]):
        self.ptrLoc = vf.ValueLocation[PyObjPtr]()
        self.ptrLoc.setContent(ptr)
        self.valueLoc = vf.ValueLocation[PyObj_v]()
        self.valueLoc.setContent(value)

    def __str__(self):
        return "pyobj_hasvalue("+str(self.ptrLoc.getContent())+", "+str(self.valueLoc.getContent())+")"


class PyObj_HasAttr(vf.PredicateFact):
    def __init__(self, obj: vf.Expr[PyObjPtr], attrName: vf.Expr[vf.Char], attrValue: vf.Expr[PyObjPtr]):
        self.objLoc = vf.ValueLocation[PyObjPtr]()
        self.objLoc.setContent(obj)
        self.attrNameLoc = vf.ValueLocation[vf.Char]()
        self.attrNameLoc.setContent(attrName)
        self.attrValueLoc = vf.ValueLocation[PyObj_v]()
        self.attrValueLoc.setContent(attrValue)

    def __str__(self):
        return "pyobj_hasattr("+str(self.objLoc.getContent())+", "+str(self.attrNameLoc.getContent())+", "+str(self.attrValueLoc.getContent())+")"


class PyTuple(PyObj_v):
    # TODO: a pointer is represented as a an expression here, but could it be refined as a val? decude whe we'll define the class ptr
    def __init__(self, items: vf.List[vf.Pair[PyObjPtr, PyObj_t]]):
        pass
        # self.items =

    def __str__(self):
        return "PyTuple_v("+(",\n\t".join(map(str, self.items)))+")"
