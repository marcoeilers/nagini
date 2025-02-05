import nagini_translation.native.vf.standard as vf


class PyObj_v(vf.expr):
    pass


class PyLong(PyObj_v):
    def __init__(self, value: int):
        self.value = value


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
    def __init__(self, name: str, type: PyClass):
        self.name = name
        self.type = type

    def __str__(self):
        return "PyClassInstance_v(\""+self.name+"\", "+str(self.type)+")"


class PyObj_HasVal(vf.pred):
    def __init__(self, p: vf.ptr, o: PyObj_v):
        super().__init__("pyobj_hasval")
        self.ptr = p
        self.pyobj = o
    def __str__(self):
        return self.name + "(" + str(self.ptr) + ", " + str(self.pyobj) + ")"


class PyObj_HasAttr(vf.pred):
    def __init__(self, p1: vf.ptr, attr_name: str, p2: vf.ptr):
        super().__init__("pyobj_hasattr")
        self.ptr = p1
        self.attr_name = attr_name
        self.attr_val = p2
    def __str__(self):
        return self.name + "(" + str(self.ptr) + ", \"" + self.attr_name + "\", " + str(self.attr_val) + ")"


class PyObj_HasContent(vf.pred):
    def __init__(self, p: vf.ptr, o: PyObj_v):
        super().__init__("pyobj_hascontent")
        self.ptr = p
        self.pyobj = o
    def __str__(self):
        return self.name + "(" + str(self.ptr) + ", " + str(self.pyobj) + ")"


class PyObj_t(vf.expr):
    pass
