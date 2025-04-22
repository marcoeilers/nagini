import nagini_translation.native.vf.vf as vf
from abc import ABC
import ast


class AccessType(ABC):
    pass


# TODO. one day, recall to use this
class LeafAccessType(AccessType, ABC):
    pass


class PtrAccess(AccessType):
    def __str__(self):
        return "__ptr"

    def __repr__(self):
        return ":ptr"


class CtntAccess(AccessType):
    def __init__(self, value: AccessType):
        self.value = value

    def __str__(self):
        return "__content"+str(self.value)

    def __repr__(self):
        return "[]"+repr(self.value) if isinstance(self.value, AccessType) else str(self.value)


class ValAccess(AccessType):
    def __str__(self):
        return "__val"

    def __repr__(self):
        return ":val"


class TupleSbscAccess(AccessType):
    def __init__(self, index: ast.Expr, value: AccessType):
        self.index = index
        self.value = value

    def __str__(self):
        if (isinstance(self.value, LeafAccessType)):
            return str(self.value)+"_AT"+str(self.index)
        else:
            return "_AT"+str(self.index)+str(self.value)

    def __repr__(self):
        if (isinstance(self.value, LeafAccessType)):
            return repr(self.value)+"["+repr(self.index)+"]"
        else:
            return "["+str(self.index)+"]"+repr(self.value)


class AttrAccess(AccessType):
    def __init__(self, attr: str, value: AccessType):
        self.attr = attr
        self.value = value

    def __str__(self):
        if (isinstance(self.value, LeafAccessType)):
            return str(self.value)+"_DOT_"+str(self.attr)
        else:
            return "_DOT_"+str(self.attr)+str(self.value)

    def __repr__(self):
        if (isinstance(self.value, LeafAccessType)):
            return repr(self.value)+"."+repr(self.attr)
        else:
            return "."+str(self.attr)+repr(self.value)


class py2vf_context:
    def __init__(self, parent: "py2vf_context" = None, old: "py2vf_context" = None, prefix: str = ""):
        self.context = dict()
        self.parent = parent
        if (prefix is None):
            self._prefix = ""
        else:
            self._prefix = prefix
        self.old = old

    def getprefix(self):
        return self._prefix
    
    def setprefix(self, prefix: str):
        self._prefix = prefix

    def __getloc(self, key: ast.Expr, AccessType: AccessType):
        if (isinstance(key, ast.Name)):
            loc = key.id + repr(AccessType)
            return (loc, key.id)
        elif (isinstance(key, ast.Call) and key.func.id == "Result" and key.args == []):
            loc = "Result()"+repr(AccessType)
            return (loc, "result")
        else:
            raise NotImplementedError("Unsupported expression key")

    def setExpr(self, key: ast.Expr, AccessType: AccessType, value: vf.Value):
        loc, key = self.__getloc(key, AccessType)
        self[loc] = value

    def getExpr(self, key: ast.Expr, AccessType: AccessType, useonly: bool = False):
        loc, keystr = self.__getloc(key, AccessType)
        theval = self[loc]
        if (theval == None and not useonly):
            self[loc] = vf.NamedValue(self._prefix+keystr+str(AccessType))
            return vf.NameDefExpr(self[loc])
        else:
            if theval != None:
                return vf.NameUseExpr(theval)
            else:
                #TODO: once finished, remove the return none
                return None
                raise NotImplementedError("Expression cannot be translated into a symbol")

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
