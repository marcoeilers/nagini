import ast
import mypy
import os

from collections import OrderedDict
from py2viper_translation import astpp
from py2viper_contracts.contracts import CONTRACT_FUNCS, CONTRACT_WRAPPER_FUNCS
from py2viper_translation.ast_util import mark_text_ranges
from py2viper_translation.constants import PRIMITIVES, LITERALS
from py2viper_translation.typeinfo import TypeInfo
from py2viper_translation.util import get_func_name, UnsupportedException
from typing import List, Optional, Dict


class PythonScope:
    """
    Represents a namespace/scope in Python
    """

    def contains_name(self, name: str) -> bool:
        result = name in self.sil_names
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
            self.sil_names.append(newname)
            return newname
        else:
            self.sil_names.append(name)
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
    def __init__(self, types: TypeInfo) -> None:
        self.classes = OrderedDict()
        self.functions = OrderedDict()
        self.methods = OrderedDict()
        self.predicates = OrderedDict()
        self.global_vars = OrderedDict()
        self.sil_names = []
        self.superscope = None
        self.types = types
        for primitive in PRIMITIVES:
            self.classes[primitive] = PythonClass(primitive, self)

    def process(self, translator: 'Translator') -> None:
        for name, cls in self.classes.items():
            cls.process(self.get_fresh_name(name), translator)
        for name, function in self.functions.items():
            function.process(self.get_fresh_name(name), translator)
        for name, method in self.methods.items():
            method.process(self.get_fresh_name(name), translator)
        for name, predicate in self.predicates.items():
            predicate.process(self.get_fresh_name(name), translator)
        for name, var in self.global_vars.items():
            var.process(self.get_fresh_name(name), translator)

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
        self.sil_name = None


class PythonClass(PythonNode, PythonScope):
    """
    Represents a class in the Python program.
    """

    def __init__(self, name: str, superscope: PythonScope, node: ast.AST = None,
                 superclass: 'PythonClass' = None, interface=False):
        """
        :param superscope: The scope, usually program, this belongs to.
        :param interface: True iff the class implementation is provided in
        native Silver.
        """
        super().__init__(name, node)
        self.superclass = superclass
        self.functions = OrderedDict()
        self.methods = OrderedDict()
        self.predicates = OrderedDict()
        self.fields = OrderedDict()
        self.type = None  # infer, domain type
        self.superscope = superscope
        self.sil_names = []
        self.interface = interface

    def add_field(self, name: str, node: ast.AST,
                  type: 'PythonClass') -> 'PythonField':
        """
        Adds a field with the given name and type if it doesn't exist yet in
        this class.
        """
        if name in self.fields:
            field = self.fields[name]
            assert field.type == type
        else:
            field = PythonField(name, node, type, self)
            self.fields[name] = field
        return field

    def get_field(self, name: str) -> Optional['PythonField']:
        """
        Returns the field with the given name in this class or a superclass.
        """
        if name in self.fields:
            return self.fields[name]
        elif self.superclass is not None:
            return self.superclass.get_field(name)
        else:
            return None

    def get_method(self, name: str) -> Optional['PythonMethod']:
        """
        Returns the method with the given name in this class or a superclass.
        """
        if name in self.methods:
            return self.methods[name]
        elif self.superclass is not None:
            return self.superclass.get_method(name)
        else:
            return None

    def get_function(self, name: str) -> Optional['PythonMethod']:
        """
        Returns the function with the given name in this class or a superclass.
        """
        if name in self.functions:
            return self.functions[name]
        elif self.superclass is not None:
            return self.superclass.get_function(name)
        else:
            return None

    def get_func_or_method(self, name: str) -> Optional['PythonMethod']:
        """
        Returns the function or method with the given name in this class or a
        superclass.
        """
        if self.get_function(name) is not None:
            return self.get_function(name)
        else:
            return self.get_method(name)

    def get_predicate(self, name: str) -> Optional['PythonMethod']:
        """
        Returns the predicate with the given name in this class or a superclass.
        """
        if name in self.predicates:
            return self.predicates[name]
        elif self.superclass is not None:
            return self.superclass.get_predicate(name)
        else:
            return None

    def process(self, sil_name: str, translator: 'Translator') -> None:
        """
        Creates fresh Silver names for all class members and initializes all
        of them.
        """
        self.sil_name = sil_name
        for name, function in self.functions.items():
            func_name = self.name + '_' + name
            function.process(self.get_fresh_name(func_name), translator)
        for name, method in self.methods.items():
            method_name = self.name + '_' + name
            method.process(self.get_fresh_name(method_name), translator)
        for name, predicate in self.predicates.items():
            pred_name = self.name + '_' + name
            predicate.process(self.get_fresh_name(pred_name), translator)
        for name, field in self.fields.items():
            field_name = self.name + '_' + name
            field.process(self.get_fresh_name(field_name))

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
                 superscope: PythonScope, pure: bool, contract_only: bool,
                 interface: bool = False):
        """
        :param cls: Class this method belongs to, if any.
        :param superscope: The scope (class or program) this method belongs to
        :param pure: True iff ir's a pure function, not an impure method
        :param contract_only: True iff we're not generating the method's
        implementation, just its contract
        :param interface: True iff the method implementation is provided in
        native Silver.
        """
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
        self.try_blocks = []  # direct
        self.superscope = superscope
        self.pure = pure
        self.predicate = False
        self.sil_names = ['_res', '_err', '__end']
        self.contract_only = contract_only
        self.interface = interface

    def process(self, sil_name: str, translator: 'Translator') -> None:
        """
        Creates fresh Silver names for all parameters and initializes them,
        same for local variables. Also sets the method type and
        checks if this method overrides one from a superclass,
        """
        self.sil_name = sil_name
        for arg in self.args:
            self.args[arg].process(self.get_fresh_name(arg), translator)
        if self.interface:
            return
        func_type = self.get_program().types.get_func_type(
            self.get_scope_prefix())
        if isinstance(func_type, mypy.types.Void):
            self.type = None
        elif isinstance(func_type, mypy.types.Instance):
            self.type = self.get_program().classes[func_type.type.name()]
        else:
            raise UnsupportedException(func_type)
        if self.cls is not None and self.cls.superclass is not None:
            if self.predicate:
                self.overrides = self.cls.superclass.get_predicate(self.name)
            else:
                self.overrides = self.cls.superclass.get_func_or_method(
                    self.name)
        for local in self.locals:
            self.locals[local].process(self.get_fresh_name(local), translator)

    def get_variable(self, name: str) -> 'PythonVar':
        """
        Returns the variable (local variable or method parameter) with the
        given name.
        """
        if name in self.locals:
            return self.locals[name]
        elif name in self.args:
            return self.args[name]
        else:
            return self.get_program().global_vars[name]

    def create_variable(self, name: str, cls: PythonClass,
                        translator: 'Translator') -> 'PythonVar':
        """
        Creates a new local variable with the given name and type and performs
        all necessary processing/initialization
        """
        sil_name = self.get_fresh_name(name)
        result = PythonVar(sil_name, None, cls)
        result.process(sil_name, translator)
        self.locals[sil_name] = result
        return result


class PythonExceptionHandler(PythonNode):
    """
    Represents an except-block belonging to a try-block.
    """

    def __init__(self, node: ast.AST, exception_type: PythonClass,
                 try_block: 'PythonTryBlock', handler_name: str, body: ast.AST,
                 exception_name: str):
        """
        :param exception_type: The type of exception this handler catches
        :param try_block: The try-block this handler belongs to
        :param handler_name: Label that this handler will get in Silver
        :param exception_name: Variable name for the exception in the block
        """
        super().__init__(handler_name, node=node)
        self.try_block = try_block
        self.body = body
        self.exception = exception_type
        self.exception_name = exception_name


class PythonTryBlock(PythonNode):
    """
    Represents a try-block, which may include except-blocks, an else-block
    and/or a finally-block.
    """

    def __init__(self, node: ast.AST, try_name: str, method: PythonMethod,
                 protected_region: ast.AST):
        """
        :param method: Method this block is in
        :param protected_region: Statements protected by the try
        """
        super().__init__(try_name, node=node)
        self.handlers = []
        self.else_block = None
        self.finally_block = None
        self.protected_region = protected_region
        self.finally_var = None
        self.error_var = None
        self.method = method

    def get_finally_var(self, translator: 'Translator') -> 'PythonVar':
        """
        Lazily creates and returns the variable in which we store the
        information how control flow should proceed after the execution
        of a finally block. We use a value of 0 to say normal flow, 1 to say
        we returned normally, i.e. jump to the end of the function asap, 2
        to say we returned exceptionally, i.e. jump to the end of the function
        moving through exception handlers.
        """
        if self.finally_var:
            return self.finally_var
        sil_name = self.method.get_fresh_name('try_finally')
        bool_type = self.method.get_program().classes['int']
        result = PythonVar(sil_name, None, bool_type)
        result.process(sil_name, translator)
        self.method.locals[sil_name] = result
        self.finally_var = result
        return result

    def get_error_var(self, translator: 'Translator') -> 'PythonVar':
        """
        Lazily creates and returns the variable in which any exceptions thrown
        within the block will be stored.
        """
        if self.error_var:
            return self.error_var
        sil_name = self.method.get_fresh_name('error')
        exc_type = self.method.get_program().classes['Exception']
        result = PythonVar(sil_name, None, exc_type)
        result.process(sil_name, translator)
        self.method.locals[sil_name] = result
        self.error_var = result
        return result


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

    def process(self, sil_name: str, translator: 'Translator') -> None:
        """
        Creates a Silver variable declaration and reference representing this
        Python variable.
        """
        self.sil_name = sil_name
        prog = self.type.get_program()
        self.decl = translator.translate_pythonvar_decl(self, prog)
        self.ref = translator.translate_pythonvar_ref(self, prog)


class PythonField(PythonNode):
    """
    Represents a field of a Python class.
    """
    def __init__(self, name: str, node: ast.AST, type: PythonClass,
                 cls: PythonClass):
        """
        :param type: The type of the field.
        :param cls: The class this field belongs to
        """
        super().__init__(name, node)
        self.cls = cls
        self.inherited = None  # infer
        self.type = type
        self.reads = []  # direct
        self.writes = []  # direct

    def process(self, sil_name: str) -> None:
        """
        Checks if this field is inherited from a superclass.
        """
        self.sil_name = sil_name
        if not self.is_mangled():
            if self.cls.superclass is not None:
                self.inherited = self.cls.superclass.get_field(self.name)

    def is_mangled(self) -> bool:
        return self.name.startswith('__') and not self.name.endswith('__')


class Analyzer(ast.NodeVisitor):
    """
    Walks through the Python AST and collects the structures to be translated.
    """

    def __init__(self, jvm: 'JVM', viperast: 'ViperAST', types: TypeInfo,
                 path: str):
        self.viper = viperast
        self.java = jvm.java
        self.scala = jvm.scala
        self.viper = jvm.viper
        self.types = types
        self.program = PythonProgram(types)
        self.current_class = None
        self.current_function = None
        self.contract_only = False
        self.modules = [os.path.abspath(path)]
        self.asts = {}

    def collect_imports(self, abs_path: str) -> None:
        """
        Parses the file at the given location, puts the result into self.asts.
        Scans the parsed file for Import-statements and adds all imported paths
        to self.modules.
        """
        with open(abs_path, 'r') as file:
            text = file.read()
        parseresult = ast.parse(text)
        try:
            mark_text_ranges(parseresult, text)
        except Exception:
            # ignore
            pass
        self.asts[abs_path] = parseresult
        print(astpp.dump(parseresult))
        assert isinstance(parseresult, ast.Module)
        for stmt in parseresult.body:
            if get_func_name(stmt) != 'Import':
                continue
            if isinstance(stmt, ast.Expr):
                call = stmt.value
            else:
                call = stmt
            if len(call.args) != 1 or not isinstance(call.args[0], ast.Str):
                raise UnsupportedException(call)
            imported = call.args[0].s
            imp_path = os.path.dirname(abs_path) + os.sep + imported
            self.add_module(imp_path)

    def add_module(self, abs_path: str) -> None:
        if abs_path not in self.modules:
            self.modules.append(abs_path)

    def process(self, translator: 'Translator') -> None:
        """
        Performs preprocessing on the result of the analysis, which infers some
        things, creates some data structures for the translation etc.
        """
        self.program.process(translator)

    def add_interface(self, interface: Dict) -> None:
        """
        Adds the classes, methods and functions in the interface-dict to
        the program. Meant to be used with a dict containing all methods/...
        that have native Silver representations and won't be created by the
        translator.
        """
        for class_name in interface:
            if_cls = interface[class_name]
            cls = self.get_class(class_name, interface=True)
            if 'extends' in if_cls:
                cls.superclass = self.get_class(if_cls['extends'])
            for method_name in if_cls.get('methods', []):
                if_method = if_cls['methods'][method_name]
                self._add_interface_method(method_name, if_method, cls, False)
            for method_name in if_cls.get('functions', []):
                if_method = if_cls['functions'][method_name]
                self._add_interface_method(method_name, if_method, cls, True)

    def _add_interface_method(self, method_name, if_method, cls, pure):
        method = PythonMethod(method_name, None, cls, self.program,
                              pure, False, True)
        method.args = OrderedDict()
        ctr = 0
        for arg_type in if_method['args']:
            name = 'arg_' + str(ctr)
            arg = PythonVar(name, None,
                            self.get_class(arg_type))
            ctr += 1
            method.args[name] = arg
        if if_method['type']:
            method.type = self.get_class(if_method['type'])
        if pure:
            cls.functions[method_name] = method
        else:
            cls.methods[method_name] = method

    def visit_module(self, module: str) -> None:
        self.visit_default(self.asts[module])

    def visit_default(self, node: ast.AST) -> None:
        for field in node._fields:
            fieldval = getattr(node, field)
            if isinstance(fieldval, ast.AST):
                self.visit(fieldval, node)
            elif isinstance(fieldval, list):
                for item in fieldval:
                    self.visit(item, node)

    def visit(self, child_node: ast.AST, parent: ast.AST) -> None:
        child_node._parent = parent
        method = 'visit_' + child_node.__class__.__name__
        visitor = getattr(self, method, self.visit_default)
        visitor(child_node)

    def get_class(self, name: str, interface=False) -> PythonClass:
        if name in self.program.classes:
            cls = self.program.classes[name]
            if interface:
                cls.interface = interface
        else:
            cls = PythonClass(name, self.program, interface=interface)
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
        else:
            cls.superclass = self.get_class('object')
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
        if self.is_predicate(node):
            container = scope_container.predicates
        elif self.is_pure(node):
            container = scope_container.functions
        else:
            assert not node.decorator_list
            container = scope_container.methods
        if name in container:
            func = container[name]
            func.cls = self.current_class
            func.pure = self.is_pure(node)
            func.node = node
            func.superscope = scope_container
        else:
            func = PythonMethod(name, node, self.current_class, scope_container,
                                self.is_pure(node), self.contract_only)
            container[name] = func
        func.predicate = self.is_predicate(node)
        functype = self.types.get_func_type(func.get_scope_prefix())
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
                    type = self.types.get_type([], node.id)
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
            type = self.types.get_type(context, node.id)
            return self.get_class(type.name())
        elif isinstance(node, ast.Attribute):
            receiver = self.typeof(node.value)
            context = [receiver.name]
            type = self.types.get_type(context, node.attr)
            return self.get_class(type.name())
        elif isinstance(node, ast.arg):
            context = []
            if self.current_class is not None:
                context.append(self.current_class.name)
            context.append(self.current_function.name)
            type = self.types.get_type(context, node.arg)
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
        try_name = self.current_function.get_fresh_name('try')
        try_block = PythonTryBlock(node, try_name, self.current_function,
                                   node.body)
        node.sil_name = try_name
        for handler in node.handlers:
            handler_name = self.current_function.get_fresh_name(
                'handler' + handler.type.id)
            type = self.get_class(handler.type.id)
            py_handler = PythonExceptionHandler(handler, type, try_block,
                                                handler_name, handler.body,
                                                handler.name)
            try_block.handlers.append(py_handler)
        if node.orelse:
            handler_name = self.current_function.get_fresh_name('try_else')
            py_handler = PythonExceptionHandler(node, None, try_block,
                                                handler_name, node.orelse, None)
            try_block.else_block = py_handler
        if node.finalbody:
            finally_name = self.current_function.get_fresh_name('try_finally')
            try_block.finally_block = node.finalbody
            try_block.finally_name = finally_name
        self.current_function.try_blocks.append(try_block)

    def is_pure(self, func: ast.FunctionDef) -> bool:
        return (len(func.decorator_list) == 1
                and func.decorator_list[0].id == 'Pure')

    def is_predicate(self, func: ast.FunctionDef) -> bool:
        return (len(func.decorator_list) == 1
                and func.decorator_list[0].id == 'Predicate')
