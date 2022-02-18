"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import abc
import ast

from abc import ABCMeta
from collections import OrderedDict
from enum import Enum
from nagini_contracts.io_contracts import BUILTIN_IO_OPERATIONS
from nagini_translation.lib.constants import (
    BOXED_PRIMITIVES,
    CALLABLE_TYPE,
    END_LABEL,
    ERROR_NAME,
    INTERNAL_NAMES,
    MODULE_VARS,
    PMSET_TYPE,
    PRIMITIVE_INT_TYPE,
    PRIMITIVE_PREFIX,
    PRIMITIVE_SEQ_TYPE,
    PRIMITIVE_SET_TYPE,
    PRIMITIVES,
    PSEQ_TYPE,
    PSET_TYPE,
    RESULT_NAME,
    STRING_TYPE,
    VIPER_KEYWORDS,
)
from nagini_translation.lib.io_checkers import IOOperationBodyChecker
from nagini_translation.lib.typedefs import Expr, Stmt
from nagini_translation.lib.typeinfo import TypeInfo
from nagini_translation.lib.util import (
    get_column,
    InvalidProgramException,
    SingletonFreshName,
)
from nagini_translation.lib.views import (
    CombinedDict,
    IOOperationContentDict,
)
from typing import Any, Dict, List, Optional, Set, Tuple
from toposort import toposort_flatten


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
    def __init__(self, sil_names: Set[str], superscope: 'PythonScope'):
        self.sil_names = sil_names
        self.superscope = superscope
        self._module = None

    def contains_name(self, name: str) -> bool:
        if self.sil_names is not None:
            result = name in self.sil_names
        else:
            result = self.superscope.contains_name(name)
        return result

    def get_fresh_name(self, name: str) -> str:
        if self.contains_name(name):
            counter = 0
            new_name = name + '_' + str(counter)
            while self.contains_name(new_name):
                counter += 1
                new_name = name + '_' + str(counter)
            self._add_name(new_name)
            return new_name
        else:
            self._add_name(name)
            return name

    def _add_name(self, new_name: str) -> None:
        if self.sil_names is not None:
            self.sil_names.add(new_name)
        else:
            self.superscope._add_name(new_name)

    @property
    def scope_prefix(self) -> List[str]:
        if self.superscope is None:
            return [self.name]
        else:
            return self.superscope.scope_prefix + [self.name]

    @property
    def module(self) -> 'PythonModule':
        if self._module is not None:
            return self._module
        if self.superscope is not None:
            return self.superscope.module
        else:
            return self


class PythonStatementContainer:
    """
    Class to be mixed into any node that contains executable statements (currently methods
    and modules). Stores the analyzer information related to those statements.
    """
    def __init__(self):
        self.labels = [END_LABEL]
        self.precondition = []
        self.postcondition = []
        self.try_blocks = []  # direct
        self.loop_invariants = {}   # type: Dict[Union[ast.While, ast.For], List[ast.AST]]


class PythonModule(PythonScope, ContainerInterface, PythonStatementContainer):
    def __init__(self, types: TypeInfo,
                 node_factory: 'ProgramNodeFactory',
                 type_prefix: str,
                 global_module: 'PythonModule',
                 node: ast.Module,
                 sil_names: Set[str] = None,
                 file: str = None) -> None:
        """
        Represents a module, i.e. either a directory that only contains other
        modules or an actual file that may contain classes, methods etc.

        :param type_prefix: The prefix identifying this module in TypeInfo.
        :param global_module: The module containing globally available elements.
        :param sil_names: Set of all used Silver names, shared between modules.
        """
        if sil_names is None:
            sil_names = set(VIPER_KEYWORDS + INTERNAL_NAMES)
            sil_names |= set([RESULT_NAME, ERROR_NAME, END_LABEL])
        PythonScope.__init__(self, sil_names, None)
        PythonStatementContainer.__init__(self)
        self.node = node
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
        self.type_vars = OrderedDict()
        self.file = file
        self.defined_var = None
        self.names_var = None
        if global_module and type_prefix != '__main__':
            self.add_builtin_vars()

    def add_builtin_vars(self) -> None:
        """
        Adds builtin variables that are defined in every module.
        """
        file_var = PythonGlobalVar('__file__', None,
                                   self.global_module.classes[STRING_TYPE], self)
        self.global_vars['__file__'] = file_var
        name_var = PythonGlobalVar('__name__', None,
                                   self.global_module.classes[STRING_TYPE], self)
        self.global_vars['__name__'] = name_var


    def process(self, translator: 'Translator') -> None:
        self.sil_name = self.get_fresh_name('module')
        defined_var_name = self.get_fresh_name('module_defined')
        self.defined_var = defined_var_name
        names_var_name = self.get_fresh_name('module_names')
        self.names_var = names_var_name

        for name, cls in self.classes.items():
            if name == cls.name:
                # if this is not a type alias
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

    @property
    def scope_prefix(self) -> List[str]:
        return []

    def get_func_or_method(self, name: str) -> 'PythonMethod':
        for module in [self] + self.from_imports + [self.global_module]:
            if not isinstance(module, PythonModule):
                # It's a ModuleView, we take the actual module wrapped by it.
                module = module.module
            if name in module.functions:
                return module.functions[name]
            elif name in module.methods:
                return module.methods[name]

    def get_type(self, prefixes: List[str], name: str,
                 previous: Tuple['PythonModule', ...] = ()) -> Tuple[str,
                                                                     Dict[Tuple[int, int],
                                                                          str]]:
        """
        Returns the main type and the alternative types of the element
        identified by this name found under this prefix in the current module
        (or imported ones).
        E.g., the type of local variable 'a' from method 'm' in class 'C'
        will be returned for the input (['C', 'm'], 'a').
        """
        if self in previous:
            return None, None
        actual_prefix = self.type_prefix.split('.') if self.type_prefix else []
        actual_prefix.extend(prefixes)
        local_type, local_alts = self.types.get_type(actual_prefix, name)
        if local_type is not None:
            return local_type, local_alts
        return None, None

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
            module_result = module.get_func_type(path)
            if module_result is not None:
                return module_result
        return None

    def get_included_modules(self, exclude: Set['PythonModule'] = (),
                             include_global: bool = True) -> List['PythonModule']:
        """
        Returns a list of modules whose contents are (transitively) available in the this
        module, optionally including the global module, but excluding the modules in the
        given set (to prevent infinite recursion in case of cyclic imports).
        """
        result = [self]
        for p in self.from_imports:
            result.extend(p.get_included_modules(exclude + (self,),
                                                 include_global=False))
        if include_global:
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

    def try_box(self) -> 'PythonType':
        """
        If this class represents a primitive type, returns the boxed version,
        otherwise just return the type itself.
        """
        # By default, just return self. Subclasses can override.
        return self

    def try_unbox(self) -> 'PythonType':
        """
        If this class represents a boxed version of a primitive type, returns
        the primitive version, otherwise just returns the type itself.
        """
        # By default, just return self. Subclasses can override.
        return self


class SilverType(PythonType):
    """
    Wrapper around a Silver type. Only used for creating local variables with types not
    present in Python.
    """
    def __init__(self, type, module):
        self.type = type
        self.module = module


class TypeVar(PythonType, ContainerInterface):
    """
    Represents a type variable.
    """

    def __init__(self, name: str, bound: PythonType,
                 module: PythonModule, target_type: PythonType = None,
                 target_node: ast.AST = None,
                 index: int = None):
        """
        For class parameters, supply target_type, target_node and index. For
        method parameters, supply the defining node as target_node and later
        set self.type_expr.
        """
        self.name = name
        self.target_type = target_type
        self.target_node = target_node
        self.index = index
        self.bound = bound
        self.type_expr = None
        self.module = module

    def get_contents(self, only_top: bool) -> Dict:
        return self.bound.get_contents(only_top)

    @property
    def python_class(self) -> 'PythonClass':
        return self.bound


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
        PythonScope.__init__(self, None, superscope)
        self.direct_subclasses = []
        self.node_factory = node_factory
        self.superclass = superclass
        if superclass:
            superclass.direct_subclasses.append(self)
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
        self.type_vars = OrderedDict()
        self.definition_deps = set()
        self.is_adt = name == 'ADT' # This flag is set when the class is
        # defining an algebraic data type or one of its constructors.
        # This flag is set transitively across subclasses.

    @property
    def is_defining_adt(self) -> bool:
        """
        Returns true if the class is defining an algebraic data type. This class
        defines the name of the ADT and should be directly inherited by the
        classes defining the ADT's constructors.
        """
        assert self.is_adt
        if self.superclass:
            return self.superclass.name == 'ADT'
        return False

    @property
    def adt_def(self) -> 'PythonClass':
        """
        Returns the class that defines the ADT.
        """
        assert self.is_adt
        if self.is_defining_adt:
            return self
        else:
            return self.superclass.adt_def

    @property
    def adt_domain_name(self) -> str:
        """
        Returns the domain name where the ADT is defined.
        """
        assert self.is_adt
        return self.fresh(self.adt_def.name)

    @property
    def adt_prefix(self) -> str:
        """
        Returns the prefix of the domain name where the ADT is defined.
        Prefixes are used in defining domain functions and axioms.
        """
        assert self.is_adt
        return self.adt_def.name + '_'

    @property
    def all_subclasses(self) -> List['PythonClass']:
        """
        Returns all direct or indirect subclasses of this class.
        """
        res = [self]
        for sub in self.direct_subclasses:
            res.extend(sub.all_subclasses)
        return res

    @property
    def call_deps(self):
        """
        Returns the dependencies which need to be defined when calling this class, i.e.,
        its constructor.
        """
        constructor = self.get_method('__init__')
        if constructor:
            return constructor.call_deps
        return set()

    @property
    def all_methods(self) -> Set[str]:
        result = set()
        if self.superclass:
            result |= self.superclass.all_methods
        result |= set(self.methods.keys())
        return result

    @property
    def all_static_fields(self) -> Set[str]:
        result = set()
        if self.superclass:
            result |= self.superclass.all_static_fields
        result |= set(self.static_fields)
        return result

    def fresh(self, name: str) -> str:
        assert self.is_adt
        if not hasattr(self.adt_def, '_fresh'):
            self.adt_def._fresh = SingletonFreshName(self.module)
        return self.adt_def._fresh(name)

    def types_match(self, type_a: 'PythonType', type_b: 'PythonType') -> bool:
        """
        Checks if types are either the same or, if one of them is an union, checks
        if the other type belongs to the set of types in the union. Finally, if
        both types are unions, this function returns true if they have elements
        in common.
        """
        if not isinstance(type_a, UnionType) and isinstance(type_b, UnionType):
            return type_a in type_b.get_types()
        elif not isinstance(type_b, UnionType) and isinstance(type_a, UnionType):
            return type_b in type_a.get_types()
        elif isinstance(type_a, UnionType) and isinstance(type_b, UnionType):
            return len(type_a.get_types() & type_b.get_types()) > 0
        else:
            return type_a == type_b

    def add_field(self, name: str, node: ast.AST,
                  type: 'PythonType') -> 'PythonField':
        """
        Adds a field with the given name and type if it doesn't exist yet in
        this class.
        """
        if name in self.fields:
            field = self.fields[name]
            assert self.types_match(field.type.try_box(), type.try_box())
        elif name in self.static_fields:
            field = self.static_fields[name]
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

    def has_function(self, name: str) -> bool:
        """
        Check the function with the given name exists this class or
        superclass.
        """
        return name in self.functions or (self.superclass.has_function(name)
               if self.superclass is not None else False)

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

    @property
    def all_fields(self) -> List['PythonField']:
        fields = []
        cls = self
        while cls is not None:
            for field in cls.python_class.fields.values():
                if isinstance(field, PythonField) and field.inherited is None:
                    fields.append(field)
            cls = cls.superclass
        return fields

    @property
    def all_sil_fields(self) -> List['silver.ast.Field']:
        """
        Returns a list of fields defined in the given class or its superclasses.
        """
        fields = []
        cls = self
        while cls is not None:
            for field in cls.python_class.fields.values():
                if isinstance(field, PythonField) and field.inherited is None:
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
            if isinstance(field, PythonMethod):
                # This is a property.
                getter_name = self.name + '_' + name + '_getter'
                setter_name = self.name + '_' + name + '_setter'
                field.process(self.get_fresh_name(getter_name), translator)
                if field.setter:
                    field.setter.process(self.get_fresh_name(setter_name), translator)
            else:
                field_name = self.name + '_' + name
                field.process(self.get_fresh_name(field_name))
        for name, field in self.static_fields.items():
            field_name = self.name + '_' + name
            field.process(self.get_fresh_name(field_name), translator)
        if self.interface:
            all_methods = list(self.functions.values())
            all_methods.extend(self.methods.values())
            for method in all_methods:
                requires = set()
                for requirement in method.requires:
                    target = self.get_func_or_method(requirement)
                    if target:
                        requires.add(target.sil_name)
                    else:
                        requires.add(requirement)
                translator.set_required_names(method.sil_name, requires)

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
            return self.superclass.python_class.get_common_superclass(other)
        elif other.superclass:
            return self.get_common_superclass(other.superclass.python_class)
        else:
            assert False, 'Internal error: Classes without common superclass.'

    def get_contents(self, only_top: bool) -> Dict:
        """
        Returns the elements that can be accessed from this container (to be
        used by get_target). If 'only_top' is true, returns only top level
        elements that can be accessed without a receiver.
        """
        dicts = [self.static_methods, self.static_fields]
        if not only_top:
            dicts.extend([self.functions, self.fields, self.methods,
                          self.predicates])
        return CombinedDict([], dicts)

    def try_box(self) -> 'PythonClass':
        """
        If this class represents a primitive type, returns the boxed version,
        otherwise just return the type itself.
        """
        if self.name in PRIMITIVES and self.name not in (PRIMITIVE_SEQ_TYPE + '_type',
                                                         PRIMITIVE_SET_TYPE + '_type',
                                                         CALLABLE_TYPE):
            boxed_name = self.name[len(PRIMITIVE_PREFIX):]
            if boxed_name == 'Set':
                boxed_name = PSET_TYPE
            if boxed_name == 'Multiset':
                boxed_name = PMSET_TYPE
            if boxed_name == 'Seq':
                boxed_name = PSEQ_TYPE
            return self.module.classes[boxed_name]
        return self

    def try_unbox(self) -> 'PythonClass':
        """
        If this class represents a boxed version of a primitive type, returns
        the primitive version, otherwise just returns the type itself.
        """
        if self.name in BOXED_PRIMITIVES:
            unboxed_name = PRIMITIVE_PREFIX + self.name
            return self.module.classes[unboxed_name]
        return self

    @property
    def python_class(self) -> 'PythonClass':
        return self


class GenericType(PythonType):
    """
    Represents a specific instantiation of a generic type, e.g. list[int].
    Provides access to the type arguments (in this case int) and otherwise
    behaves like the underlying PythonClass (in this case list).
    """

    def __init__(self, cls: PythonClass,
                 args: List[PythonType]) -> None:
        self.name = cls.name
        self.module = cls.module
        self.cls = cls
        self.type_args = args
        self.exact_length = True

    @property
    def python_class(self) -> PythonClass:
        return self.cls

    @property
    def sil_name(self) -> str:
        return self.python_class.sil_name

    def add_field(self, name: str, node: ast.AST,
                  type: 'PythonType') -> 'PythonField':
        return self.cls.add_field(name, node, type)

    @property
    def superclass(self) -> PythonClass:
        result = self.python_class.superclass
        if isinstance(result, GenericType):
            # Return a GenericType that has all type variables instantiated
            # based on the type arguments of this type.
            args = []
            for arg in result.type_args:
                if isinstance(arg, TypeVar):
                    args.append(self.type_args[arg.index])
                else:
                    args.append(arg)
            result = GenericType(result.cls, args)
        return result

    def get_field(self, name: str) -> Optional['PythonField']:
        """
        Returns the field with the given name in this class or a superclass.
        """
        return self.python_class.get_field(name)

    def get_method(self, name: str) -> Optional['PythonMethod']:
        """
        Returns the method with the given name in this class or a superclass.
        """
        return self.python_class.get_method(name)

    def has_function(self, name: str) -> bool:
        """
        Check if all types of the generic type have a function with the given
        name.
        """
        if isinstance(self, UnionType):
            types_set = self.get_types() - {None}
            result = len(types_set) > 0
            for type in types_set:
                result = result and type.has_function(name)
            return result
        else:
            return self.cls.has_function(name)

    def get_function(self, name: str) -> Optional['PythonMethod']:
        """
        Returns the function with the given name in this class or a superclass.
        """
        return self.python_class.get_function(name)

    def get_func_or_method(self, name: str) -> Optional['PythonMethod']:
        """
        Returns the function or method with the given name in this class or a
        superclass.
        """
        return self.python_class.get_func_or_method(name)

    @property
    def all_methods(self) -> Set[str]:
        return self.python_class.all_methods

    @property
    def all_static_fields(self) -> Set[str]:
        return self.python_class.all_static_fields

    def get_predicate(self, name: str) -> Optional['PythonMethod']:
        """
        Returns the predicate with the given name in this class or a superclass.
        """
        return self.python_class.get_predicate(name)

    def issubtype(self, other: PythonType) -> bool:
        if isinstance(other, GenericType):
            if self.python_class.issubtype(other.cls):
                if self.type_args == other.type_args:
                    return True
            return False
        return self.python_class.issubtype(other)

    def get_contents(self, only_top: bool) -> Dict:
        return self.python_class.get_contents(only_top)

    def __hash__(self) -> int:
        return hash(self.python_class)

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
        self._cls = None
        self.module = args[0].module
        self.type_args = args
        self.exact_length = True

    @property
    def cls(self):
        if self._cls is None:
            # Get common supertype of all types in the union.
            args = self.type_args
            cls = args[0]
            if isinstance(cls, GenericType):
                cls = cls.cls
            for type_option in args[1:]:
                if type_option:
                    if isinstance(type_option, GenericType):
                        type_option = type_option.cls
                    cls = cls.get_common_superclass(type_option)
            self._cls = cls
        return self._cls

    @property
    def python_class(self) -> PythonClass:
        return self.cls.python_class

    def get_types(self) -> Set[PythonClass]:
        """
        Returns a flattened set of types contained in Union
        """
        result = set()
        for type in self.type_args:
            if not isinstance(type, UnionType):
                if type is None:
                    result.add(None)
                else:
                    result.add(type.python_class)
            else:
                result |= type.get_types()
        return result


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

    @property
    def cls(self):
        return self.optional_type

    def get_types(self) -> Set[PythonClass]:
        """
        Returns a flattened set of types contained in Optional
        """
        if isinstance(self.optional_type, UnionType):
            return {None} | self.optional_type.get_types()
        else:
            return {None} | {self.optional_type}


class MethodType(Enum):
    normal = 0
    static_method = 1
    class_method = 2


def add_all_call_deps(call_deps: Set[Tuple[ast.AST, PythonNode, PythonModule]],
                      res: Set[Tuple[ast.AST, PythonNode, PythonModule]],
                      prefix: Tuple[PythonNode, ...]=()) -> None:
    """
    Adds all dependencies represented by call_deps to the given set.
    The set will contain tuples of length at least 3, where the first element is
    the Python AST node representing the access, the second the PythonNode accessed,
    the third the PythonModule in which the first name needs to be defined.
    All further elements are PythonNodes which represent conditions, i.e., the name
    needs to be defined in the module IF all the conditional PythonNodes have been
    defined in their respective modules.
    """
    for dep in call_deps:
        if dep not in res:
            c_prefix = prefix
            if len(dep) > 3:
                # this is a conditional dependency; its dependencies are to be in-
                # cluded under this condition.
                c_prefix = prefix + dep[3:]
            else:
                # this is a direct dependency, add it to the result
                res.add(dep + c_prefix)

            if hasattr(dep[1], 'add_all_call_deps'):
                dep[1].add_all_call_deps(res, c_prefix)


class PythonMethod(PythonNode, PythonScope, ContainerInterface, PythonStatementContainer):
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
        PythonScope.__init__(self, None, superscope)
        PythonStatementContainer.__init__(self)
        if cls is not None:
            if not isinstance(cls, PythonClass):
                raise Exception(cls)
        self.cls = cls
        self.overrides = None  # infer
        self._locals = OrderedDict()  # direct
        self.globals = set()
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
        self.pure = pure
        self.predicate = False
        self.all_low = False
        self.preserves_low = False
        self.contract_only = contract_only
        self.interface = interface
        self.interface_name = None  # Name to be used in error messages, if different from
                                    # the "actual" internal name. To be used for interface
                                    # methods.
        self.interface_dict = interface_dict
        self.node_factory = node_factory
        self.method_type = method_type
        self.obligation_info = None
        self.requires = []
        self.type_vars = OrderedDict()
        self.setter = None
        self.func_constant = None
        self.threading_id = None
        self.definition_deps = set()
        self.call_deps = set()

    def add_all_call_deps(self, res: Set[Tuple[ast.AST, PythonNode, PythonModule]],
                          prefix: Tuple[PythonNode, ...]=()) -> None:
        """
        Adds all dependencies needed when this method is called to the given set.
        """
        add_all_call_deps(self.call_deps, res, prefix)

    def process(self, sil_name: str, translator: 'Translator') -> None:
        """
        Creates fresh Silver names for all parameters and initializes them,
        same for local variables. Also sets the method type and
        checks if this method overrides one from a superclass,
        """
        self.sil_name = sil_name
        self.threading_id = self.superscope.get_fresh_name(self.name + "_threading")
        if self.pure:
            self.func_constant = self.superscope.get_fresh_name(self.name)
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
            requires = set()
            for requirement in self.requires:
                requires.add(requirement)
            translator.set_required_names(self.sil_name, requires)
            return
        func_type = self.module.types.get_func_type(self.scope_prefix)
        if self.type is not None:
            self.result = self.node_factory.create_python_var(RESULT_NAME, None,
                                                              self.type)
            self.result.process(RESULT_NAME, translator)
        if self.cls is not None and self.cls.superclass is not None:
            try:
                # Could be overridden by anything, so we have to check if there's
                # anything with the same name.
                self.overrides = self.cls.superclass.get_contents(False)[self.name]
            except KeyError:
                pass
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
            return self.module.global_vars.get(name)

    def create_variable(self, name: str, cls: PythonClass, translator: 'Translator',
                        local: bool = True, show_in_ce: bool = False) -> 'PythonVar':
        """
        Creates a new local variable with the given name and type and performs
        all necessary processing/initialization
        """
        sil_name = self.get_fresh_name(name)
        result = self.node_factory.create_python_var(name, None, cls)
        result.process(sil_name, translator)
        result.show_in_ce = show_in_ce
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
        PythonScope.__init__(self, None, superscope)
        self._preset = []
        self._postset = []
        self._inputs = []
        self._outputs = []
        self._io_universals = []
        self._terminates = None
        self._termination_measure = None
        self._body = None
        self._io_existentials = None
        self.func_args = []
        self.definition_deps = set()
        self.call_deps = set()
        self.node_factory = node_factory

    def add_all_call_deps(self, res: Set[Tuple[ast.AST, PythonNode, PythonModule]],
                          prefix: Tuple[PythonNode, ...]=()) -> None:
        add_all_call_deps(self.call_deps, res, prefix)

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
            body_checker = IOOperationBodyChecker(
                self._body,
                self.get_results(),
                self._io_existentials,
                module,
                translator)
            body_checker.check()
        self.sil_name = sil_name
        self._process_var_list(self._preset, translator)
        self._process_var_list(self._postset, translator)
        self._process_var_list(self._inputs, translator)
        self._process_var_list(self._outputs, translator)
        self._process_var_list(self._io_universals, translator)

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
        for var in self._io_universals:
            if var.name == name:
                return var
        if self._io_existentials:
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
        return IOOperationContentDict(self)


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
                 method: PythonStatementContainer,
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
        global_module = self.method.module.global_module
        int_type = global_module.classes[PRIMITIVE_INT_TYPE]
        result = self.node_factory.create_python_var(sil_name, None,
                                                     int_type)
        result.process(sil_name, translator)
        if isinstance(self.method, PythonMethod):
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
        exc_type = self.method.module.global_module.classes['Exception']
        result = self.node_factory.create_python_var(sil_name, None,
                                                     exc_type)
        result.process(sil_name, translator)
        result.show_in_ce = False
        if isinstance(self.method, PythonMethod):
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
        self.show_in_ce = True

    def process(self, sil_name: str, translator: 'Translator') -> None:
        """
        Sets ``sil_name``.
        """
        self.sil_name = sil_name

    def get_specific_type(self, node: ast.AST) -> PythonType:
        """
        Returns the type of this variable when referenced by the given node,
        i.e., checks if there is an alt_type for this node, otherwise returns
        the default type.
        """
        col = get_column(node)
        key = (node.lineno, col)
        if key in self.alt_types:
            return self.alt_types[key]
        else:
            return self.type


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
        module = self.type.module
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
        module = self.type.module
        return self._translator.translate_pythonvar_ref(self, module, node, ctx)


class PythonGlobalVar(PythonVarBase):
    """
    Represents a global variable in Python.
    """

    def __init__(self, name: str, node: ast.AST, type: PythonClass, module: PythonModule,
                 cls: PythonClass = None):
        super().__init__(name, node, type)
        self.module = module
        self.cls = cls
        self.overrides = None

    @property
    def is_final(self) -> bool:
        """
        A variable is final if it is written to only once (globally). Built-in module
        variables like __name__ are not considered final.
        """
        return len(self.writes) <= 1 and self.name not in MODULE_VARS

    def process(self, sil_name: str, translator: 'Translator') -> None:
        super().process(sil_name, translator)
        if self.cls is not None and self.cls.superclass is not None:
            try:
                self.overrides = self.cls.superclass.get_contents(False)[self.name]
                if not isinstance(self.overrides, PythonGlobalVar):
                    raise InvalidProgramException(self.node, 'invalid.override')
            except KeyError:
                pass


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

    @property
    def actual_field(self) -> 'PythonField':
        """
        If this field is inherited from a superclass, it will not actually be used in the
        translation; this function will return the field that is actually used.
        """
        result = self
        while result.inherited is not None:
            result = result.inherited
        return result


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
            self, name: str, node: ast.AST, type_: PythonClass,
            module: PythonModule) -> PythonGlobalVar:
        return PythonGlobalVar(name, node, type_, module)

    def create_static_field(
            self, name: str, node: ast.AST, type_: PythonClass, module: PythonModule,
            cls: PythonClass) -> PythonGlobalVar:
        return PythonGlobalVar(name, node, type_, module, cls)

    def create_python_io_existential_var(
            self, name: str, node: ast.AST,
            type_: PythonClass) -> PythonIOExistentialVar:
        return PythonIOExistentialVar(name, node, type_)

    def create_python_var_creator(
            self, name: str, node: ast.AST,
            type_: PythonClass) -> PythonIOExistentialVar:
        return PythonVarCreator(name, node, type_)

    def create_python_method(
            self, name: str, node: ast.AST, cls: PythonClass,
            superscope: PythonScope,
            pure: bool, contract_only: bool,
            container_factory: 'ProgramNodeFactory',
            interface: bool = False,
            interface_dict: Dict[str, Any] = None,
            method_type: MethodType = MethodType.normal) -> PythonMethod:
        return PythonMethod(name, node, cls, superscope, pure, contract_only,
                            container_factory, interface, interface_dict,
                            method_type)

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

def toposort_classes(class_set: Set[PythonClass]) -> List[PythonClass]:
    """
    Topological sorting of classes in a set, ensuring that derived classes
    precede their base classes in the returned list
    """
    map = {}

    for type in class_set:
        map[type] = set(type.all_subclasses) & class_set

    return list(toposort_flatten(map, False))

def chain_if_stmts(guarded_blocks: List[Tuple[Expr, Stmt]],
                   viper, position, info, ctx) -> Stmt:
    """
    Receives a list of tuples each one containing a guard and a guarded
    block and produces an equivalent chain of if statements.
    """
    assert(guarded_blocks)
    guard, then_block = guarded_blocks[0]
    if len(guarded_blocks) == 1:
        else_block = viper.Seqn([], position, info) # Empty block
    else:
        else_block = chain_if_stmts(guarded_blocks[1:], viper, position, info, ctx)
    return viper.If(guard, then_block, else_block, position, info)

def chain_cond_exp(guarded_expr: List[Tuple[Expr, Expr]],
                   viper, position, info, ctx) -> Expr:
    """
    Receives a list of tuples each one containing a guard and a guarded
    expression and produces an equivalent chain of conditional expressions.
    """
    if len(guarded_expr) == 1:
        return guarded_expr[0][1]
    guard, then_exp = guarded_expr[0]
    if len(guarded_expr) == 2:
        _, else_exp = guarded_expr[1]
    else:
        else_exp = chain_cond_exp(guarded_expr[1:], viper, position, info, ctx)
    return viper.CondExp(guard, then_exp, else_exp, position, info)