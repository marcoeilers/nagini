import ast
import collections
import mypy

from constants import CONTRACT_WRAPPER_FUNCS, PRIMITIVES, LITERALS
from util import UnsupportedException
from typeinfo import TypeInfo
from typing import List, Optional


class PythonScope:
    def contains_name(self, name: str) -> bool:
        result = name in self.silnames
        if self.superscope is not None:
            result = result or self.superscope.contains_name(name)
        return result

    def get_fresh_name(self, name: str) -> str:
        if self.contains_name(name):
            counter = 0
            newname = name + '_' + str(counter)
            while self.contains_name(newname):
                counter = counter + 1
                newname = name + '_' + str(counter)
            self.silnames.append(newname)
            return newname
        else:
            self.silnames.append(name)
            return name

    def get_scope_prefix(self) -> List[str]:
        if self.superscope is None:
            return [self.name]
        else:
            return self.superscope.get_scope_prefix() + [self.name]

    def get_program(self) -> 'PythonProgram':
        if self.superscope is not None:
            return self.superscope.get_program()
        else:
            return self


class PythonProgram(PythonScope):
    def __init__(self, types: TypeInfo):
        self.classes = {}
        self.functions = {}
        self.methods = {}
        self.global_vars = {}
        self.silnames = []
        self.superscope = None
        self.types = types
        for primitive in PRIMITIVES:
            self.classes[primitive] = PythonClass(primitive, self)

    def process(self, translator: 'Translator') -> None:
        for clazz in self.classes:
            self.classes[clazz].process(self.get_fresh_name(clazz), translator)
        for function in self.functions:
            self.functions[function].process(self.get_fresh_name(function),
                                             translator)
        for method in self.methods:
            self.methods[method].process(self.get_fresh_name(method),
                                         translator)
        for var in self.global_vars:
            self.global_vars[var].process(self.get_fresh_name(var), translator)

    def get_scope_prefix(self) -> List[str]:
        return []

    def get_func_or_method(self, name: str) -> 'PythonMethod':
        if name in self.functions:
            return self.functions[name]
        else:
            return self.methods[name]


class PythonNode:
    def __init__(self, name: str, node=None):
        self.node = node
        self.name = name
        self.silname = None


class PythonClass(PythonNode, PythonScope):
    def __init__(self, name: str, superscope: PythonScope, node: ast.AST = None,
                 superclass: 'PythonClass' = None):
        super().__init__(name, node)
        if name == 'None' or name == None:
            raise Exception()
        self.superclass = superclass
        self.functions = collections.OrderedDict()
        self.methods = collections.OrderedDict()
        self.fields = collections.OrderedDict()
        self.type = None  # infer, domain type
        self.superscope = superscope
        self.silnames = []

    def add_field(self, name: str, node: ast.AST,
                  type: 'PythonClass') -> 'PythonField':
        if name in self.fields:
            field = self.fields[name]
            assert field.type == type
        else:
            field = PythonField(name, node, type, self)
            self.fields[name] = field
        return field

    def get_field(self, name: str) -> Optional['PythonField']:
        if name in self.fields:
            return self.fields[name]
        elif self.superclass is not None:
            return self.superclass.get_field(name)
        else:
            return None

    def get_method(self, name: str) -> Optional['PythonMethod']:
        if name in self.methods:
            return self.methods[name]
        elif self.superclass is not None:
            return self.superclass.get_method(name)
        else:
            return None

    def get_function(self, name: str) -> Optional['PythonMethod']:
        if name in self.functions:
            return self.functions[name]
        elif self.superclass is not None:
            return self.superclass.get_function(name)
        else:
            return None

    def get_func_or_method(self, name: str) -> Optional['PythonMethod']:
        if self.get_function(name) is not None:
            return self.get_function(name)
        else:
            return self.get_method(name)

    def process(self, silname: str, translator: 'Translator') -> None:
        self.silname = silname
        for function in self.functions:
            self.functions[function].process(self.get_fresh_name(function),
                                             translator)
        for method in self.methods:
            self.methods[method].process(self.get_fresh_name(method),
                                         translator)
        for field in self.fields:
            self.fields[field].process(self.get_fresh_name(field))


class PythonMethod(PythonNode, PythonScope):
    def __init__(self, name: str, node: ast.AST, clazz: PythonClass,
                 superscope: PythonScope, pure: bool):
        super().__init__(name, node=node)
        if clazz is not None:
            if not isinstance(clazz, PythonClass):
                raise Exception(clazz)
        self.clazz = clazz
        self.overrides = None  # infer
        self.locals = collections.OrderedDict()  # direct
        self.args = collections.OrderedDict()  # direct
        self.type = None  # infer
        self.declaredexceptions = collections.OrderedDict()  # direct
        self.precondition = []
        self.postcondition = []
        self.handlers = []  # direct
        self.superscope = superscope
        self.pure = pure
        self.silnames = ['_res', '_err', '__end']

    def process(self, silname: str, translator: 'Translator') -> None:
        self.silname = silname
        functype = self.get_program().types.getfunctype(self.get_scope_prefix())
        if isinstance(functype, mypy.types.Void):
            self.type = None
        elif isinstance(functype, mypy.types.Instance):
            self.type = self.get_program().classes[functype.type.name()]
        else:
            raise UnsupportedException(functype)
        if self.clazz is not None and self.clazz.superclass is not None:
            self.overrides = self.clazz.superclass.get_function(
                self.name) if self.pure else self.clazz.superclass.get_method(
                self.name)
        for arg in self.args:
            self.args[arg].process(self.get_fresh_name(arg), translator)
        for local in self.locals:
            self.locals[local].process(self.get_fresh_name(local), translator)

    def get_variable(self, name: str) -> 'PythonVar':
        if name in self.locals:
            return self.locals[name]
        elif name in self.args:
            return self.args[name]
        else:
            return self.get_program().global_vars[name]

    def create_variable(self, name: str, clazz: PythonClass,
                        translator: 'Translator') -> 'PythonVar':
        silname = self.get_fresh_name(name)
        result = PythonVar(silname, None, clazz)
        result.process(silname, translator)
        self.locals[silname] = result
        return result


class PythonExceptionHandler(PythonNode):
    def __init__(self, node: ast.AST, type: PythonClass, tryname: str,
                 handlername: str, body: ast.AST, protectedRegion: ast.AST):
        super().__init__(handlername, node=node)
        self.tryname = tryname
        self.body = body
        self.region = protectedRegion
        self.type = type


class PythonVar(PythonNode):
    def __init__(self, name: str, node: ast.AST, clazz: PythonClass):
        super().__init__(name, node)
        self.clazz = clazz
        self.writes = []
        self.reads = []

    def process(self, silname: str, translator: 'Translator') -> None:
        self.silname = silname
        self.decl = translator.translate_pythonvar_decl(self)
        self.ref = translator.translate_pythonvar_ref(self)


class PythonField(PythonNode):
    def __init__(self, name: str, node: ast.AST, type: PythonClass,
                 clazz: PythonClass):
        super().__init__(name, node)
        self.clazz = clazz
        self.inherited = None  # infer
        self.type = type
        self.reads = []  # direct
        self.writes = []  # direct

    def process(self, silname: str) -> None:
        self.silname = silname
        if not self.is_mangled():
            if self.clazz.superclass is not None:
                self.inherited = self.clazz.superclass.get_field(self.name)

    def is_mangled(self) -> bool:
        return self.name.startswith('__') and not self.name.endswith('__')


class Analyzer:
    """
    Walks through the Python AST and collects the structures to be translated
    """

    def __init__(self, jvm: 'JVM', viperast: 'ViperAST', types: TypeInfo):
        self.viper = viperast
        self.java = jvm.java
        self.scala = jvm.scala
        self.viper = jvm.viper
        self.types = types
        self.program = PythonProgram(types)
        self.currentClass = None
        self.currentFunction = None

    def process(self, translator: 'Translator') -> None:
        self.program.process(translator)

    def visit_default(self, node: ast.AST) -> None:
        for field in node._fields:
            fieldval = getattr(node, field)
            if isinstance(fieldval, ast.AST):
                self.visit(fieldval, node)
            elif isinstance(fieldval, list):
                for item in fieldval:
                    self.visit(item, node)

    def visit(self, childnode: ast.AST, parent: ast.AST) -> None:
        childnode._parent = parent
        method = 'visit_' + childnode.__class__.__name__
        visitor = getattr(self, method, self.visit_default)
        visitor(childnode)

    def get_class(self, name: str) -> PythonClass:
        if name in self.program.classes:
            clazz = self.program.classes[name]
        else:
            clazz = PythonClass(name, self.program)
            self.program.classes[name] = clazz
        return clazz

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        assert self.currentClass is None
        assert self.currentFunction is None
        name = node.name
        if not isinstance(name, str):
            raise Exception(name)
        clazz = self.get_class(name)
        if len(node.bases) > 1:
            raise UnsupportedException(node)
        if len(node.bases) == 1:
            clazz.superclass = self.get_class(node.bases[0].id)
        self.currentClass = clazz
        for member in node.body:
            self.visit(member, node)
        self.currentClass = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
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
            func = PythonMethod(name, node, self.currentClass, scopecontainer,
                                self.is_pure(node))
            container[name] = func
        self.currentFunction = func
        self.visit_default(node)
        self.currentFunction = None

    def visit_arg(self, node: ast.arg) -> None:
        assert self.currentFunction is not None
        self.currentFunction.args[node.arg] = PythonVar(node.arg, node,
                                                        self.typeof(node))

    def track_access(self, node: ast.AST, var: PythonVar) -> None:
        if var is not None:
            if isinstance(node.ctx, ast.Load):
                var.reads.append(node)
            elif isinstance(node.ctx, ast.Store):
                var.writes.append(node)
            else:
                raise UnsupportedException(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func,
                      ast.Name) and node.func.id in CONTRACT_WRAPPER_FUNCS:
            assert self.currentFunction is not None
            if node.func.id == 'Requires':
                self.currentFunction.precondition.append(node.args[0])
            elif node.func.id == 'Ensures':
                self.currentFunction.postcondition.append(node.args[0])
            elif node.func.id == 'Exsures':
                exception = node.args[0].id
                if exception not in self.currentFunction.declaredexceptions:
                    self.currentFunction.declaredexceptions[exception] = []
                self.currentFunction.declaredexceptions[exception].append(
                    node.args[1])
        self.visit_default(node)

    def visit_Name(self, node: ast.Name) -> None:
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
        if isinstance(node._parent, ast.ExceptHandler):
            if node._parent.type is node:
                return
        # could be global declaration or global reference or static member
        # or local var or func arg
        if self.currentFunction is None:
            # this is global in some way
            if self.currentClass is None:
                # global var
                if isinstance(node.ctx, ast.Store):
                    type = self.types.gettype([], node.id)
                    clazz = self.get_class(type.name())
                    var = PythonVar(node.id, node, clazz)
                    assign = node._parent
                    if not isinstance(assign, ast.Assign) or len(
                            assign.targets) != 1:
                        raise UnsupportedException(assign)
                    var.value = assign.value
                    self.program.global_vars[node.id] = var
                var = self.program.global_vars[node.id]
                self.track_access(node, var)
            else:
                # static field
                raise UnsupportedException(node)
        # this is a global or a local var or a static field
        if not node.id in self.program.global_vars:
            # must be local for static field
            if self.currentFunction is None:
                # must be static field
                raise UnsupportedException(node)
            else:
                # must be local var?
                var = None
                if node.id in self.currentFunction.locals:
                    var = self.currentFunction.locals[node.id]
                elif node.id in self.currentFunction.args:
                    pass
                else:
                    var = PythonVar(node.id, node, self.typeof(node))
                    self.currentFunction.locals[node.id] = var
                self.track_access(node, var)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        self.visit_default(node)
        if not isinstance(node._parent, ast.Call):
            receiver = self.typeof(node.value)
            field = receiver.add_field(node.attr, node, self.typeof(node))
            self.track_access(node, field)

    def typeof(self, node: ast.AST) -> PythonClass:
        if isinstance(node, ast.Name):
            if node.id in LITERALS:
                raise UnsupportedException(node)
            context = []
            if self.currentClass is not None:
                context.append(self.currentClass.name)
            if self.currentFunction is not None:
                context.append(self.currentFunction.name)
            type = self.types.gettype(context, node.id)
            return self.get_class(type.name())
        elif isinstance(node, ast.Attribute):
            receiver = self.typeof(node.value)
            context = [receiver.name]
            type = self.types.gettype(context, node.attr)
            return self.get_class(type.name())
        elif isinstance(node, ast.arg):
            context = []
            if self.currentClass is not None:
                context.append(self.currentClass.name)
            context.append(self.currentFunction.name)
            type = self.types.gettype(context, node.arg)
            return self.get_class(type.name())
        else:
            raise UnsupportedException(node)

    def visit_Try(self, node: ast.Try) -> None:
        assert self.currentFunction is not None
        self.visit_default(node)
        tryname = self.currentFunction.get_fresh_name('try')
        node.silname = tryname
        for handler in node.handlers:
            handlername = self.currentFunction.get_fresh_name(
                'handler' + handler.type.id)
            type = self.get_class(handler.type.id)
            pyhndlr = PythonExceptionHandler(handler, type, tryname,
                                             handlername, handler.body,
                                             node.body)
            self.currentFunction.handlers.append(pyhndlr)

    def is_pure(self, func: ast.FunctionDef) -> bool:
        return (len(func.decorator_list) == 1
                and func.decorator_list[0].id == 'Pure')
