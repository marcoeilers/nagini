import ast
import logging
import mypy
import os
import py2viper_contracts.io_builtins
import py2viper_translation.external.astpp
import tokenize

from collections import OrderedDict
from py2viper_contracts.contracts import CONTRACT_FUNCS, CONTRACT_WRAPPER_FUNCS
from py2viper_contracts.io import IO_OPERATION_PROPERTY_FUNCS
from py2viper_translation.analyzer_io import IOOperationAnalyzer
from py2viper_translation.external.ast_util import mark_text_ranges
from py2viper_translation.lib.constants import LITERALS, OBJECT_TYPE, TUPLE_TYPE
from py2viper_translation.lib.program_nodes import (
    _get_target,
    GenericType,
    MethodType,
    ProgramNodeFactory,
    PythonClass,
    PythonExceptionHandler,
    PythonGlobalVar,
    PythonIOOperation,
    PythonNode,
    PythonModule,
    PythonModuleView,
    PythonTryBlock,
    PythonType,
    PythonVar,
    PythonMethod,
)
from py2viper_translation.lib.typeinfo import TypeInfo
from py2viper_translation.lib.util import (
    construct_lambda_prefix,
    get_func_name,
    InvalidProgramException,
    is_io_existential,
    UnsupportedException,
)
from typing import Dict, List, Set, Union


logger = logging.getLogger('py2viper_translation.analyzer')


class Analyzer(ast.NodeVisitor):
    """
    Walks through the Python AST and collects the structures to be translated.
    """

    def __init__(self, jvm: 'JVM', viperast: 'ViperAST', types: TypeInfo,
                 path: str, node_factory: ProgramNodeFactory):
        self.viper = viperast
        self.java = jvm.java
        self.scala = jvm.scala
        self.viper = jvm.viper
        self.types = types
        self.global_mod = PythonModule(types, node_factory, None, None)
        self.global_mod.global_mod = self.global_mod
        self.module = PythonModule(types, node_factory, '__main__',
                                   self.global_mod,
                                   sil_names=self.global_mod.sil_names)
        self.current_class = None
        self.current_function = None
        self.current_scopes = []
        self.contract_only = False
        self.module_paths = [os.path.abspath(path)]
        self.modules = {os.path.abspath(path): self.module}
        self.asts = {}
        self.node_factory = node_factory
        self.io_operation_analyzer = IOOperationAnalyzer(self, node_factory)
        self._is_io_existential = False     # Are we defining an
                                            # IOExists block?
        self._aliases = {}                  # Dict[str, PythonBaseVar]
        self.current_loop_invariant = None

    def define_new(self, container: Union[PythonModule, PythonClass],
                   name: str, node: ast.AST) -> None:
        """
        Called when a new top level element named ``name`` is created in
        ``container``. Checks there is any existing element with the
        same name, and raises an exception in that case.
        """
        if isinstance(container, PythonModule):
            if name in container.classes:
                cls = container.classes[name]
                if cls.defined:
                    raise InvalidProgramException(node, 'multiple.definitions')
            if name in container.global_vars and hasattr(container.global_vars[name], 'value'):
                raise InvalidProgramException(node, 'multiple.definitions')
        if (name in container.functions or
                    name in container.methods or
                    name in container.predicates):
            raise InvalidProgramException(node, 'multiple.definitions')

    IGNORED_IMPORTS = {'py2viper_contracts.contracts',
                       'typing',
                       'py2viper_contracts.io',
                       'py2viper_contracts.obligations',
                       'threading'}

    def collect_imports(self, abs_path: str) -> None:
        """
        Parses the file at the given location, puts the result into self.asts.
        Scans the parsed file for Import-statements and adds all imported paths
        to self.modules.
        """
        if abs_path.startswith('mod$'):
            return
        with tokenize.open(abs_path) as file:
            text = file.read()
        parse_result = ast.parse(text)
        try:
            mark_text_ranges(parse_result, text)
        except Exception:
            # ignore
            pass
        self.asts[abs_path] = parse_result
        logger.debug(py2viper_translation.external.astpp.dump(parse_result))
        assert isinstance(parse_result, ast.Module)
        imports = [s for s in parse_result.body if isinstance(s, (ast.Import, ast.ImportFrom))]
        for stmt in parse_result.body:
            if isinstance(stmt, ast.Import):
                for name in stmt.names:
                    module = name.name
                    if module in self.IGNORED_IMPORTS:
                        continue
                    as_ = name.asname
                    assert module in self.types.files
                    path = self.types.files[module]
                    self.add_module(path, abs_path, as_ if as_ else module)
            elif isinstance(stmt, ast.ImportFrom):
                module = stmt.module
                if (module in self.IGNORED_IMPORTS):
                    continue
                if module == 'py2viper_contracts.io_builtins':
                    path = py2viper_contracts.io_builtins.__file__
                else:
                    assert module in self.types.files
                    path = self.types.files[module]
                if len(stmt.names) == 1 and stmt.names[0].name== '*':
                    names = None
                else:
                    names = [(a.name, a.asname if a.asname else None) for a in stmt.names]
                self.add_module(path, abs_path, None, names)

    def add_module(self, abs_path: str, into: str, as_: str, names=None) -> None:
        if as_ and '.' in as_:
            split = as_.split('.', 1)
            first = split[0]
            rest = split[1]
            self.add_module('mod$' + first, into, first)
            self.add_module(abs_path, 'mod$' + first, rest)
            return
        if abs_path not in self.module_paths:
            self.module_paths.append(abs_path)
            type_prefix = self.types.get_type_prefix(abs_path)
            new_mod = PythonModule(self.module.types, self.node_factory,
                                    type_prefix, self.module.global_mod,
                                    self.module.sil_names)
            self.modules[abs_path] = new_mod
        else:
            new_mod = self.modules[abs_path]
        into_mod = self.modules[into]
        if as_:
            assert not names
            into_mod.namespaces[as_] = new_mod
        else:
            if names:
                new_mod = PythonModuleView(new_mod, names)
            into_mod.from_imports.append(new_mod)

    def process(self, translator: 'Translator') -> None:
        """
        Performs preprocessing on the result of the analysis, which infers some
        things, creates some data structures for the translation etc.
        """
        self.module.global_mod.process(translator)
        for module in self.modules.values():
            module.process(translator)

    def add_interface(self, interface: Dict) -> None:
        """
        Adds the classes, methods and functions in the interface-dict to
        the program. Meant to be used with a dict containing all methods/...
        that have native Silver representations and won't be created by the
        translator.
        """
        # create global classes first
        for class_name in interface:
            cls = self.get_class(class_name, interface=True,
                                 module=self.module.global_mod)
            cls.defined = True
        for class_name in interface:
            cls = self.get_class(class_name)
            if_cls = interface[class_name]
            if 'extends' in if_cls:
                superclass = self.get_class(if_cls['extends'],
                                            module=self.module.global_mod)
                cls.superclass = superclass
            for method_name in if_cls.get('methods', []):
                if_method = if_cls['methods'][method_name]
                self._add_interface_method(method_name, if_method, cls, False)
            for method_name in if_cls.get('functions', []):
                if_method = if_cls['functions'][method_name]
                self._add_interface_method(method_name, if_method, cls, True)

    def _add_interface_method(self, method_name, if_method, cls, pure):
        method = PythonMethod(method_name, None, cls, self.module,
                              pure, False, self.node_factory, True,
                              if_method)
        ctr = 0
        for arg_type in if_method['args']:
            name = 'arg_' + str(ctr)
            arg = self.node_factory.create_python_var(name, None,
                                                      self.get_class(arg_type))
            ctr += 1
            method.add_arg(name, arg)
        if if_method['type']:
            method.type = self.get_class(if_method['type'])
        if if_method.get('generic_type'):
            method.generic_type = if_method['generic_type']
        if pure:
            cls.functions[method_name] = method
        else:
            cls.methods[method_name] = method

    def visit_module(self, module: str) -> None:
        self.visit(self.asts[module], None)

    def visit_Module(self, node: ast.Module) -> None:
        # Top level elements may only be imports, classes, functions, or global
        # var assignments.
        for stmt in node.body:
            if isinstance(stmt, (ast.ClassDef, ast.FunctionDef, ast.Import,
                                 ast.ImportFrom, ast.Assign)):
                continue
            if (isinstance(stmt, ast.Expr) and
                    isinstance(stmt.value, ast.Str)):
                # A docstring.
                continue
            if get_func_name(stmt) == 'Import':
                continue
            if get_func_name(stmt) in CONTRACT_WRAPPER_FUNCS:
                raise InvalidProgramException(stmt, 'invalid.contract.position')
            raise InvalidProgramException(stmt, 'global.statement')
        self.visit_default(node)

    def visit_default(self, node: ast.AST) -> None:
        for field in node._fields:
            fieldval = getattr(node, field)
            if isinstance(fieldval, ast.AST):
                self.visit(fieldval, node)
            elif isinstance(fieldval, list):
                for item in fieldval:
                    if isinstance(item, ast.AST):
                        self.visit(item, node)

    def visit(self, child_node: ast.AST, parent: ast.AST) -> None:
        child_node._parent = parent
        method = 'visit_' + child_node.__class__.__name__
        visitor = getattr(self, method, self.visit_default)
        visitor(child_node)

    def get_target(self, node: ast.AST, container: PythonNode) -> PythonModule:
        containers = [container]
        if isinstance(container, (PythonMethod, PythonIOOperation)):
            containers.extend(container.get_module().get_included_modules())
        else:
            containers.extend(container.get_included_modules())
        return _get_target(node, containers, container)

    def get_class(self, name: str, interface=False,
                  module=None) -> PythonClass:
        if not module:
            module = self.module
        if name in module.global_mod.classes:
            cls = module.global_mod.classes[name]
            if interface:
                cls.interface = interface
        elif name in module.classes:
            cls = module.classes[name]
            if interface:
                cls.interface = interface
        else:
            cls = self.node_factory.create_python_class(name, module,
                                                        self.node_factory,
                                                        interface=interface)
            module.classes[name] = cls
        return cls

    def get_target_class(self, node: ast.AST) -> PythonClass:
        if isinstance(node, ast.Name):
            return self.get_class(node.id)
        elif isinstance(node, ast.Attribute):
            ctx = self.get_target(node.value, self.module)
            return self.get_class(node.attr, module=ctx)
        else:
            raise UnsupportedException(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        assert self.current_class is None
        assert self.current_function is None
        name = node.name
        self.define_new(self.module, name, node)
        cls = self.get_class(name)
        cls.defined = True
        cls.node = node
        if len(node.bases) > 1:
            raise UnsupportedException(node)
        if len(node.bases) == 1:
            superclass = self.get_target_class(node.bases[0])
            cls.superclass = superclass
        else:
            cls.superclass = self.get_class(OBJECT_TYPE)
        self.current_class = cls
        for member in node.body:
            self.visit(member, node)
        self.current_class = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        assert self.current_function is None
        name = node.name
        if not isinstance(name, str):
            raise Exception(name)
        if self.is_io_operation(node):
            self.io_operation_analyzer.analyze_io_operation(node)
            return
        if self.current_class is None:
            scope_container = self.module
        else:
            scope_container = self.current_class
        self.define_new(scope_container, name, node)
        if self.is_predicate(node):
            container = scope_container.predicates
        elif self.is_pure(node):
            container = scope_container.functions
        else:
            container = scope_container.methods
        if name in container:
            func = container[name]
            if not self.is_static_method(node):
                func.cls = self.current_class
            func.pure = self.is_pure(node)
            func.node = node
            func.superscope = scope_container
        else:
            cls = self.current_class
            contract_only = self.contract_only or self.is_contract_only(node)
            func = self.node_factory.create_python_method(name, node,
                cls, scope_container, self.is_pure(node),
                contract_only, self.node_factory)
            container[name] = func
        if self.is_static_method(node):
            func.method_type = MethodType.static_method
        elif self.is_class_method(node):
            func.method_type = MethodType.class_method
            self.current_class._has_classmethod = True
        func.predicate = self.is_predicate(node)
        functype = self.module.get_func_type(func.get_scope_prefix())
        if func.pure and not functype:
            raise InvalidProgramException(node, 'function.type.none')
        func.type = self.convert_type(functype)
        self.current_function = func
        self.visit(node.args, node)
        for child in node.body:
            if is_io_existential(child):
                self._is_io_existential = True
                self.visit(child.value.args[0], node)
            else:
                self.visit(child, node)
        self.current_function = None

    def visit_loop(self, node: Union[ast.While, ast.For]) -> None:
        assert self.current_function is not None
        old_loop_invariant = self.current_loop_invariant
        self.current_function.loop_invariants[node] = []
        self.current_loop_invariant = self.current_function.loop_invariants[
            node]
        if isinstance(node, ast.While):
            self.visit(node.test, node)
        else:
            self.visit(node.target, node)
        for child in node.body:
            if is_io_existential(child):
                self._is_io_existential = True
                self.visit(child.value.args[0], node)
            else:
                self.visit(child, node)
        self.current_loop_invariant = old_loop_invariant

    def visit_While(self, node: ast.While) -> None:
        self.visit_loop(node)

    def visit_For(self, node: ast.While) -> None:
        self.visit_loop(node)

    def visit_arguments(self, node: ast.arguments) -> None:
        assert self.current_function is not None
        for arg in node.args:
            self.visit(arg, node)
        self.current_function.nargs = len(node.args)
        for kw_only in node.kwonlyargs:
            self.visit(kw_only, node)
        defaults = node.defaults
        args = list(self.current_function.args.values())
        for index in range(len(defaults)):
            arg = args[index - len(defaults)]
            arg.default = defaults[index]
        if node.vararg:
            arg = node.vararg
            annotated_type = self.typeof(arg)
            assert annotated_type.name == TUPLE_TYPE
            annotated_type.exact_length = False
            var_arg = self.node_factory.create_python_var(arg.arg, arg,
                                                          annotated_type)
            self.current_function.var_arg = var_arg
        if node.kwarg:
            arg = node.kwarg
            annotated_type = self.typeof(arg)
            kw_arg = self.node_factory.create_python_var(arg.arg, arg,
                                                         annotated_type)
            self.current_function.kw_arg = kw_arg

    def visit_Lambda(self, node: ast.Lambda) -> None:
        assert self.current_function
        name = construct_lambda_prefix(node.lineno, node.col_offset)
        self.current_scopes.append(name)
        assert not self._aliases
        for arg in node.args.args:
            if self._is_io_existential:
                var = self.node_factory.create_python_io_existential_var(
                    arg.arg, arg, self.typeof(arg))
                self._aliases[arg.arg] = var
            else:
                var = self.node_factory.create_python_var(
                    arg.arg, arg, self.typeof(arg))
            alts = self.get_alt_types(node)
            var.alt_types = alts
            local_name = name + '$' + arg.arg
            if self._is_io_existential:
                self.current_function.io_existential_vars[local_name] = var
            else:
                self.current_function.special_vars[local_name] = var
        self._is_io_existential = False
        self.visit(node.body, node)
        self.current_scopes.pop()
        self._aliases.clear()

    def visit_arg(self, node: ast.arg) -> None:
        assert self.current_function is not None
        self.current_function.args[node.arg] = \
            self.node_factory.create_python_var(node.arg, node,
                                                self.typeof(node))
        alts = self.get_alt_types(node)
        self.current_function.args[node.arg].alt_types = alts

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
        if (isinstance(node.func, ast.Name) and
                node.func.id in CONTRACT_WRAPPER_FUNCS):
            if not self.current_function or self.current_function.predicate:
                raise InvalidProgramException(node, 'invalid.contract.position')
            if node.func.id == 'Requires':
                self.current_function.precondition.append(
                    (node.args[0], self._aliases.copy()))
            elif node.func.id == 'Ensures':
                self.current_function.postcondition.append(
                    (node.args[0], self._aliases.copy()))
            elif node.func.id == 'Exsures':
                exception = self.get_target(node.args[0], self.module)
                if exception not in self.current_function.declared_exceptions:
                    self.current_function.declared_exceptions[exception] = []
                self.current_function.declared_exceptions[exception].append(
                    (node.args[1], self._aliases.copy()))
            elif node.func.id == 'Invariant':
                self.current_loop_invariant.append(
                    (node, self._aliases.copy()))
        if (isinstance(node.func, ast.Name) and
            node.func.id in IO_OPERATION_PROPERTY_FUNCS):
            raise InvalidProgramException(
                node, 'invalid.io_operation.misplaced_property')
        self.visit_default(node)

    def _get_parent_of_type(self, node: ast.AST, typ: type) -> ast.AST:
        parent = node._parent
        while not isinstance(parent, ast.Module):
            if isinstance(parent, typ):
                return parent
            parent = parent._parent
        return None

    def _get_parents_of_type(self, node: ast.AST, typ: type) -> List[ast.AST]:
        result = []
        current = self._get_parent_of_type(node, typ)
        while current:
            result.append(current)
            current = self._get_parent_of_type(current, typ)
        return result

    def visit_Name(self, node: ast.Name) -> None:
        if node.id in LITERALS:
            return
        if node.id.startswith('IOExists'):
            raise InvalidProgramException(node, 'invalid.ioexists.misplaced')
        if self._get_parent_of_type(node, ast.Call):
            return
        arg_parent = self._get_parent_of_type(node, ast.arg)
        if arg_parent:
            if arg_parent.annotation is node:
                return
        func_def_parent = self._get_parent_of_type(node, ast.FunctionDef)
        if func_def_parent:
            if func_def_parent.returns is node:
                return
            if node in func_def_parent.decorator_list:
                return
        handler_parents = self._get_parents_of_type(node, ast.ExceptHandler)
        for handler_parent in handler_parents:
            if handler_parent:
                if handler_parent.type is node:
                    return
                if handler_parent.name and handler_parent.name == node.id:
                    return
        # node could be global reference or static member
        # or local variable or function argument.
        if self.current_function is None:
            # node is global in some way.
            if self.current_class is None:
                if node.id in self.module.classes:
                    return
                # node is a global variable.
                if isinstance(node.ctx, ast.Store):
                    cls = self.typeof(node)
                    self.define_new(self.module, node.id, node)
                    existing_var = self.get_target(node, self.module)
                    if existing_var:
                        var = existing_var
                    else:
                        var = self.node_factory.create_python_global_var(
                            node.id, node, cls)
                    assign = node._parent
                    if (not isinstance(assign, ast.Assign)
                            or len(assign.targets) != 1):
                        raise UnsupportedException(assign)
                    var.value = assign.value
                    self.module.global_vars[node.id] = var
                var = self.module.global_vars[node.id]
                self.track_access(node, var)
            else:
                # node is a static field.
                cls = self.typeof(node)
                self.define_new(self.current_class, node.id, node)
                var = self.node_factory.create_python_var(node.id,
                                                          node, cls)
                assign = node._parent
                if (not isinstance(assign, ast.Assign)
                    or len(assign.targets) != 1):
                    raise UnsupportedException(assign)
                var.value = assign.value
                self.current_class.static_fields[node.id] = var
                if node.id in self.current_class.fields:
                    del self.current_class.fields[node.id]
                return
        if not isinstance(self.get_target(node, self.module), PythonGlobalVar):
            # node is a local variable, lambda argument, or a global variable
            # that hasn't been encountered yet
            var = None
            if node.id in self.current_function.locals:
                var = self.current_function.locals[node.id]
            elif node.id in self.current_function.args:
                pass
            elif node.id in self.current_function.special_vars:
                pass
            elif node.id in self.current_function.io_existential_vars:
                pass
            elif (self.current_function.var_arg and
                    self.current_function.var_arg.name == node.id):
                pass
            elif (self.current_function.kw_arg and
                    self.current_function.kw_arg.name == node.id):
                pass
            elif isinstance(self.get_target(node, self.module), PythonModule):
                return
            elif isinstance(self.get_target(node, self.module), PythonClass):
                return
            else:
                if isinstance(node.ctx, ast.Store):
                    var = self.node_factory.create_python_var(node.id,
                                                              node,
                                                              self.typeof(node))
                    alts = self.get_alt_types(node)
                    var.alt_types = alts
                    self.current_function.locals[node.id] = var
                else:
                    # this is a read of a variable we don't know, so it must
                    # be a global variable.
                    var = self.node_factory.create_python_global_var(
                        node.id, node, self.typeof(node))
                    self.module.global_vars[node.id] = var
            self.track_access(node, var)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        self.visit_default(node)
        if (not isinstance(node._parent, ast.Call) and
                not isinstance(node.value, ast.Subscript) and
                not isinstance(self.get_target(node.value, self.module),
                               PythonModule)):
            receiver = self.typeof(node.value)
            field = receiver.add_field(node.attr, node, self.typeof(node))
            self.track_access(node, field)

    def convert_type(self, mypy_type) -> PythonType:
        """
        Converts an internal mypy type to a PythonType.
        """
        if self.types.is_void_type(mypy_type):
            result = None
        elif self.types.is_instance_type(mypy_type):
            result = self.convert_type(mypy_type.type)
            if mypy_type.args:
                args = [self.convert_type(arg) for arg in mypy_type.args]
                result = GenericType(result, args)
        elif self.types.is_normal_type(mypy_type):
            prefix = mypy_type._fullname
            if prefix.endswith('.' + mypy_type.name()):
                prefix = prefix[:-(len(mypy_type.name()) + 1)]
            module = self.module
            for module in self.modules.values():
                if module.type_prefix == prefix:
                    module = module
                    break
            result = self.get_class(mypy_type.name(), module=module)
        elif self.types.is_tuple_type(mypy_type):
            args = [self.convert_type(arg_type) for arg_type in mypy_type.items]
            result = GenericType(self.module.global_mod.classes[TUPLE_TYPE],
                                 args)
        else:
            raise UnsupportedException(mypy_type)
        return result

    def get_alt_types(self, node: ast.AST) -> Dict[int, PythonType]:
        """
        If the given node refers to a local variable, returns a dict with
        the alt-types of the given variable, i.e. the types it has at other
        places where it is referenced (e.g. because a reference happens after
        an isinstance-check).
        The format is a dict that maps line numbers to types; for anything but
        references to local vars, the dict is empty.
        """
        if isinstance(node, (ast.Name, ast.arg)):
            context = []
            if self.current_class is not None:
                context.append(self.current_class.name)
            if self.current_function is not None:
                context.append(self.current_function.name)
            name = node.id if isinstance(node, ast.Name) else node.arg
            _, alts = self.module.get_type(context, name)
            result = {}
            if alts:
                for line, type in alts.items():
                    result[line] = self.convert_type(type)
            return result
        else:
            return {}

    def typeof(self, node: ast.AST) -> PythonType:
        """
        Returns the type of the given AST node.
        """
        if isinstance(node, ast.Name):
            if node.id in LITERALS:
                raise UnsupportedException(node)
            if node.id in self.module.classes:
                return self.module.classes[node.id]
            context = []
            if self.current_class is not None:
                context.append(self.current_class.name)
            if self.current_function is not None:
                context.append(self.current_function.name)
            context.extend(self.current_scopes)
            type, alts = self.module.get_type(context, node.id)
            key = (node.lineno, node.col_offset)
            if alts and key in alts:
                return self.convert_type(alts[key])
            return self.convert_type(type)
        elif isinstance(node, ast.Attribute):
            receiver = self.typeof(node.value)
            context = [receiver.name]
            type, _ = self.module.get_type(context, node.attr)
            return self.convert_type(type)
        elif isinstance(node, ast.arg):
            # special case for cls parameter of classmethods:
            if self.current_function.method_type == MethodType.class_method:
                args_list = self.current_function.node.args.args
                if args_list and node is args_list[0]:
                    cls = self.module.global_mod.classes['type']
                    arg = self.current_class
                    return GenericType(cls, [arg])
            context = []
            if self.current_class is not None:
                context.append(self.current_class.name)
            context.append(self.current_function.name)
            context.extend(self.current_scopes)
            type, _ = self.module.get_type(context, node.arg)
            return self.convert_type(type)
        elif (isinstance(node, ast.Call) and
              isinstance(node.func, ast.Name) and
              node.func.id in CONTRACT_FUNCS):
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

    def _get_basic_name(self, node: Union[ast.Name, ast.Attribute]) -> str:
        if isinstance(node, ast.Name):
            return node.id
        else:
            return self._get_basic_name(node.value)

    def visit_With(self, node: ast.With) -> None:
        assert self.current_function is not None
        self.visit_default(node)
        try_name = self.current_function.get_fresh_name('with')
        try_block = PythonTryBlock(node, try_name, self.node_factory,
                                   self.current_function, node.body)
        try_block.sil_name = try_name
        self.current_function.labels.append(try_name)
        post_name = self.current_function.get_fresh_name('post_with')
        try_block.post_name = post_name
        self.current_function.labels.append(post_name)
        finally_name = self.current_function.get_fresh_name('with_finally')
        # try_block.finally_block = node.finalbody
        if len(node.items) != 1:
            raise UnsupportedException(node)
        try_block.with_item = node.items[0]
        try_block.finally_name = finally_name
        self.current_function.labels.append(finally_name)
        self.current_function.try_blocks.append(try_block)

    def visit_Try(self, node: ast.Try) -> None:
        assert self.current_function is not None
        try_name = self.current_function.get_fresh_name('try')
        try_block = PythonTryBlock(node, try_name, self.node_factory,
                                   self.current_function, node.body)
        try_block.sil_name = try_name
        self.current_function.labels.append(try_name)
        post_name = self.current_function.get_fresh_name('post_try')
        try_block.post_name = post_name
        self.current_function.labels.append(post_name)
        self.current_function.try_blocks.append(try_block)
        for handler in node.handlers:
            handler_name = self.current_function.get_fresh_name(
                'handler' + self._get_basic_name(handler.type))
            type = self.get_target_class(handler.type)
            py_handler = PythonExceptionHandler(handler, type, try_block,
                                                handler_name, handler.body,
                                                handler.name)
            self.current_function.labels.append(handler_name)
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
            self.current_function.labels.append(finally_name)
        self.visit_default(node)

    def _incompatible_decorators(self, decorators) -> bool:
        return ((('Predicate' in decorators) and ('Pure' in decorators)) or
                (('IOOperation' in decorators) and (len(decorators) != 1)))

    def is_contract_only(self, func: ast.FunctionDef) -> bool:
        decorators = {d.id for d in func.decorator_list}
        if self._incompatible_decorators(decorators):
            raise InvalidProgramException(func, "decorators.incompatible")
        return 'ContractOnly' in decorators

    def is_pure(self, func: ast.FunctionDef) -> bool:
        decorators = {d.id for d in func.decorator_list}
        if self._incompatible_decorators(decorators):
            raise InvalidProgramException(func, "decorators.incompatible")
        return 'Pure' in decorators

    def is_predicate(self, func: ast.FunctionDef) -> bool:
        decorators = {d.id for d in func.decorator_list}
        if self._incompatible_decorators(decorators):
            raise InvalidProgramException(func, "decorators.incompatible")
        return 'Predicate' in decorators

    def is_static_method(self, func: ast.FunctionDef) -> bool:
        decorators = {d.id for d in func.decorator_list}
        if self._incompatible_decorators(decorators):
            raise InvalidProgramException(func, "decorators.incompatible")
        return 'staticmethod' in decorators

    def is_class_method(self, func: ast.FunctionDef) -> bool:
        decorators = {d.id for d in func.decorator_list}
        if self._incompatible_decorators(decorators):
            raise InvalidProgramException(func, "decorators.incompatible")
        return 'classmethod' in decorators

    def is_io_operation(self, func: ast.FunctionDef) -> bool:
        decorators = {d.id for d in func.decorator_list}
        if self._incompatible_decorators(decorators):
            raise InvalidProgramException(func, "decorators.incompatible")
        return 'IOOperation' in decorators
