from constants import CONTRACT_FUNCS, PRIMITIVES, LITERALS
from util import UnsupportedException
from typing import TypeVar, List, Tuple, Optional, Dict
from typeinfo import TypeInfo
import ast
import collections
import mypy

class PythonScope:

    def containsName(self, name):
        result = name in self.silNames
        if self.superscope is not None:
            result = result or self.superscope.containsName(name)
        return result

    def getName(self, name):
        if self.containsName(name):
            counter = 0
            newname = name + '_' + str(counter)
            while self.containsName(newname):
                counter = counter + 1
                newname = name + '_' + str(counter)
            self.silNames.append(newname)
            return newname
        else:
            self.silNames.append(name)
            return name

    def getScopePrefix(self):
        if self.superscope is None:
            return [self.name]
        else:
            return self.superscope.getScopePrefix() + [self.name]

    def getProgram(self):
        if self.superscope is not None:
            return self.superscope.getProgram()
        else:
            return self

class PythonProgram(PythonScope):
    def __init__(self, types):
        self.classes = {}
        self.functions = {}
        self.methods = {}
        self.globalVars = {}
        self.silNames = []
        self.superscope = None
        self.types = types
        for primitive in PRIMITIVES:
            self.classes[primitive] = PythonClass(primitive, self)

    def process(self, translator):
        for clazz in self.classes:
            self.classes[clazz].process(self.getName(clazz), translator)
        for function in self.functions:
            self.functions[function].process(self.getName(function), translator)
        for method in self.methods:
            self.methods[method].process(self.getName(method), translator)

    def getScopePrefix(self):
        return []

    def getFuncOrMethod(self, name):
        if name in self.functions:
            return self.functions[name]
        else:
            return self.methods[name]


class PythonNode:
    def __init__(self, name, node = None):
        self.node = node
        self.name = name
        self.silName = None

class PythonClass(PythonNode, PythonScope):

    def __init__(self, name, superscope, node = None, superclass = None):
        super().__init__(name, node)
        if name == 'None' or name == None:
            raise Exception()
        self.superclass = superclass
        self.functions = {}
        self.methods = {}
        self.fields = {}
        self.type = None # infer, domain type
        self.superscope = superscope
        self.silNames = []

    def addField(self, name, node, type):
        if name in self.fields:
            field = self.fields[name]
            print(field.type)
            print(type)
            assert field.type == type
        else:
            print("creating ffield with type")
            print(type)
            field = PythonField(name, node, type, self)
            self.fields[name] = field
        return field

    def getField(self, name):
        if name in self.fields:
            return self.fields[name]
        elif self.superclass is not None:
            return self.superclass.getField(name)
        else:
            return None

    def getMethod(self, name):
        if name in self.methods:
            return self.methods[name]
        elif self.superclass is not None:
            return self.superclass.getMethod(name)
        else:
            return None

    def getFunction(self, name):
        if name in self.functions:
            return self.functions[name]
        elif self.superclass is not None:
            return self.superclass.getFunction(name)
        else:
            return None

    def process(self, silName, translator):
        print("process class")
        print(silName)
        self.silName = silName
        for function in self.functions:
            self.functions[function].process(self.getName(function), translator)
        for method in self.methods:
            self.methods[method].process(self.getName(method), translator)
        for field in self.fields:
            self.fields[field].process(self.getName(field))



class PythonMethod(PythonNode, PythonScope):

    def __init__(self, name, node, clazz, superscope, pure):
        super().__init__(name, node=node)
        if clazz is not None:
            if not isinstance(clazz, PythonClass):
                raise Exception(clazz)
        self.clazz = clazz
        self.overrides = None # infer
        self.locals = {} # direct
        self.args = collections.OrderedDict() # direct
        self.type = None # infer
        self.declaredExceptions = {} # direct
        self.precondition = []
        self.postcondition = []
        self.handlers = [] # direct
        self.superscope = superscope
        self.pure = pure
        self.silNames = []

    def getHandlers(self, stmt) -> Dict['ExceptionType', Tuple['Node', str]]:
        raise UnsupportedException(None)

    def process(self, silName, translator):
        print("process method")
        print(silName)
        self.silName = silName
        functype = self.getProgram().types.getfunctype(self.getScopePrefix())
        if isinstance(functype, mypy.types.Void):
            self.type = None
        elif isinstance(functype, mypy.types.Instance):
            self.type = self.getProgram().classes[functype.type.name()]
        else:
            raise UnsupportedException(functype)
        if self.clazz is not None:
            self.overrides = self.clazz.getFunction(self.name) if self.pure else self.clazz.getMethod(self.name)
        for arg in self.args:
            self.args[arg].process(self.getName(arg), translator)
        for local in self.locals:
            self.locals[local].process(self.getName(local), translator)

    def getVariable(self, name):
        if name in self.locals:
            return self.locals[name]
        elif name in self.args:
            return self.args[name]
        else:
            return self.getProgram().globalVars[name]

class PythonExceptionHandler(PythonNode):

    def __init__(self, node, type, tryname, handlername, body, protectedRegion):
        super().__init__(handlername, node=node)
        self.tryname = tryname
        self.body = body
        self.region = protectedRegion
        self.type = type

class PythonVar(PythonNode):
    def __init__(self, name, node, clazz):
        super().__init__(name, node)
        self.clazz = clazz
        self.writes = []
        self.reads = []

    def process(self, silName, translator):
        self.silName = silName
        self.decl = translator.translate_pythonvar_decl(self)
        self.ref = translator.translate_pythonvar_ref(self)

class PythonField(PythonNode):

    def __init__(self, name, node, type, clazz):
        super().__init__(name, node)
        self.clazz = clazz
        self.inherited = None # infer
        self.type = type
        self.reads = [] # direct
        self.writes = [] # direct

    def process(self, silName):
        self.silName = silName
        if not self.isMangled():
            if self.clazz.superclass is not None:
                self.inherited = self.clazz.superclass.getField(self.name)

    def isMangled(self):
        return self.name.startswith('__') and not self.name.endswith('__')


class Analyzer:
    """
    Walks through the Python AST and collects the structures to be translated
    """

    def __init__(self, jvm, viperast, types: TypeInfo):
        self.viper = viperast
        self.java = jvm.java
        self.scala = jvm.scala
        self.viper = jvm.viper
        self.types = types
        self.program = PythonProgram(types)
        self.currentClass = None
        self.currentFunction = None

    def process(self, translator):
        self.program.process(translator)

    def visit_default(self, node: ast.AST):
        print('default ' + node.__class__.__name__)
        for field in node._fields:
            fieldval = getattr(node, field)
            if isinstance(fieldval, ast.AST):
                self.visit(fieldval, node)
            elif isinstance(fieldval, list):
                for item in fieldval:
                    self.visit(item, node)
            #else:
            #    print('Unknown: ' + str(fieldval))

    def visit(self, childnode, parent):
        childnode._parent = parent
        method = 'visit_' + childnode.__class__.__name__
        visitor = getattr(self, method, self.visit_default)
        visitor(childnode)

    def getClass(self, name):
        if name in self.program.classes:
            clazz = self.program.classes[name]
        else:
            clazz = PythonClass(name, self.program)
            self.program.classes[name] = clazz
        return clazz

    def visit_ClassDef(self, node):
        assert self.currentClass is None
        assert self.currentFunction is None
        name = node.name
        if not isinstance(name, str):
            raise Exception(name)
        clazz = self.getClass(name)
        if len(node.bases) > 1:
            raise UnsupportedException(node)
        if len(node.bases) == 1:
            clazz.superclass = self.getClass(node.bases[0].id)
        self.currentClass = clazz
        for member in node.body:
            self.visit(member, node)
        self.currentClass = None


    def visit_FunctionDef(self, node):
        assert self.currentFunction is None
        name = node.name
        if not isinstance(name, str):
            raise Exception(name)
        if self.currentClass is None:
            scopecontainer = self.program
        else:
            scopecontainer = self.currentClass
        if self.is_pure(node):
            container = scopecontainer.functions
        else:
            container = scopecontainer.methods
        if name in container:
            func = container[name]
        else:
            func = PythonMethod(name, node, self.currentClass, scopecontainer, self.is_pure(node))
            container[name] = func
        self.currentFunction = func
        self.visit_default(node)
        self.currentFunction = None

    def visit_arg(self, node):
        assert self.currentFunction is not None
        self.currentFunction.args[node.arg] = PythonVar(node.arg, node, self.typeOf(node))

    def trackReadOrWrite(self, node, varOrField):
        if varOrField is not None:
            if isinstance(node.ctx, ast.Load):
                varOrField.reads.append(node)
            elif isinstance(node.ctx, ast.Store):
                varOrField.writes.append(node)
            else:
                raise UnsupportedException(node)

    def visit_Call(self, node):
        if node.func.id in CONTRACT_FUNCS:
            assert self.currentFunction is not None
            if node.func.id == 'Requires':
                self.currentFunction.precondition.append(node.args[0])
            elif node.func.id == 'Ensures':
                self.currentFunction.postcondition.append(node.args[0])
            elif node.func.id == 'Exsures':
                exception = node.args[0].id
                assert exception not in self.currentFunction.declaredExceptions
                self.currentFunction.declaredExceptions[exception] = node.args[1]
        self.visit_default(node)


    def visit_Name(self, node):
        if node.id in LITERALS:
            return
        if isinstance(node._parent, ast.Call):
            return
        if isinstance(node._parent, ast.arg):
            if node._parent.annotation is node:
                return
        if isinstance(node._parent, ast.FunctionDef):
            if node._parent.returns is node:
                return
            if node in node._parent.decorator_list:
                return
        # could be global declaration or global reference or static member
        # or local var or func arg
        if self.currentFunction is None:
            # this is global in some way
            if self.currentClass is None:
               # global var
                if isinstance(node.ctx, ast.Store):
                    var = PythonVar(node.id, node)
                    self.program.globalVars[node.id] = var
                var = self.program.globalVars[node.id]
                self.trackReadOrWrite(node, var)
            else:
                # static field
                print(node.id)
                raise UnsupportedException(node)
        # this is a global or a local var or a static field
        if not node.id in self.program.globalVars:
            # must be local for static field
            if self.currentFunction is None:
                # must be static field
                raise UnsupportedException(node)
            else:
                # must be local var?
                var = None
                if node.id in self.currentFunction.locals:
                    var = self.currentFunction.locals[node.id]
                    print("++++")
                elif node.id in self.currentFunction.args:
                    pass
                else:
                    var = PythonVar(node.id, node, self.typeOf(node))
                    self.currentFunction.locals[node.id] = var
                print(var)
                self.trackReadOrWrite(node, var)

    def visit_Attribute(self, node):
        self.visit_default(node)
        receiver = self.typeOf(node.value)
        field = receiver.addField(node.attr, node, self.typeOf(node))
        self.trackReadOrWrite(node, field)

    def typeOf(self, node):
        if isinstance(node, ast.Name):
            if node.id in LITERALS:
                raise UnsupportedException(node)
            context = []
            if self.currentClass is not None:
                context.append(self.currentClass.name)
            if self.currentFunction is not None:
                context.append(self.currentFunction.name)
            type = self.types.gettype(context, node.id)
            if isinstance(type.name, str):
                print(node.id)
                print('name string ' + type.__class__.__name__)
                raise Exception()
            else:
                print('name not string ' + type.__class__.__name__)
            return self.getClass(type.name())
        elif isinstance(node, ast.Attribute):
            receiver = self.typeOf(node.value)
            context = [receiver.name]
            print(context)
            print(node.attr)
            type = self.types.gettype(context, node.attr)
            if isinstance(type.name, str):
                raise Exception(type.name)
            return self.getClass(type.name())
        elif isinstance(node, ast.arg):
            context = []
            if self.currentClass is not None:
                context.append(self.currentClass.name)
            context.append(self.currentFunction.name)
            type = self.types.gettype(context, node.arg)
            return self.getClass(type.name())
        else:
            raise UnsupportedException(node)

    def visit_Try(self, node):
        assert self.currentFunction is not None
        self.visit_default(node)
        tryname = self.currentFunction.getName('try')
        for handler in node.handlers:
            handlername = self.currentFunction.getName('handler' + type.name)
            pyhndlr = PythonExceptionHandler(handler, type, tryname, handlername, handler.body, node.body)
            self.currentFunction.handlers.append(pyhndlr)

    def is_pure(self, func) -> bool:
        return (len(func.decorator_list) == 1
                and func.decorator_list[0].id == 'Pure')