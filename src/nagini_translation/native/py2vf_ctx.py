import nagini_translation.native.vf.vf as vf
from abc import ABC
import ast


class ValueAccess(ABC):
    pass


class LeafValueAccess(ValueAccess, ABC):
    pass


class PtrAccess(ValueAccess):
    def __str__(self):
        return "__ptr"

    def __repr__(self):
        return ":ptr"


class ValAccess(ValueAccess):
    def __str__(self):
        return "__val"

    def __repr__(self):
        return ":val"


class TupleSubscriptAccess(ValueAccess):
    def __init__(self, index: ast.Expr, value: ValueAccess):
        self.index = index
        self.value = value

    def __str__(self):
        if (isinstance(self.value, LeafValueAccess)):
            return str(self.value)+"_AT"+str(self.index)
        else:
            return "_AT"+str(self.index)+str(self.value)

    def __repr__(self):
        if (isinstance(self.value, LeafValueAccess)):
            return repr(self.value)+"["+str(self.index)+"]"
        else:
            return "["+str(self.index)+"]"+repr(self.value)


class AttrAccess(ValueAccess):
    def __init__(self, attr: str, value: ValueAccess):
        self.attr = attr
        self.value = value

    def __str__(self):
        if (isinstance(self.value, LeafValueAccess)):
            return str(self.value)+"_DOT_"+str(self.attr)
        else:
            return "_DOT_"+str(self.attr)+str(self.value)

    def __repr__(self):
        if (isinstance(self.value, LeafValueAccess)):
            return repr(self.value)+"."+str(self.attr)
        else:
            return "."+str(self.attr)+repr(self.value)


class py2vf_context:
    def __init__(self, parent: "py2vf_context" = None, prefix: str = ""):
        self.context = dict()
        self.parent = parent
        self.setup = []
        if (prefix is None):
            self._prefix = ""
        else:
            self._prefix = prefix

    def getprefix(self):
        return self._prefix

    def getExpr(self, key: str, ValueAccess: ValueAccess, useonly: bool = False):
        loc = key + repr(ValueAccess)
        theval = self[loc]
        if theval != None or useonly:
            return vf.NameUseExpr(theval)
        else:
            self[loc] = vf.NamedValue(self._prefix+key+str(ValueAccess))
            return vf.NameDefExpr(self[loc])

    def __getitem__(self, key: str):
        if key in self.context:
            return self.context[key]
        elif self.parent:
            return self.parent[key]
        else:
            # raise KeyError(key)
            return None

    def __setitem__(self, key: str, value: vf.Value):
        self.context[key] = value
