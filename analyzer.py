import ast
import mypy

from collections import OrderedDict
from constants import PRIMITIVES, LITERALS
from contracts.contracts import CONTRACT_FUNCS, CONTRACT_WRAPPER_FUNCS
from typeinfo import TypeInfo
from typing import List, Optional
from util import UnsupportedException


class PythonScope:
    """
    Represents a namespace/scope in Python
    """

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
        self.classes = OrderedDict()
        self.functions = OrderedDict()
        self.methods = OrderedDict()
        self.global_vars = OrderedDict()
        self.silnames = []
        self.superscope = None
        self.types = types
        for primitive in PRIMITIVES:
            self.classes[primitive] = PythonClass(primitive, self)

    def process(self, translator: 'Translator') -> None:
        for cls in self.classes:
            self.classes[cls].process(self.get_fresh_name(cls), translator)
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
        self.superclass = superclass
        self.functions = OrderedDict()
        self.methods = OrderedDict()
        self.fields = OrderedDict()
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

    def issubtype(self, cls: 'PythonClass') -> bool:
        if cls is self:
            return True
        if self.superclass is None:
            return False
        return self.superclass.issubtype(cls)


class PythonMethod(PythonNode, PythonScope):
    """
    Represents a Python function which may be pure or impure, belong
    to a class or not
    """

    def __init__(self, name: str, node: ast.AST, cls: PythonClass,
                 superscope: PythonScope, pure: bool):
        super().__init__(name, node=node)
        if cls is not None:
            if not isinstance(cls, PythonClass):
                raise Exception(cls)
        self.cls = cls
        self.overrides = None  # infer
        self.locals = OrderedDict()  # direct
        self.args = OrderedDict()  # direct
        self.type = None  # infer
        self.declared_exceptions = OrderedDict()  # direct
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
        if self.cls is not None and self.cls.superclass is not None:
            self.overrides = self.cls.superclass.get_func_or_method(self.name)

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

    def create_variable(self, name: str, cls: PythonClass,
                        translator: 'Translator') -> 'PythonVar':
        silname = self.get_fresh_name(name)
        result = PythonVar(silname, None, cls)
        result.process(silname, translator)
        self.locals[silname] = result
        return result


class PythonExceptionHandler(PythonNode):
    def __init__(self, node: ast.AST, exception_type: PythonClass, tryname: str,
                 handlername: str, body: ast.AST, protectedRegion: ast.AST):
        super().__init__(handlername, node=node)
        self.tryname = tryname
        self.body = body
        self.region = protectedRegion
        self.exception = exception_type


class PythonVar(PythonNode):
    """
    Represents a variable in Python. Can be a global variable, a local variable
    or a function parameter.
    """

    def __init__(self, name: str, node: ast.AST, type: PythonClass):
        super().__init__(name, node)
        self.type = type
        self.writes = []
        self.reads = []

    def process(self, silname: str, translator: 'Translator') -> None:
        self.silname = silname
        self.decl = translator.translate_pythonvar_decl(self)
        self.ref = translator.translate_pythonvar_ref(self)


class PythonField(PythonNode):
    def __init__(self, name: str, node: ast.AST, type: PythonClass,
                 cls: PythonClass):
        super().__init__(name, node)
        self.cls = cls
        self.inherited = None  # infer
        self.type = type
        self.reads = []  # direct
        self.writes = []  # direct

    def process(self, silname: str) -> None:
        self.silname = silname
        if not self.is_mangled():
            if self.cls.superclass is not None:
                self.inherited = self.cls.superclass.get_field(self.name)

    def is_mangled(self) -> bool:
        return self.name.startswith('__') and not self.name.endswith('__')


class Analyzer(ast.NodeVisitor):
    """
    Walks through the Python AST and collects the structures to be translated.
    """

    def __init__(self, jvm: 'JVM', viperast: 'ViperAST', types: TypeInfo):
        self.viper = viperast
        self.java = jvm.java
        self.scala = jvm.scala
        self.viper = jvm.viper
        self.types = types
        self.program = PythonProgram(types)
        self.current_class = None
        self.current_function = None

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
            cls = self.program.classes[name]
        else:
            cls = PythonClass(name, self.program)
            self.program.classes[name] = cls
        return cls

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        assert self.current_class is None
        assert self.current_function is None
        name = node.name
        cls = self.get_class(name)
        if len(node.bases) > 1:
            raise UnsupportedException(node)
        if len(node.bases) == 1:
            cls.superclass = self.get_class(node.bases[0].id)
        self.current_class = cls
        for member in node.body:
            self.visit(member, node)
        self.current_class = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        assert self.current_function is None
        name = node.name
        if not isinstance(name, str):
            raise Exception(name)
        if self.current_class is None:
            scope_container = self.program
        else:
            scope_container = self.current_class
        if self.is_pure(node):
            container = scope_container.functions
        else:
            container = scope_container.methods
        if name in container:
            func = container[name]
            func.cls = self.current_class
            func.pure = self.is_pure(node)
            func.node = node
            func.superscope = scope_container
        else:
            func = PythonMethod(name, node, self.current_class, scope_container,
                                self.is_pure(node))
            container[name] = func
        functype = self.types.getfunctype(func.get_scope_prefix())
        if isinstance(functype, mypy.types.Void):
            func.type = None
        elif isinstance(functype, mypy.types.Instance):
            func.type = self.get_class(functype.type.name())
        else:
            raise UnsupportedException(functype)
        self.current_function = func
        self.visit_default(node)
        self.current_function = None

    def visit_arg(self, node: ast.arg) -> None:
        assert self.current_function is not None
        self.current_function.args[node.arg] = PythonVar(node.arg, node,
                                                        self.typeof(node))

    def track_access(self, node: ast.AST, var: PythonVar) -> None:
        if var is None:
            return
        if isinstance(node.ctx, ast.Load):
            var.reads.append(node)
        elif isinstance(node.ctx, ast.Store):
            var.writes.append(node)
        else:
            raise UnsupportedException(node)

    def visit_Call(self, node: ast.Call) -> None:
        if (isinstance(node.func, ast.Name)
                and node.func.id in CONTRACT_WRAPPER_FUNCS):
            assert self.current_function is not None
            if node.func.id == 'Requires':
                self.current_function.precondition.append(node.args[0])
            elif node.func.id == 'Ensures':
                self.current_function.postcondition.append(node.args[0])
            elif node.func.id == 'Exsures':
                exception = node.args[0].id
                if exception not in self.current_function.declared_exceptions:
                    self.current_function.declared_exceptions[exception] = []
                self.current_function.declared_exceptions[exception].append(
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
        # node could be global reference or static member
        # or local variable or function argument.
        if self.current_function is None:
            # node is global in some way.
            if self.current_class is None:
                # node is a global variable.
                if isinstance(node.ctx, ast.Store):
                    type = self.types.gettype([], node.id)
                    cls = self.get_class(type.name())
                    var = PythonVar(node.id, node, cls)
                    assign = node._parent
                    if (not isinstance(assign, ast.Assign)
                        or len(assign.targets) != 1):
                        raise UnsupportedException(assign)
                    var.value = assign.value
                    self.program.global_vars[node.id] = var
                var = self.program.global_vars[node.id]
                self.track_access(node, var)
            else:
                # node is a static field.
                raise UnsupportedException(node)
        if node.id not in self.program.global_vars:
            # node is a local variable or a static field.
            if self.current_function is None:
                # node is a static field.
                raise UnsupportedException(node)
            else:
                # node refers to a local variable.
                var = None
                if node.id in self.current_function.locals:
                    var = self.current_function.locals[node.id]
                elif node.id in self.current_function.args:
                    pass
                else:
                    var = PythonVar(node.id, node, self.typeof(node))
                    self.current_function.locals[node.id] = var
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
            if self.current_class is not None:
                context.append(self.current_class.name)
            if self.current_function is not None:
                context.append(self.current_function.name)
            type = self.types.gettype(context, node.id)
            return self.get_class(type.name())
        elif isinstance(node, ast.Attribute):
            receiver = self.typeof(node.value)
            context = [receiver.name]
            type = self.types.gettype(context, node.attr)
            return self.get_class(type.name())
        elif isinstance(node, ast.arg):
            context = []
            if self.current_class is not None:
                context.append(self.current_class.name)
            context.append(self.current_function.name)
            type = self.types.gettype(context, node.arg)
            return self.get_class(type.name())
        elif (isinstance(node, ast.Call)
              and isinstance(node.func, ast.Name)
              and node.func.id in CONTRACT_FUNCS):
            if node.func.id == 'Result':
                return self.current_function.type
            else:
                raise UnsupportedException(node)
        elif isinstance(node, ast.Call) and isinstance(node.func,
                                                       ast.Attribute):
            receiver = self.typeof(node.func.value)
            method = receiver.get_func_or_method(node.func.attr)
            return method.type
        else:
            raise UnsupportedException(node)

    def visit_Try(self, node: ast.Try) -> None:
        assert self.current_function is not None
        self.visit_default(node)
        tryname = self.current_function.get_fresh_name('try')
        node.silname = tryname
        for handler in node.handlers:
            handlername = self.current_function.get_fresh_name(
                'handler' + handler.type.id)
            type = self.get_class(handler.type.id)
            pyhndlr = PythonExceptionHandler(handler, type, tryname,
                                             handlername, handler.body,
                                             node.body)
            self.current_function.handlers.append(pyhndlr)

    def is_pure(self, func: ast.FunctionDef) -> bool:
        return (len(func.decorator_list) == 1
                and func.decorator_list[0].id == 'Pure')
