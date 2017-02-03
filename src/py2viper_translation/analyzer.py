import ast
import logging
import mypy
import os
import py2viper_contracts.io_builtins
import py2viper_contracts.lock
import py2viper_translation.external.astpp
import tokenize

from collections import OrderedDict
from py2viper_contracts.contracts import CONTRACT_FUNCS, CONTRACT_WRAPPER_FUNCS
from py2viper_contracts.io import IO_OPERATION_PROPERTY_FUNCS
from py2viper_translation.analyzer_io import IOOperationAnalyzer
from py2viper_translation.external.ast_util import mark_text_ranges
from py2viper_translation.lib.constants import (
    IGNORED_IMPORTS,
    LITERALS,
    OBJECT_TYPE,
    TUPLE_TYPE,
    UNION_TYPE,
)
from py2viper_translation.lib.program_nodes import (
    ContainerInterface,
    GenericType,
    MethodType,
    OptionalType,
    ProgramNodeFactory,
    PythonClass,
    PythonExceptionHandler,
    PythonGlobalVar,
    PythonIOOperation,
    PythonModule,
    PythonNode,
    PythonTryBlock,
    PythonType,
    PythonVar,
    PythonMethod,
    TypeVar,
    UnionType,
)
from  py2viper_translation.lib.resolver import get_target as do_get_target
from py2viper_translation.lib.typeinfo import TypeInfo
from py2viper_translation.lib.util import (
    construct_lambda_prefix,
    get_func_name,
    get_parent_of_type,
    InvalidProgramException,
    is_io_existential,
    UnsupportedException,
)
from py2viper_translation.lib.views import PythonModuleView
from typing import Dict, List, Optional, Set, Tuple, Union


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
        self.global_module = PythonModule(types, node_factory, None, None)
        self.global_module.global_module = self.global_module
        self.module = PythonModule(types, node_factory, '__main__',
                                   self.global_module,
                                   sil_names=self.global_module.sil_names)
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
            if (name in container.global_vars and
                    hasattr(container.global_vars[name], 'value')):
                raise InvalidProgramException(node, 'multiple.definitions')
        if (name in container.functions or
                    name in container.methods or
                    name in container.predicates or
                    (isinstance(container, PythonClass) and
                    name in container.static_methods)):
            raise InvalidProgramException(node, 'multiple.definitions')

    def collect_imports(self, abs_path: str) -> None:
        """
        Parses the file at the given location, puts the result into self.asts.
        Scans the parsed file for Import-statements and adds all imported paths
        to self.modules.
        """
        if abs_path.startswith('mod$'):
            # This is a module that corresponds to a directory, so it has no
            # contents of its own.
            return
        with tokenize.open(abs_path) as file:
            text = file.read()
        parse_result = ast.parse(text)
        try:
            mark_text_ranges(parse_result, text)
        except Exception:
            # Ignore
            pass
        self.asts[abs_path] = parse_result
        logger.debug(py2viper_translation.external.astpp.dump(parse_result))
        assert isinstance(parse_result, ast.Module)
        imports = [s for s in parse_result.body
                   if isinstance(s, (ast.Import, ast.ImportFrom))]
        for stmt in parse_result.body:
            if isinstance(stmt, ast.Import):
                for name in stmt.names:
                    module_name = name.name
                    if module_name in IGNORED_IMPORTS:
                        continue
                    redefined_name = name.asname
                    if not redefined_name:
                        redefined_name = module_name
                    assert module_name in self.types.files
                    path = self.types.files[module_name]
                    self.add_module(path, abs_path, redefined_name)
            elif isinstance(stmt, ast.ImportFrom):
                module_name = stmt.module
                if module_name in IGNORED_IMPORTS:
                    continue
                if module_name == 'py2viper_contracts.io_builtins':
                    path = py2viper_contracts.io_builtins.__file__
                elif module_name == 'py2viper_contracts.lock':
                    path = py2viper_contracts.lock.__file__
                else:
                    assert module_name in self.types.files
                    path = self.types.files[module_name]
                if len(stmt.names) == 1 and stmt.names[0].name == '*':
                    names = None
                else:
                    names = [(name.name, name.asname if name.asname else None)
                             for name in stmt.names] # TODO rename?
                self.add_module(path, abs_path, None, names)

    def add_module(self, abs_path: str, into: str, as_name: Optional[str],
                   names: List[Tuple[str, str]] = None) -> None:
        """
        Adds the module with the given 'abs_path' into the the module with
        path 'into'. If it's a from-import, 'as_name' should be None and
        'names' may contain rename information for specific imported
        members, otherwise (with a normal import) as_name should contain the
        name under which the module is imported.
        """
        if as_name and '.' in as_name:
            # Imported multi.part.name, add part by part
            split = as_name.split('.', 1)
            first = split[0]
            rest = split[1]
            # Add first part into original module. The first part must
            # correspond to a directory, so it has no contents of its own,
            # and we just create a dummy module (indicated by the path starting
            # with 'mod$') that's just there to contain the following module(s).
            self.add_module('mod$' + first, into, first)
            # Add next part(s) into first part recursively
            self.add_module(abs_path, 'mod$' + first, rest)
            return
        if abs_path not in self.module_paths:
            # Module has not been imported yet
            self.module_paths.append(abs_path)
            type_prefix = self.types.get_type_prefix(abs_path)
            new_module = PythonModule(self.module.types, self.node_factory,
                                      type_prefix, self.module.global_module,
                                      self.module.sil_names)
            self.modules[abs_path] = new_module
        else:
            new_module = self.modules[abs_path]
        into_mod = self.modules[into]
        if as_name:
            assert not names
            into_mod.namespaces[as_name] = new_module
        else:
            if names:
                new_module = PythonModuleView(new_module, names)
            into_mod.from_imports.append(new_module)

    def process(self, translator: 'Translator') -> None:
        """
        Performs preprocessing on the result of the analysis, which infers some
        things, creates some data structures for the translation etc.
        """
        self.module.global_module.process(translator)
        for module in self.modules.values():
            module.process(translator)

    def add_native_silver_builtins(self, interface: Dict) -> None:
        """
        Adds the classes, methods and functions in the interface-dict to
        the program. Meant to be used with a dict containing all methods/...
        that have native Silver representations and won't be created by the
        translator.
        """
        # Create global classes first
        for class_name in interface:
            cls = self.find_or_create_class(class_name,
                                            module=self.module.global_module)
            cls.interface = True
            cls.defined = True
        for class_name in interface:
            cls = self.find_or_create_class(class_name)
            if_cls = interface[class_name]
            if 'type_vars' in if_cls:
                for i in range(if_cls['type_vars']):
                    name = 'var' + str(i)
                    cls.type_vars[name] = TypeVar(name, cls, None, i, None, [],
                                                  None)
            if 'extends' in if_cls:
                superclass = self.find_or_create_class(if_cls['extends'],
                    module=self.module.global_module)
                cls.superclass = superclass
            for method_name in if_cls.get('methods', []):
                if_method = if_cls['methods'][method_name]
                self._add_native_silver_method(method_name, if_method, cls,
                                               False)
            for method_name in if_cls.get('functions', []):
                if_method = if_cls['functions'][method_name]
                self._add_native_silver_method(method_name, if_method, cls,
                                               True)
            for pred_name in if_cls.get('predicates', []):
                if_pred = if_cls['predicates'][pred_name]
                self._add_native_silver_method(pred_name, if_pred, cls,
                                               True, True)

    def _add_native_silver_method(self, method_name: str, if_method: str,
                                  cls: PythonClass, pure: bool,
                                  predicate: bool = False) -> None:
        method = PythonMethod(method_name, None, cls, self.module,
                              pure, False, self.node_factory, True,
                              if_method)
        ctr = 0
        for arg_type in if_method['args']:
            name = 'arg_' + str(ctr)
            arg = self.node_factory.create_python_var(name, None,
                self.find_or_create_class(arg_type))
            ctr += 1
            method.add_arg(name, arg)
        if if_method['type']:
            method.type = self.find_or_create_class(if_method['type'])
        if if_method.get('generic_type'):
            method.generic_type = if_method['generic_type']
        if if_method.get('requires'):
            method.requires = if_method['requires']
        if predicate:
            cls.predicates[method_name] = method
        elif pure:
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

    def get_target(self, node: ast.AST,
                   container: ContainerInterface) -> PythonNode:
        """
        Finds the PythonNode that the given 'node' refers to, e.g. a PythonClass
        or a PythonVar, if the immediate container (e.g. a PythonMethod) of the
        node is 'container'.
        """
        containers = [container]
        if isinstance(container, (PythonMethod, PythonIOOperation)):
            containers.extend(container.get_module().get_included_modules())
        else:
            containers.extend(container.get_included_modules())
        return do_get_target(node, containers, container)

    def find_or_create_class(self, name: str, module=None) -> PythonClass:
        """
        Gets the class with the given 'name' from the given 'module' (or the
        current module if none is provided). If no such class exists, one will
        be created.
        """
        # If the name refers to a type alias from the typing module, get
        # the actual name
        aliases = {'List': 'list',
                   'Tuple': 'tuple',
                   'Set': 'set',
                   'Dict': 'dict',
                   'Type': 'type',}
        name = aliases.get(name, name)
        if self.current_class and name in self.current_class.type_vars:
            return self.current_class.type_vars[name]
        if not module:
            module = self.module
        if name in module.global_module.classes:
            cls = module.global_module.classes[name]
        elif name in module.classes:
            cls = module.classes[name]
        else:
            cls = self.node_factory.create_python_class(name, module,
                                                        self.node_factory)
            module.classes[name] = cls
        return cls

    def find_or_create_target_class(self, node: ast.AST) -> PythonClass:
        """
        Assuming that the given node is a reference to a class, retrieves the
        PythonClass object if it already exists, otherwise creates one.
        """
        if isinstance(node, ast.Name):
            return self.find_or_create_class(node.id)
        elif isinstance(node, ast.Attribute):
            ctx = self.get_target(node.value, self.module)
            return self.find_or_create_class(node.attr, module=ctx)
        elif isinstance(node, ast.Subscript):
            cls = self.find_or_create_target_class(node.value)
            if isinstance(node.slice.value, ast.Name):
                ast_args = [node.slice.value]
            else:
                ast_args = node.slice.value.elts
            args = [self.find_or_create_target_class(arg) for arg in ast_args]
            result = GenericType(cls, args)
            return result
        else:
            raise UnsupportedException(node,
                                       'class literal has unsupported format')

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if self.current_function or self.current_class:
            raise UnsupportedException(node, 'nested class declaration')
        name = node.name
        self.define_new(self.module, name, node)
        cls = self.find_or_create_class(name)
        cls.defined = True
        cls.node = node
        self.current_class = cls
        actual_bases = []
        current_index = 0
        for base in node.bases:
            if isinstance(base, ast.Subscript) and base.value.id == 'Generic':
                if isinstance(base.slice.value, ast.Name):
                    arg_names = [base.slice.value.id]
                else:
                    arg_names = [elmt.id for elmt in base.slice.value.elts]
                for arg_name in arg_names:
                    assert arg_name in self.module.type_vars
                    var_info = self.module.type_vars[arg_name]
                    bound = self.convert_type(var_info[0])
                    options = [self.convert_type(typ) for typ in var_info[1]]
                    var = TypeVar(arg_name, cls, None, current_index, bound,
                                  options, base)
                    cls.type_vars[arg_name] = var
                    current_index += 1
            else:
                actual_bases.append(base)
        if len(actual_bases) > 1:
            raise UnsupportedException(node, 'multiple inheritance')
        if len(actual_bases) == 1:
            cls.superclass = self.find_or_create_target_class(actual_bases[0])
        else:
            cls.superclass = self.find_or_create_class(OBJECT_TYPE)

        for member in node.body:
            self.visit(member, node)
        self.current_class = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if self.current_function:
            raise UnsupportedException(node, 'nested function declaration')
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
        elif self.is_static_method(node):
            container = scope_container.static_methods
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
            contract_only = self.contract_only or self.is_contract_only(node)
            func = self.node_factory.create_python_method(name, node,
                self.current_class, scope_container, self.is_pure(node),
                contract_only, self.node_factory)
            container[name] = func
        if self.is_static_method(node):
            func.method_type = MethodType.static_method
        elif self.is_class_method(node):
            func.method_type = MethodType.class_method
            self.current_class._has_classmethod = True
        func.predicate = self.is_predicate(node)

        # TODO: create type vars
        functype = self.module.get_func_type(func.get_scope_prefix())
        if func.pure and not functype:
            raise InvalidProgramException(node, 'function.type.none')
        self.current_function = func
        func.type = self.convert_type(functype)

        self.visit(node.args, node)
        for child in node.body:
            if is_io_existential(child):
                self._is_io_existential = True
                self.visit(child.value.args[0], node)
            else:
                self.visit(child, node)
        self.current_function = None

    def visit_loop(self, node: Union[ast.While, ast.For]) -> None:
        if not self.current_function:
            raise UnsupportedException(node, 'top level loop')
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
        if node.orelse:
            for stmt in node.orelse:
                self.visit(stmt, node)
        self.current_loop_invariant = old_loop_invariant

    def visit_While(self, node: ast.While) -> None:
        self.visit_loop(node)

    def visit_For(self, node: ast.While) -> None:
        self.visit_loop(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        alias = False
        type_var = False
        # Check if this is a type alias
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            lhs_name = (self.module.type_prefix, node.targets[0].id)
            # If it's a type alias marked by mypy
            if lhs_name in self.types.type_aliases:
                type_name = self.types.type_aliases[lhs_name]
                aliased_type = self.convert_type(type_name)
                self.module.classes[node.targets[0].id] = aliased_type
                alias = True
            # If it's a type variable markes by mypy
            elif lhs_name in self.types.type_vars:
                var = self.types.type_vars[lhs_name]
                self.module.type_vars[node.targets[0].id] = var
                type_var = True
            # Could still be a type alias if RHS refers to class
            elif not isinstance(node.value, ast.Call):
                target = self.get_target(node.value, self.module)
                if isinstance(target, PythonType):
                    self.module.classes[node.targets[0].id] = target
                    alias = True

        # Nothing else to do for type aliases and type vars,, for all other
        # cases proceed as usual.
        if alias:
            if self.current_function or self.current_class:
                raise InvalidProgramException(node, 'local.type.alias')
        elif type_var:
            if self.current_function or self.current_class:
                raise InvalidProgramException(node, 'local.typevar')
        else:
            self.visit_default(node)

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
            # For IO operation arguments, we want parameters to be primitive
            # b/c primitive equality is simpler than boxed reference equality,
            # and for simplicity we use the same policy for output params too.
            if self._is_io_existential:
                arg_type = self.typeof(arg).try_unbox()
                var = self.node_factory.create_python_io_existential_var(
                    arg.arg, arg, arg_type)
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
        """
        Collects preconditions, postconditions, raised exceptions and
        invariants.
        """
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
        """
        Returns the closest parent node of 'node' that is of the given type
        (e.g. ast.Name), or None if there is no such node.
        """
        parent = node._parent
        while not isinstance(parent, ast.Module):
            if isinstance(parent, typ):
                return parent
            parent = parent._parent
        return None

    def _get_parents_of_type(self, node: ast.AST, typ: type) -> List[ast.AST]:
        """
        Returns all parent nodes of 'node' that are of the given type (e.g.
        ast.Name), sorted from bottom (closest to 'node') to the top of the
        tree. If there is no such parent node, the returned list will be empty.
        """
        result = []
        current = get_parent_of_type(node, typ)
        while current:
            result.append(current)
            current = get_parent_of_type(current, typ)
        return result

    def visit_Name(self, node: ast.Name) -> None:
        """
        This method tracks all local variables, global variables,
        lambda arguments and static fields in the program and creates the
        corresponding PythonNodes.
        """
        # Since lots of things in the AST (that we don't care about here) are
        # also ast.Names, we filter out those cases first.
        if node.id in LITERALS:
            return
        if node.id.startswith('IOExists'):
            raise InvalidProgramException(node, 'invalid.ioexists.misplaced')
        if get_parent_of_type(node, ast.Call):
            return
        arg_parent = get_parent_of_type(node, ast.arg)
        if arg_parent:
            if arg_parent.annotation is node:
                # We're looking at a parameter type annotation
                return
        func_def_parent = get_parent_of_type(node, ast.FunctionDef)
        if func_def_parent:
            if func_def_parent.returns is node:
                # We're looking at a return type annotation
                return
            if node in func_def_parent.decorator_list:
                # We're looking at a decorator
                return
        handler_parents = self._get_parents_of_type(node, ast.ExceptHandler)
        for handler_parent in handler_parents:
            if handler_parent:
                if handler_parent.type is node:
                    # We're looking at an exception type that's caught
                    return
                if handler_parent.name and handler_parent.name == node.id:
                    # We're looking at an alias for a caught exception,
                    # those are handled along with the try-block itself.
                    return
        # Node could be global reference or static member
        # or local variable or function argument.
        if self.current_function is None:
            # Node is global in some way.
            if self.current_class is None:
                if node.id in self.module.classes:
                    return
                # Node is a global variable.
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
                        msg = ('only simple assignments and reads allowed for '
                               'global variables')
                        raise UnsupportedException(assign, msg)
                    var.value = assign.value
                    self.module.global_vars[node.id] = var
                var = self.module.global_vars[node.id]
                self.track_access(node, var)
            else:
                # Node is a static field.
                cls = self.typeof(node)
                self.define_new(self.current_class, node.id, node)
                var = self.node_factory.create_python_var(node.id,
                                                          node, cls)
                assign = node._parent
                if (not isinstance(assign, ast.Assign)
                        or len(assign.targets) != 1):
                    msg = ('only simple assignments and reads allowed for '
                           'static fields')
                    raise UnsupportedException(assign, msg)
                var.value = assign.value
                self.current_class.static_fields[node.id] = var
                if node.id in self.current_class.fields:
                    # It's possible that we encountered a read of this field
                    # before seeing the definition, assumed it's a normal
                    # (non-static) field, and created the field. We remove it
                    # again now that we now it's actually static.
                    del self.current_class.fields[node.id]
                return
        if not isinstance(self.get_target(node, self.module), PythonGlobalVar):
            # Node is a local variable, lambda argument, or a global variable
            # that hasn't been encountered yet
            var = None
            # First check if the node refers to something local that we already
            # know; in that case we don't have to do anything
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
                # We don't know this identifier yet, so it must be something
                # new
                if isinstance(node.ctx, ast.Store):
                    # Assume it's the first write to a local variable
                    var = self.node_factory.create_python_var(node.id,
                                                              node,
                                                              self.typeof(node))
                    alts = self.get_alt_types(node)
                    var.alt_types = alts
                    self.current_function.locals[node.id] = var
                else:
                    # This is a read of a variable we don't know, so it must
                    # be a global variable whose definition comes after the
                    # current method. Any local variable would first be accessed
                    # with a write.
                    var = self.node_factory.create_python_global_var(
                        node.id, node, self.typeof(node))
                    self.module.global_vars[node.id] = var
            self.track_access(node, var)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """
        Tracks field accesses to find out which fields exist.
        """
        self.visit_default(node)
        # If the LHS of this attribute is a module, or if this
        # is part of a complex expression and it's guaranteed that the field
        # is also accessed in a simpler expression elsewhere, we just do
        # nothing here.
        if (not isinstance(node._parent, ast.Call) and
                not isinstance(node.value, ast.Subscript) and
                not isinstance(self.get_target(node.value, self.module),
                               PythonModule)):
            test = self.get_target(node.value, self.module)
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
            target_module = self.module
            for module in self.modules.values():
                if module.type_prefix == prefix:
                    target_module = module
                    break
            result = self.find_or_create_class(mypy_type.name(),
                                               module=target_module)
        elif self.types.is_tuple_type(mypy_type):
            args = [self.convert_type(arg_type) for arg_type in mypy_type.items]
            result = GenericType(self.module.global_module.classes[TUPLE_TYPE],
                                 args)
        elif self.types.is_none_type(mypy_type):
            result = None
        elif self.types.is_union_type(mypy_type):
            args = [self.convert_type(arg_type) for arg_type in mypy_type.items]
            optional = False
            if None in args:
                # It's an optional type, remember this and wrap it later
                optional = True
                args.remove(None)
            if len(args) > 1:
                result = UnionType(args)
            else:
                result = args[0]
            if optional:
                result = OptionalType(result)
        elif self.types.is_type_var(mypy_type):
            name = mypy_type.name
            assert name in self.module.type_vars
            if name in self.current_function.type_vars:
                return self.current_function.type_vars[name]
            elif (self.current_class and name in self.current_class.type_vars):
                return self.current_class.type_vars[name]
            else:
                assert False, 'Unknown type variable'

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
            # Special case for cls parameter of classmethods; for those, we
            # return the type 'type[C]', where C is the class the method
            # belongs to.
            if self.current_function.method_type == MethodType.class_method:
                args_list = self.current_function.node.args.args
                if args_list and node is args_list[0]:
                    cls = self.module.global_module.classes['type']
                    return GenericType(cls, [self.current_class])
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
        """
        For a reference.of.this.kind, returns the last part ('kind' in this
        case).
        """
        if isinstance(node, ast.Name):
            return node.id
        else:
            return self._get_basic_name(node.value)

    def visit_With(self, node: ast.With) -> None:
        """
        With-blocks get translated to try-finally-blocks, so we create a
        PythonTryBlock here.
        """
        if not self.current_function:
            raise UnsupportedException(node, 'top level with statement')
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
        if len(node.items) != 1:
            msg = 'with block may only have one item'
            raise UnsupportedException(node, msg)
        try_block.with_item = node.items[0]
        try_block.finally_name = finally_name
        self.current_function.labels.append(finally_name)
        self.current_function.try_blocks.append(try_block)

    def visit_Try(self, node: ast.Try) -> None:
        """
        Creates PythonTryBlocks and PythonExceptionHandlers.
        """
        if not self.current_function:
            raise UnsupportedException(node, 'top level try statement')
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
            if handler.type:
                handler_type = self.find_or_create_target_class(handler.type)
            else:
                # Handler has no explicit type, therefore catches any kind
                # of exception.
                handler_type = self.module.global_module.classes['Exception']
            handler_name = self.current_function.get_fresh_name(
                'handler' + handler_type.name)
            py_handler = PythonExceptionHandler(handler, handler_type,
                                                try_block, handler_name,
                                                handler.body, handler.name)
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
