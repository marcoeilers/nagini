import nagini_translation.native.vf.standard as vf
from abc import ABC, abstractmethod


class PyObj_v(vf.expr, ABC):
    pass
class PyObj_t(vf.expr):
    def __init__(self, type:str):
        self.type = type
    def __str__(self):
        return self.type

class PyObjPtr(vf.VFVal):
    pass


class PyLong(PyObj_v):
    def __init__(self, value: int):
        self.value = value

    def __str__(self):
        return "PyLong_v("+str(self.value)+")"


class PyTuple(PyObj_v):
    # TODO: a pointer is represented as a an expression here, but could it be refined as a val? decude whe we'll define the class ptr
    def __init__(self, items: list[vf.Pair[vf.expr, PyObj_t]]):
        self.items = items

    def __str__(self):
        return "PyTuple_v("+(", ".join(map(str, self.items)))+")"


class PyClass():
    def __init__(self, name: str, parent: "PyClass" = None):
        self.name = name
        self.parent = parent

    def __str__(self):
        return "PyClass_v(\""+self.name+"\", "+(str(self.parent) if self.parent != None else "ObjectType")+")"


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


class pyobj_hasval(vf.pred):
    # TODO: refine the type to a pointer instead of any expression
    def __init__(self, ptr: vf.expr, obj: PyObj_v):
        self.ptr = ptr
        self.obj = obj

    def __str__(self):
        return "pyobj_hasval("+str(self.ptr)+", "+str(self.obj)+")"
