import nagini_translation.native.vf.standard as vf
from abc import ABC, abstractmethod


class PyObj_v(vf.expr, ABC):
    pass


class PyLong(PyObj_v):
    def __init__(self, value: int):
        self.value = value
    def __str__(self):
        return "PyLong_v("+str(self.value)+")"

class PyTuple(PyObj_v):
    def __init__(self, items: list[]):
        self.items = items
    def __str__(self):
        return "PyTuple_v("+", ".join(map(str, self.items))+")"
class PyClass():
    def __init__(self, name: str, parent: "PyClass" = None):
        self.name = name
        self.parent = parent

    def __init__(self, name: str):
        self.name = name
        self.parent = None

    def __str__(self):
        return "PyClass_v(\""+self.name+"\", "+(str(self.parent) if self.parent != None else "ObjectType")+")"

class PyClassInstance(PyObj_v):
    def __init__(self, type: PyClass):
        self.type = type
    def __str__(self):
        return "PyClassInstance_v("+str(self.type)+")"

class PyObj_HasVal(vf.pred):
    def __init__(self, val: vf.val_pattern, obj: PyObj_v):
        self.val = val
        self.obj = obj

    def __str__(self):
        return "pyobj_hasval("+str(self.val)+", "+str(self.obj)+")"
