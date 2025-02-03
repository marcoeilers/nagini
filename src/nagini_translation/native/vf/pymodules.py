import nagini_translation.native.vf.standard as standard

class PyObj_v(standard.expr):
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


class PyObj_t(standard.expr):
    pass