import ast
import mypy
import os

from collections import OrderedDict
from py2viper_translation.containers import (
    PythonClass,
    PythonExceptionHandler,
    PythonProgram,
    PythonTryBlock,
    PythonVar,
    ContainerFactory,
    PythonMethod)
from py2viper_contracts.contracts import CONTRACT_FUNCS, CONTRACT_WRAPPER_FUNCS
from py2viper_translation import astpp
from py2viper_translation.ast_util import mark_text_ranges
from py2viper_translation.constants import LITERALS
from py2viper_translation.typeinfo import TypeInfo
from py2viper_translation.util import get_func_name, UnsupportedException
from typing import Dict


class Analyzer(ast.NodeVisitor):
    """
    Walks through the Python AST and collects the structures to be translated.
    """

    def __init__(self, jvm: 'JVM', viperast: 'ViperAST', types: TypeInfo,
                 path: str, container_factory: ContainerFactory):
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
        self.container_factory = container_factory

    def collect_imports(self, abs_path: str) -> None:
        """
        Parses the file at the given location, puts the result into self.asts.
        Scans the parsed file for Import-statements and adds all imported paths
        to self.modules.
        """
        with open(abs_path, 'r') as file:
            text = file.read()
        parse_result = ast.parse(text)
        try:
            mark_text_ranges(parse_result, text)
        except Exception:
            # ignore
            pass
        self.asts[abs_path] = parse_result
        # print(astpp.dump(parse_result))
        assert isinstance(parse_result, ast.Module)
        for stmt in parse_result.body:
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
                              pure, False, self.container_factory, True)
        method.args = OrderedDict()
        ctr = 0
        for arg_type in if_method['args']:
            name = 'arg_' + str(ctr)
            arg = self.container_factory.create_python_var(name, None,
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
            func = self.container_factory.create_python_method(name, node,
                self.current_class, scope_container, self.is_pure(node),
                self.contract_only, self.container_factory)
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
        self.current_function.args[node.arg] = \
            self.container_factory.create_python_var(node.arg, node,
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
                    var = self.container_factory.create_python_var(node.id,
                                                                   node, cls)
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
                    var = self.container_factory.create_python_var(node.id,
                        node, self.typeof(node))
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
        try_block = PythonTryBlock(node, try_name, self.container_factory,
                                   self.current_function, node.body)
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
