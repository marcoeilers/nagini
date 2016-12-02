import abc
import ast
import mypy

from abc import ABCMeta
from collections import OrderedDict
from enum import Enum
from py2viper_contracts.io import BUILTIN_IO_OPERATIONS
from py2viper_translation.lib.constants import (
    END_LABEL,
    ERROR_NAME,
    INT_TYPE,
    INTERNAL_NAMES,
    PRIMITIVES,
    RESULT_NAME,
    STRING_TYPE,
    VIPER_KEYWORDS,
)
from py2viper_translation.lib.io_checkers import IOOperationBodyChecker
from py2viper_translation.lib.views import (
    CombinedDict,
    ModuleDictView,
)
from py2viper_translation.lib.typedefs import Expr
from py2viper_translation.lib.typeinfo import TypeInfo
from py2viper_translation.lib.util import (
    get_func_name,
    InvalidProgramException,
    UnsupportedException,
)
from typing import Any, Dict, List, Optional, Set, Tuple, Union


class ContainerInterface(metaclass=ABCMeta):
    """
    Interface implemented by PythonNodes that can contain other PythonNodes,
    and by the translation context. Enables others to get the context of
    this container.
    """
    @abc.abstractmethod
    def get_contents(self, only_top: bool) -> Dict:
        """
        Returns the elements that can be accessed from this container (to be
        used by get_target). If 'only_top' is true, returns only top level
        elements that can be accessed without a receiver.
        """


class PythonScope:
    """
    Represents a namespace/scope in Python
    """
    def __init__(self, sil_names: List[str], superscope: 'PythonScope'):
        self.sil_names = sil_names
        self.superscope = superscope

    def contains_name(self, name: str) -> bool:
        result = name in self.sil_names
        if self.superscope is not None:
            result = result or self.superscope.contains_name(name)
        return result

    def get_fresh_name(self, name: str) -> str:
        if self.contains_name(name):
            counter = 0
            new_name = name + '_' + str(counter)
            while self.contains_name(new_name):
                counter += 1
                new_name = name + '_' + str(counter)
            self.sil_names.append(new_name)
            return new_name
        else:
            self.sil_names.append(name)
            return name

    def get_scope_prefix(self) -> List[str]:
        if self.superscope is None:
            return [self.name]
        else:
            return self.superscope.get_scope_prefix() + [self.name]

    def get_module(self) -> 'PythonModule':
        if self.superscope is not None:
            return self.superscope.get_module()
        else:
            return self


class PythonModule(PythonScope, ContainerInterface):
    def __init__(self, types: TypeInfo,
                 node_factory: 'ProgramNodeFactory',
                 type_prefix: str,
                 global_module: 'PythonModule',
                 sil_names: List[str] = None) -> None:
        """
        Represents a module, i.e. either a directory that only contains other
        modules or an actual file that may contain classes, methods etc.

        :param type_prefix: The prefix identifying this module in TypeInfo.
        :param global_module: The module containing globally available elements.
        :param sil_names: List of all used Silver names, shared between modules.
        """
        if sil_names is None:
            sil_names = list(VIPER_KEYWORDS + INTERNAL_NAMES)
        super().__init__(sil_names, None)
        self.classes = OrderedDict()
        self.functions = OrderedDict()
        self.methods = OrderedDict()
        self.predicates = OrderedDict()
        self.io_operations = OrderedDict()
        self.global_vars = OrderedDict()
        self.namespaces = OrderedDict()
        self.global_module = global_module
        self.type_prefix = type_prefix
        self.from_imports = []
        self.node_factory = node_factory
        self.types = types

    def process(self, translator: 'Translator') -> None:
        if self.type_prefix:
            # If this is not the global module, add a __file__ variable
            file_var = PythonGlobalVar('__file__', None,
                                       self.global_module.classes[STRING_TYPE])
            self.global_vars['__file__'] = file_var
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
        for name, operation in self.io_operations.items():
            operation.process(self.get_fresh_name(name), translator, self)

    def get_scope_prefix(self) -> List[str]:
        return []

    def get_func_or_method(self, name: str) -> 'PythonMethod':
        for module in [self] + self.from_imports + [self.global_module]:
            if name in module.functions:
                return module.functions[name]
            elif name in module.methods:
                return module.methods[name]

    def get_type(self, prefixes: List[str],
                 name: str) -> Tuple[str, Dict[Tuple[int, int], str]]:
        """
        Returns the main type and the alternative types of the element
        identified by this name found under this prefix in the current module
        (or imported ones).
        E.g., the type of local variable 'a' from method 'm' in class 'C'
        will be returned for the input (['C', 'm'], 'a').
        """
        actual_prefix = self.type_prefix.split('.') if self.type_prefix else []
        actual_prefix.extend(prefixes)
        local_type, local_alts = self.types.get_type(actual_prefix, name)
        if local_type is not None:
            return local_type, local_alts
        for module in self.from_imports:
            module_result = module.get_type(prefixes, name)
            if module_result is not None:
                return module_result
        return None

    def get_func_type(self, path: List[str]):
        """
        Returns the type of the function identified by the given path in the
        current module (including imported other modules). It is assumed that
        the path points to a function, and the returned type will be the return
        type of that function, i.e., generally not a function type.
        """
        actual_prefix = self.type_prefix.split('.') if self.type_prefix else []
        actual_prefix.extend(path)
        local_result = self.types.get_func_type(actual_prefix)
        if local_result is not None:
            return local_result
        for module in self.from_imports:
            module_result = module.get_func_type(prefix)
            if module_result is not None:
                return module_result
        return None

    def get_included_modules(
            self, include_global: bool = True) -> List['PythonModule']:
        result = [self]
        for p in self.from_imports:
            result.extend(p.get_included_modules(include_global=False))
        result.append(self.global_module)
        return result

    def get_contents(self, only_top: bool) -> Dict:
        """
        Returns the elements that can be accessed from this container (to be
        used by get_target). If 'only_top' is true, returns only top level
        elements that can be accessed without a receiver.
        """
        dicts = [self.classes,  self.functions, self.global_vars, self.methods,
                 self.predicates, self.io_operations, self.namespaces]
        return CombinedDict([], dicts)


class PythonNode:
    def __init__(self, name: str, node=None):
        self.node = node
        self.name = name
        self.sil_name = None


class PythonType(metaclass=ABCMeta):
    """
    Abstract superclass of all kinds python types.
    """
    pass


class PythonClass(PythonType, PythonNode, PythonScope, ContainerInterface):
    """
    Represents a class in the Python program.
    """

    def __init__(self, name: str, superscope: PythonScope,
                 node_factory: 'ProgramNodeFactory', node: ast.AST = None,
                 superclass: 'PythonClass' = None, interface=False):
        """
        :param superscope: The scope, usually module, this belongs to.
        :param interface: True iff the class implementation is provided in
        native Silver.
        """
        PythonNode.__init__(self, name, node)
        PythonScope.__init__(self, VIPER_KEYWORDS + INTERNAL_NAMES, superscope)
        self.node_factory = node_factory
        self.superclass = superclass
        self.functions = OrderedDict()
        self.methods = OrderedDict()
        self.static_methods = OrderedDict()
        self.predicates = OrderedDict()
        self.fields = OrderedDict()
        self.static_fields = OrderedDict()
        self.type = None  # infer, domain type
        self.interface = interface
        self.defined = False
        self._has_classmethod = False

    def get_all_methods(self) -> Set['PythonMethod']:
        result = set()
        if self.superclass:
            result |= self.superclass.get_all_methods()
        result |= set(self.methods.keys())
        return result

    def add_field(self, name: str, node: ast.AST,
                  type: 'PythonClass') -> 'PythonField':
        """
        Adds a field with the given name and type if it doesn't exist yet in
        this class.
        """
        if name in self.fields:
            field = self.fields[name]
            assert field.type == type
        elif name in self.static_fields:
            field = self.static_fields[name]
            assert field.type == type
        else:
            field = self.node_factory.create_python_field(name, node,
                                                          type, self)
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

    def get_static_field(self, name: str) -> Optional['PythonVar']:
        """
        Returns the static field with the given name in this class or a
        superclass.
        """
        if name in self.static_fields:
            return self.static_fields[name]
        elif self.superclass is not None:
            return self.superclass.get_static_field(name)
        else:
            return None

    def get_method(self, name: str) -> Optional['PythonMethod']:
        """
        Returns the method with the given name in this class or a superclass.
        """
        if name in self.methods:
            return self.methods[name]
        elif name in self.static_methods:
            return self.static_methods[name]
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

    def get_all_fields(self) -> List['PythonField']:
        fields = []
        cls = self
        while cls is not None:
            for field in cls.fields.values():
                if field.inherited is None:
                    fields.append(field)
            cls = cls.superclass
        return fields

    def get_all_sil_fields(self) -> List['silver.ast.Field']:
        """
        Returns a list of fields defined in the given class or its superclasses.
        """
        fields = []
        cls = self
        while cls is not None:
            for field in cls.fields.values():
                if field.inherited is None:
                    fields.append(field.sil_field)
            cls = cls.superclass
        return fields

    @property
    def has_classmethod(self) -> bool:
        if self._has_classmethod:
            return True
        if self.superclass:
            return self.superclass.has_classmethod
        return False

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
        for name, method in self.static_methods.items():
            method_name = self.name + '_' + name
            method.process(self.get_fresh_name(method_name), translator)
        for name, predicate in self.predicates.items():
            pred_name = self.name + '_' + name
            predicate.process(self.get_fresh_name(pred_name), translator)
        for name, field in self.fields.items():
            field_name = self.name + '_' + name
            field.process(self.get_fresh_name(field_name))
        for name, field in self.static_fields.items():
            field_name = self.name + '_' + name
            field.process(self.get_fresh_name(field_name), translator)

    def issubtype(self, cls: 'PythonClass') -> bool:
        if cls is self:
            return True
        if self.superclass is None:
            return False
        return self.superclass.issubtype(cls)

    def get_common_superclass(self, other: 'PythonClass') -> 'PythonClass':
        """
        Returns the common superclass of both classes. Raises an error if they
        don't have any, which should never happen.
        """
        if self.issubtype(other):
            return other
        if other.issubtype(self):
            return self
        if self.superclass:
            return self.superclass.get_common_superclass(other)
        elif other.superclass:
            return self.get_common_superclass(other.superclass)
        else:
            assert False, 'Internal error: Classes without common superclass.'

    def get_contents(self, only_top: bool) -> Dict:
        """
        Returns the elements that can be accessed from this container (to be
        used by get_target). If 'only_top' is true, returns only top level
        elements that can be accessed without a receiver.
        """
        dicts = [self.functions,  self.methods, self.static_methods,
                 self.predicates]
        if not only_top:
            dicts.append(self.fields)
            dicts.append(self.static_fields)
        return CombinedDict([], dicts)


class GenericType(PythonType):
    """
    Represents a specific instantiation of a generic type, e.g. list[int].
    Provides access to the type arguments (in this case int) and otherwise
    behaves like the underlying PythonClass (in this case list).
    """

    def __init__(self, cls: PythonClass,
                 args: List[PythonType]) -> None:
        self.name = cls.name
        self.module = cls.get_module()
        self.cls = cls
        self.type_args = args
        self.exact_length = True

    def get_class(self) -> PythonClass:
        return self.cls

    def get_module(self) -> 'PythonModule':
        return self.module

    @property
    def sil_name(self) -> str:
        return self.get_class().sil_name

    @property
    def superclass(self) -> PythonClass:
        return self.get_class().superclass

    def get_field(self, name: str) -> Optional['PythonField']:
        """
        Returns the field with the given name in this class or a superclass.
        """
        return self.get_class().get_field(name)

    def get_method(self, name: str) -> Optional['PythonMethod']:
        """
        Returns the method with the given name in this class or a superclass.
        """
        return self.get_class().get_method(name)

    def get_function(self, name: str) -> Optional['PythonMethod']:
        """
        Returns the function with the given name in this class or a superclass.
        """
        return self.get_class().get_function(name)

    def get_func_or_method(self, name: str) -> Optional['PythonMethod']:
        """
        Returns the function or method with the given name in this class or a
        superclass.
        """
        return self.get_class().get_func_or_method(name)

    def get_predicate(self, name: str) -> Optional['PythonMethod']:
        """
        Returns the predicate with the given name in this class or a superclass.
        """
        return self.get_class().get_predicate(name)

    def __eq__(self, other) -> bool:
        if not isinstance(other, GenericType):
            return False
        if self.cls != other.cls or len(self.type_args) != len(other.type_args):
            return False
        for my_arg, other_arg in zip(self.type_args, other.type_args):
            if my_arg != other_arg:
                return False
        return True


class UnionType(GenericType):
    """
    A special case of a generic type for union types. Behaves like any generic
    type named 'Union' with the given type arguments in most scenarios, but
    if you look up methods/functions/..., it will give you those offered by
    the common superclass of all its arguments (which should always exist and
    be 'object' if there is no other connection).
    In the special case of an optional type, it will just give you all the
    members of the non-None option.
    """
    def __init__(self, args: List[PythonType]) -> None:
        self.name = 'Union'
        cls = args[0]
        if isinstance(cls, GenericType):
            cls = cls.cls
        for type_option in args[1:]:
            if type_option:
                if isinstance(type_option, GenericType):
                    type_option = type_option.cls
                cls = cls.get_common_superclass(type_option)
        self.cls = cls
        self.module = cls.get_module()
        self.type_args = args
        self.exact_length = True


class OptionalType(UnionType):
    """
    A special case of a union type for optional types, i.e., unions of some type
    and NoneType. Will behave like a normal union type. If you look up methods
    etc., it will behave like its type argument (e.g., Optional[C] would behave
    like C).
    """
    def __init__(self, typ: PythonType) -> None:
        super().__init__([typ])
        self.type_args = [None, typ]
        self.optional_type = typ


class MethodType(Enum):
    normal = 0
    static_method = 1
    class_method = 2


class PythonMethod(PythonNode, PythonScope, ContainerInterface):
    """
    Represents a Python function which may be pure or impure, belong
    to a class or not
    """

    def __init__(self, name: str, node: ast.AST, cls: PythonClass,
                 superscope: PythonScope,
                 pure: bool, contract_only: bool,
                 node_factory: 'ProgramNodeFactory',
                 interface: bool = False,
                 interface_dict: Dict[str, Any] = None,
                 method_type: MethodType = MethodType.normal):
        """
        :param cls: Class this method belongs to, if any.
        :param superscope: The scope (class or module) this method belongs to
        :param pure: True iff ir's a pure function, not an impure method
        :param contract_only: True iff we're not generating the method's
        implementation, just its contract
        :param interface: True iff the method implementation is provided in
        native Silver.
        """
        PythonNode.__init__(self, name, node)
        PythonScope.__init__(self, VIPER_KEYWORDS + INTERNAL_NAMES +
                             [RESULT_NAME, ERROR_NAME, END_LABEL],
                             superscope)
        if cls is not None:
            if not isinstance(cls, PythonClass):
                raise Exception(cls)
        self.cls = cls
        self.overrides = None  # infer
        self._locals = OrderedDict()  # direct
        self._args = OrderedDict()  # direct
        self._special_vars = OrderedDict()  # direct
        self._io_existential_vars = OrderedDict()
        self._nargs = -1  # direct
        self.var_arg = None   # direct
        self.kw_arg = None  # direct
        self.type = None  # infer
        self.generic_type = -1
        self.result = None  # infer
        self.error_var = None  # infer
        self.declared_exceptions = OrderedDict()  # direct
        self.precondition = []
        self.postcondition = []
        self.try_blocks = []  # direct
        self.pure = pure
        self.predicate = False
        self.contract_only = contract_only
        self.interface = interface
        self.interface_dict = interface_dict
        self.node_factory = node_factory
        self.labels = [END_LABEL]
        self.method_type = method_type
        self.obligation_info = None
        self.loop_invariants = {}   # type: Dict[Union[ast.While, ast.For], List[ast.AST]]

    def process(self, sil_name: str, translator: 'Translator') -> None:
        """
        Creates fresh Silver names for all parameters and initializes them,
        same for local variables. Also sets the method type and
        checks if this method overrides one from a superclass,
        """
        self.sil_name = sil_name
        for name, arg in self.args.items():
            arg.process(self.get_fresh_name(name), translator)
        if self.var_arg:
            self.var_arg.process(self.get_fresh_name(self.var_arg.name),
                                 translator)
        if self.kw_arg:
            self.kw_arg.process(self.get_fresh_name(self.kw_arg.name),
                                translator)
        self.obligation_info = translator.create_obligation_info(self)
        if self.interface:
            return
        func_type = self.get_module().types.get_func_type(
            self.get_scope_prefix())
        if self.type is not None:
            self.result = self.node_factory.create_python_var(RESULT_NAME, None,
                                                              self.type)
            self.result.process(RESULT_NAME, translator)
        if self.cls is not None and self.cls.superclass is not None:
            if self.predicate:
                self.overrides = self.cls.superclass.get_predicate(self.name)
            else:
                self.overrides = self.cls.superclass.get_func_or_method(
                    self.name)
        for local in self.locals:
            self.locals[local].process(self.get_fresh_name(local), translator)
        for name in self.special_vars:
            self.special_vars[name].process(self.get_fresh_name(name),
                                            translator)
        for try_block in self.try_blocks:
            try_block.process(translator)

    @property
    def nargs(self) -> int:
        if self._nargs == -1:
            return len(self.args)
        else:
            return self._nargs

    @nargs.setter
    def nargs(self, nargs: int) -> None:
        self._nargs = nargs

    @property
    def args(self) -> OrderedDict:
        # TODO(shitz): Should make this return an immutable copy.
        return self._args

    def add_arg(self, name: str, arg: 'PythonVar'):
        self._args[name] = arg

    @property
    def locals(self) -> OrderedDict:
        # TODO(shitz): Should make this return an immutable copy.
        return self._locals

    def add_local(self, name: str, local: 'PythonVar'):
        self._locals[name] = local

    @property
    def special_args(self) -> Dict:
        result = {}
        if self.kw_arg:
            result[self.kw_arg.name] = self.kw_arg
        if self.var_arg:
            result[self.var_arg.name] = self.var_arg
        return result

    @property
    def special_vars(self) -> OrderedDict:
        return self._special_vars

    @property
    def io_existential_vars(self) -> OrderedDict:
        """
        IO existential variables are variables defined by using
        ``IOExists`` construct.
        """
        return self._io_existential_vars

    def get_variable(self, name: str) -> Optional['PythonVar']:
        """
        Returns the variable (local variable or method parameter) with the
        given name.
        """
        if name in self.locals:
            return self.locals[name]
        elif name in self.args:
            return self.args[name]
        elif name in self.special_vars:
            return self.special_vars[name]
        elif name in self.io_existential_vars:
            return self.io_existential_vars[name]
        elif self.var_arg and self.var_arg.name == name:
            return self.var_arg
        elif self.kw_arg and self.kw_arg.name == name:
            return self.kw_arg
        else:
            return self.get_module().global_vars.get(name)

    def create_variable(self, name: str, cls: PythonClass,
                        translator: 'Translator',
                        local: bool=True) -> 'PythonVar':
        """
        Creates a new local variable with the given name and type and performs
        all necessary processing/initialization
        """
        sil_name = self.get_fresh_name(name)
        result = self.node_factory.create_python_var(sil_name, None, cls)
        result.process(sil_name, translator)
        if local:
            self.add_local(sil_name, result)
        return result

    def get_locals(self) -> List['PythonVar']:
        """
        Returns all method locals as a list of PythonVars.
        """
        return list(self.locals.values())

    def get_args(self) -> List['PythonVar']:
        """
        Returns all method args as a list of PythonVars.
        """
        return list(self.args.values())

    def get_results(self) -> List['PythonVar']:
        """
        Returns all results as a list of PythonVars.
        """
        if self.result:
            return [self.result]
        else:
            return []

    def get_contents(self, only_top: bool) -> Dict:
        """
        Returns the elements that can be accessed from this container (to be
        used by get_target). If 'only_top' is true, returns only top level
        elements that can be accessed without a receiver.
        """
        dicts = [self.args,  self.special_args, self.locals, self.special_vars]
        return CombinedDict([], dicts)


class PythonIOOperation(PythonNode, PythonScope, ContainerInterface):
    """
    Represents an IO operation which may be basic or not.

    +   ``preset`` – a set of input places.
    +   ``postset`` – a set of output places.
    +   ``inputs`` – inputs of IO operation (excluding preset).
    +   ``outputs`` – outputs of IO operation (excluding postset).
    """
    def __init__(
            self,
            name: str,
            node: ast.AST,
            superscope: PythonScope,
            node_factory: 'ProgramNodeFactory',
            ):
        PythonNode.__init__(self, name, node)
        PythonScope.__init__(self, [], superscope)
        self._preset = []
        self._postset = []
        self._inputs = []
        self._outputs = []
        self._terminates = None
        self._termination_measure = None
        self._body = None
        self._io_existentials = None

    @property
    def is_builtin(self) -> bool:
        return self.name in BUILTIN_IO_OPERATIONS

    def _process_var_list(self, var_list: List['PythonVar'],
                          translator: 'Translator') -> None:
        """
        Creates fresh Silver names for all variables in ``var_list``.
        """
        for var in var_list:
            var.process(self.get_fresh_name(var.name), translator)

    def process(self, sil_name: str, translator: 'Translator',
                module: PythonModule) -> None:
        """
        Creates fresh Silver names for preset, postset, inputs and
        outputs. Also, sets the ``sil_name``.
        """
        if self._body is not None:
            def find_op(node: ast.AST, containers: List, container):
                result = get_target(node, containers, container)
                if isinstance(result, PythonIOOperation):
                    return result
                return None
            body_checker = IOOperationBodyChecker(
                self._body,
                self.get_results(),
                self._io_existentials,
                module,
                translator,
                find_op)
            body_checker.check()
        self.sil_name = sil_name
        self._process_var_list(self._preset, translator)
        self._process_var_list(self._postset, translator)
        self._process_var_list(self._inputs, translator)
        self._process_var_list(self._outputs, translator)

    def set_preset(self, preset: List['PythonVar']) -> None:
        assert len(preset) == 1 or self.is_builtin
        self._preset = preset

    def set_postset(self, postset: List['PythonVar']) -> None:
        assert len(postset) == 1 or self.is_builtin
        self._postset = postset

    def set_inputs(self, inputs: List['PythonVar']) -> None:
        assert isinstance(inputs, list)
        self._inputs = inputs

    def is_input(self, name) -> bool:
        for input in self._inputs:
            if input.name == name:
                return True
        else:
            return False

    def set_outputs(self, outputs: List['PythonVar']) -> None:
        assert isinstance(outputs, list)
        self._outputs = outputs

    def set_terminates(self, expression: ast.AST) -> bool:
        """
        Set the property if it is not already set and return ``True``.
        """
        if self._terminates is None:
            self._terminates = expression
            return True
        else:
            return False

    def get_terminates(self) -> ast.AST:
        """
        Get the ``Terminates`` property.

        If it was not set, it sets a default ``False``.
        """
        if self._terminates is None:
            self._terminates = ast.NameConstant(False)
            self._terminates.lineno = self.node.lineno
            self._terminates.col_offset = self.node.col_offset
        return self._terminates

    def set_termination_measure(self, expression: ast.AST) -> bool:
        """
        Set the property if it is not already set and return ``True``.
        """
        if self._termination_measure is None:
            self._termination_measure = expression
            return True
        else:
            return False

    def get_termination_measure(self) -> ast.AST:
        """
        Get the ``TerminationMeasure`` property.

        If it was not set, it sets a default ``1``.
        """
        if self._termination_measure is None:
            self._termination_measure = ast.Num(1)
            self._termination_measure.lineno = self.node.lineno
            self._termination_measure.col_offset = self.node.col_offset
        return self._termination_measure

    def is_basic(self) -> bool:
        """
        Is this IO operation basic?
        """
        return self._body is None

    def set_body(self, expression: ast.AST) -> bool:
        """
        Set the body if it is not already set and return ``True``.
        """
        if self._body is None:
            self._body = expression
            return True
        else:
            return False

    def get_body(self) -> ast.AST:
        """
        Return IO operation body.
        """
        assert self._body is not None
        return self._body

    def set_io_existentials(
            self,
            io_existentials: List['PythonVarCreator']) -> bool:
        """
        Set io existentials list if not already set and return
        ``True``.
        """
        if self._io_existentials is None:
            self._io_existentials = io_existentials
            return True
        else:
            return False

    def get_io_existentials(self) -> List['PythonVarCreator']:
        """
        Get IO existentials.
        """
        assert self._io_existentials is not None
        return self._io_existentials

    def get_parameters(self) -> List['PythonVar']:
        """
        Return a list of parameters that uniquely identify IO operation
        instance.
        """
        return self._preset + self._inputs

    def get_results(self) -> List['PythonVar']:
        """
        Return a list of results for this IO operation.
        """
        return self._outputs + self._postset

    def get_variable(self, name: str) -> Optional['PythonVar']:
        """
        Returns the variable (existential variable or parameter) with
        the given name.
        """
        for var in self._preset:
            if var.name == name:
                return var
        for var in self._inputs:
            if var.name == name:
                return var
        for var in self._io_existentials:
            if var.name == name:
                return var.create_io_existential_variable_instance()
        return None

    def get_contents(self, only_top: bool) -> Dict:
        """
        Returns the elements that can be accessed from this container (to be
        used by get_target). If 'only_top' is true, returns only top level
        elements that can be accessed without a receiver.
        """
        return {}


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

    def __init__(self, node: ast.AST, try_name: str,
                 node_factory: 'ProgramNodeFactory',
                 method: PythonMethod,
                 protected_region: ast.AST):
        """
        :param node_factory: Factory to create PythonVar objects.
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
        self.node_factory = node_factory
        self.finally_name = None
        self.post_name = None
        self.with_item = None
        self.with_var = None
        self.handler_aliases = {}
        method.labels.append(try_name)

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
        int_type = self.method.get_module().global_module.classes[INT_TYPE]
        result = self.node_factory.create_python_var(sil_name, None,
                                                     int_type)
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
        exc_type = self.method.get_module().global_module.classes['Exception']
        result = self.node_factory.create_python_var(sil_name, None,
                                                     exc_type)
        result.process(sil_name, translator)
        self.method.locals[sil_name] = result
        self.error_var = result
        return result

    def process(self, translator: 'Translator') -> None:
        self.get_error_var(translator)
        self.get_finally_var(translator)


class PythonVarBase(PythonNode):
    """
    Abstract class representing any variable in Python.
    """

    def __init__(self, name: str, node: ast.AST, type: PythonClass):
        super().__init__(name, node)
        self.type = type
        self.writes = []
        self.reads = []
        self.alt_types = {}
        self.default = None
        self.default_expr = None

    def process(self, sil_name: str, translator: 'Translator') -> None:
        """
        Sets ``sil_name``.
        """
        self.sil_name = sil_name


class PythonVar(PythonVarBase, abc.ABC):
    """
    Represents a variable in Python. Can be a local variable or a
    function parameter.
    """

    def __init__(self, name: str, node: ast.AST, type: PythonClass):
        super().__init__(name, node, type)
        self.decl = None
        self._ref = None
        self._translator = None
        self.value = None

    def process(self, sil_name: str, translator: 'Translator') -> None:
        """
        Creates a Silver variable declaration and reference representing
        this Python variable.
        """
        super().process(sil_name, translator)
        self._translator = translator
        module = self.type.get_module()
        self.decl = translator.translate_pythonvar_decl(self, module)
        self._ref = translator.translate_pythonvar_ref(self, module, None, None)

    def ref(self, node: ast.AST=None,
            ctx: 'Context'=None) -> 'silver.ast.LocalVarRef':
        """
        Creates a reference to this variable. If no arguments are supplied,
        the reference will have no position. Otherwise, it will have the
        position of the given node in the given context.
        """
        if not node:
            return self._ref
        module = self.type.get_module()
        return self._translator.translate_pythonvar_ref(self, module, node, ctx)


class PythonGlobalVar(PythonVarBase):
    """
    Represents a global variable in Python.
    """


class PythonIOExistentialVar(PythonVarBase):
    """
    Represents an existential variable in Python. Existential variable
    is a variable created by using ``IOExists`` construct and it can be
    used only in contracts. Unlike normal variables, it is translated to
    getter functions.
    """

    def __init__(self, name: str, node: ast.AST, type: PythonClass):
        super().__init__(name, node, type)
        self._ref = None
        self._old_ref = None

    def is_defined(self) -> bool:
        """
        Returns true if main getter was already defined.
        """
        return not self._ref is None

    def ref(self, node: ast.AST = None, ctx: 'Context' = None) -> Expr:
        """
        Returns a Silver expression node that can be used to refer to
        this variable.
        """
        # TODO (Vytautas): Update to new API.
        assert not self._ref is None, self.name
        if ctx.obligation_context.is_translating_posts:
            assert not self._old_ref is None, self.name
            return self._old_ref
        else:
            return self._ref

    def set_ref(self, ref: Expr, old_ref: Optional[Expr]) -> None:
        """
        Sets a Silver expression node that can be used to refer to this
        variable.
        """
        # TODO (Vytautas): Update to new API.
        assert self._ref is None
        assert self._old_ref is None
        assert ref is not None
        self._ref = ref
        self._old_ref = old_ref


class PythonVarCreator:
    """
    A factory for Python variable. It is used instead of a concrete
    variable when the same Python variable can be translated into
    multiple silver variables. For example, when opening a non-basic IO
    operation.
    """

    def __init__(self, name: str, node: ast.AST,
                 type: PythonClass) -> None:
        self._name = name
        self._node = node
        self._type = type

        # Information needed to construct defining getter.
        self._defining_order = None     # type: Optional[int]
        self._defining_node = None
        self._defining_result = None

        # Defining getter.
        self._existential_ref = None

    @property
    def defining_order(self) -> int:
        """In what order existentials are defined?

        If the variable's defining order is ``x``, then its defining
        getter might have any existential variable with defining order
        ``y (y < x)`` as its argument.
        """
        assert self._defining_order is not None
        return self._defining_order

    @property
    def name(self) -> str:
        return self._name

    def set_defining_info(self, order: int, node: ast.Call,
                          result: PythonVar) -> None:
        """Store information needed to contstruct the defining getter."""
        assert self._defining_order is None
        assert self._defining_node is None
        assert self._defining_result is None

        self._defining_order = order
        self._defining_node = node
        self._defining_result = result

    def get_defining_info(self) -> Tuple[ast.Call, PythonVar]:
        """Retrieve information needed to contstruct the defining getter."""
        assert self._defining_order is not None
        assert self._defining_node is not None
        assert self._defining_result is not None

        return self._defining_node, self._defining_result

    def set_existential_ref(self, ref: Expr) -> None:
        """Set defining getter."""
        assert not self._existential_ref
        self._existential_ref = ref

    def create_variable_instance(self) -> PythonVar:
        """Create a normal variable.

        Normal variables are used when translating ``Open`` statement.
        """
        return PythonVar(self._name, self._node, self._type)

    def create_io_existential_variable_instance(
            self) -> PythonIOExistentialVar:
        """Create an existential variable.

        Existential variables are used when translating termination
        checks.
        """
        var = PythonIOExistentialVar(self._name, self._node, self._type)
        assert self._existential_ref
        var.set_ref(self._existential_ref, None)
        return var


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
        self._sil_field = None
        self.reads = []  # direct
        self.writes = []  # direct

    @property
    def sil_field(self) -> 'silver.ast.Field':
        return self._sil_field

    @sil_field.setter
    def sil_field(self, field: 'silver.ast.Field'):
        self._set_sil_field(field)

    def _set_sil_field(self, field: 'silver.ast.Field'):
        self._sil_field = field

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


class ProgramNodeFactory:
    """
    Factory to create Python ProgramNodes.
    
    TODO: Add more interfaces for other types of containers if needed.
    """

    def create_python_var(
            self, name: str, node: ast.AST,
            type_: PythonClass) -> PythonVar:
        return PythonVar(name, node, type_)

    def create_python_global_var(
            self, name: str, node: ast.AST,
            type_: PythonClass) -> PythonGlobalVar:
        return PythonGlobalVar(name, node, type_)

    def create_python_io_existential_var(
            self, name: str, node: ast.AST,
            type_: PythonClass) -> PythonIOExistentialVar:
        return PythonIOExistentialVar(name, node, type_)

    def create_python_var_creator(
            self, name: str, node: ast.AST,
            type_: PythonClass) -> PythonIOExistentialVar:
        return PythonVarCreator(name, node, type_)

    def create_python_method(self, name: str, node: ast.AST, cls: PythonClass,
                             superscope: PythonScope,
                             pure: bool, contract_only: bool,
                             container_factory: 'ProgramNodeFactory',
                             interface: bool = False) -> PythonMethod:
        return PythonMethod(name, node, cls, superscope, pure, contract_only,
                            container_factory, interface)

    def create_python_io_operation(self, name: str, node: ast.AST,
                                   superscope: PythonScope,
                                   container_factory: 'ProgramNodeFactory',
                                   ) -> PythonIOOperation:
        return PythonIOOperation(name, node, superscope, container_factory)

    def create_python_field(self, name: str, node: ast.AST, type_: PythonClass,
                            cls: PythonClass) -> PythonField:
        return PythonField(name, node, type_, cls)

    def create_python_class(self, name: str, superscope: PythonScope,
                            node_factory: 'ProgramNodeFactory',
                            node: ast.AST = None,
                            superclass: PythonClass = None,
                            interface=False):
        return PythonClass(name, superscope, node_factory, node,
                           superclass, interface)


def get_target(node: ast.AST,
               containers: List[ContainerInterface],
               container: PythonNode) -> PythonNode:
    """
    Finds the PythonNode that the given 'node' refers to, e.g. a PythonClass or
    a PythonVar, if the immediate container (e.g. a PythonMethod) of the node
    is 'container', by looking in the given 'containers' (can be e.g.
    PythonMethods, the Context, PythonModules, etc).
    """
    if isinstance(node, ast.Name):
        # Just look for something with this name in the given containers
        for lhs in containers:
            if lhs:
                # Since this is a direct reference, only top level elements
                # can be relevant.
                options = lhs.get_contents(only_top=True)
                if node.id in options:
                    return options[node.id]
        return None
    elif isinstance(node, ast.Call):
        # For calls, we return the type of the result of the call
        func_name = get_func_name(node)
        if (container and func_name == 'Result' and
                isinstance(container, PythonMethod)):
            # In this case the immediate container must be a method, and we
            # return its result type
            return container.type
        elif (container and func_name == 'super' and
                isinstance(container, PythonMethod)):
            # Return the type of the current method's superclass
            return container.cls.superclass
        elif func_name == 'cast':
            return get_target(node.args[0], containers, container)
        return get_target(node.func, containers, container)
    elif isinstance(node, ast.Attribute):
        # Find the type of the LHS, so that we can look through its members.
        lhs = get_target(node.value, containers, container)
        if (isinstance(lhs, PythonMethod) or
                isinstance(lhs, PythonField)):
            # For methods, get the return type, for fields the field type
            lhs = lhs.type
        elif isinstance(lhs, PythonVarBase):
            # For variables, the type of the variable
            col = node.col_offset if hasattr(node, 'col_offset') else None
            key = (node.lineno, col)
            if key in lhs.alt_types:
                lhs = lhs.alt_types[key]
            else:
                lhs = lhs.type
        if isinstance(lhs, OptionalType):
            lhs = lhs.optional_type
        if isinstance(lhs, UnionType):
            # It's a regular union type; we don't support that at the
            # moment.
            raise UnsupportedException(node, 'Member access on union type.')
        if isinstance(lhs, GenericType) and lhs.name == 'type':
            # For direct references to type objects, we want to lookup things
            # defined in the class. So instead of type[C], we want to look in
            # class C directly here.
            lhs = lhs.type_args[0]
        if isinstance(lhs, GenericType):
            # Use the class, since we want to look for members.
            lhs = lhs.cls
        # Now collect all containers we have to look through
        containers = []
        if isinstance(lhs, PythonModule):
            # We have to look through all included modules as well, but not
            # through the global one, since it makes no sense to refer to
            # global stuff by looking in a different module
            containers.extend(lhs.get_included_modules(include_global=False))
        else:
            containers.append(lhs)
        while (isinstance(containers[-1], PythonClass) and
                containers[-1].superclass):
            # If we're looking in a class, add all superclasses as well.
            containers.append(containers[-1].superclass)
        for lhs in containers:
            if lhs:
                # Look in all contents, including non-top-level
                options = lhs.get_contents(only_top=False)
                if node.attr in options:
                    return options[node.attr]
        return None
    else:
        return None
