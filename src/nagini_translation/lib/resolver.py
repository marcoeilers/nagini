"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import ast

from nagini_contracts.contracts import CONTRACT_FUNCS
from nagini_translation.lib.constants import (
    BOOL_TYPE,
    BUILTINS,
    BYTES_TYPE,
    DICT_TYPE,
    INT_TYPE,
    LIST_TYPE,
    OBJECT_TYPE,
    OPERATOR_FUNCTIONS,
    PMSET_TYPE,
    PSEQ_TYPE,
    PSET_TYPE,
    RANGE_TYPE,
    SET_TYPE,
    STRING_TYPE,
    TUPLE_TYPE,
)
from nagini_translation.lib.program_nodes import (
    ContainerInterface,
    GenericType,
    OptionalType,
    PythonClass,
    PythonField,
    PythonIOOperation,
    PythonMethod,
    PythonModule,
    PythonNode,
    PythonType,
    PythonVarBase,
    TypeVar,
    UnionType,
)
from nagini_translation.lib.util import (
    get_func_name,
    InvalidProgramException,
    UnsupportedException,
)
from typing import List, Optional


def get_target(node: ast.AST,
               containers: List[ContainerInterface],
               container: PythonNode, type: bool = False) -> Optional[PythonNode]:
    """
    Finds the PythonNode that the given ``node`` refers to, e.g. a PythonClass
    or a PythonVar, if the immediate container (e.g. a PythonMethod) of the node
    is ``container``, by looking in the given ``containers`` (can be e.g.
    PythonMethods, the Context, PythonModules, etc).
    If the ``type`` parameter is set, will also consider string literals as potential
    references.
    """
    if isinstance(node, ast.Name):
        return find_entry(node.id, True, containers)
    elif type and isinstance(node, ast.Str):
        return find_entry(node.s, True, containers)
    elif isinstance(node, ast.Call):
        # For calls, we return the type of the result of the call
        if isinstance(node.func, ast.Call):
            if get_func_name(node.func) == 'IOExists':
                module = next(cont for cont in containers
                              if isinstance(cont, PythonModule))
                return module.global_module.classes[BOOL_TYPE]
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
            return None
        return get_target(node.func, containers, container)
    elif isinstance(node, ast.Attribute):
        # Find the type of the LHS, so that we can look through its members.
        lhs = get_type(node.value, containers, container)
        if isinstance(lhs, OptionalType):
            lhs = lhs.optional_type
        if isinstance(lhs, UnionType):
            # When receiver's type is union, a method call have multiple
            # targets, therefore None is returned in such cases
            return None
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
        return find_entry(node.attr, False, containers)
    elif isinstance(node, ast.Subscript):
        # This might be a type literal like List[int]
        if isinstance(node.value, ast.Name):
            module = next(cont for cont in containers
                          if isinstance(cont, PythonModule))
            type_class = None
            if node.value.id == 'Dict':
                type_class = module.global_module.classes[DICT_TYPE]
            if node.value.id == 'Set':
                type_class = module.global_module.classes[SET_TYPE]
            if node.value.id == 'List':
                type_class = module.global_module.classes[LIST_TYPE]
            if node.value.id == 'Tuple':
                type_class = module.global_module.classes[TUPLE_TYPE]
            if not type_class:
                possible_class = get_target(node.value, containers, container)
                if isinstance(possible_class, PythonType):
                    type_class = possible_class
            if type_class:
                # Look up the type arguments. Also consider string arguments.
                if isinstance(node.slice.value, ast.Tuple):
                    args = [get_target(arg, containers, container, True)
                            for arg in node.slice.value.elts]
                else:
                    args = [get_target(node.slice.value, containers, container, True)]
                return GenericType(type_class, args)
            if node.value.id == 'Optional':
                option = get_target(node.slice.value, containers, container, True)
                return OptionalType(option)
            if node.value.id == 'Union':
                if isinstance(node.slice.value, ast.Tuple):
                    elts = [get_target(e, containers, container, True)
                            for e in node.slice.value.elts]
                    return UnionType(elts)
                else:
                    return get_target(node.slice.value, containers, container, True)

    else:
        return None


def find_entry(target_name: str, only_top: bool,
               containers: List[ContainerInterface]) -> Optional[PythonNode]:
    """
    Returns the PythonNode identified by the given name in the given containers.
    """
    for lhs in containers:
        if lhs:
            options = lhs.get_contents(only_top=only_top)
            if target_name in options:
                return options[target_name]
    return None


def get_type(node: ast.AST, containers: List[ContainerInterface],
             container: PythonNode) -> Optional[PythonType]:
    """
    If ``node`` is an expression, returns its type, assuming that the immediate
    container (e.g. a PythonMethod) of the node is ``container``, by looking in
    the given ``containers`` (can be e.g. PythonMethods, the Context,
    PythonModules, etc). For primitive values, returns the boxed version.
    Returns None if the type is void.
    """
    result = _do_get_type(node, containers, container)
    if isinstance(result, PythonType):
        result = result.try_box()
    return result


def _do_get_type(node: ast.AST, containers: List[ContainerInterface],
                 container: PythonNode) -> Optional[PythonType]:
    """
    Does the actual work for get_type without boxing the type.
    """
    if isinstance(container, (PythonIOOperation, PythonMethod)):
        module = container.module
        current_function = container
    else:
        module = container
        current_function = None
    target = get_target(node, containers, container)
    if target:
        if isinstance(target, PythonVarBase):
            return target.get_specific_type(node)
        if isinstance(target, PythonMethod):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                rec_target = get_target(node.func.value, containers, container)
                if not isinstance(rec_target, PythonModule):
                    rectype = get_type(node.func.value, containers, container)
                    if target.generic_type != -1:
                        return rectype.type_args[target.generic_type]
                    if isinstance(target.type, TypeVar):
                        while rectype.python_class is not target.cls:
                            rectype = rectype.superclass
                        name_list = list(rectype.python_class.type_vars.keys())
                        index = name_list.index(target.type.name)
                        return rectype.type_args[index]
            return target.type
        if isinstance(target, PythonField):
            result = target.type
            if isinstance(result, TypeVar):
                assert isinstance(node, ast.Attribute)
                rec_type = _do_get_type(node.value, containers, container)
                while (rec_type.python_class is not
                        result.target_type.python_class):
                    rec_type = rec_type.superclass
                result = rec_type.type_args[result.index]
            return result
        if isinstance(target, PythonIOOperation):
            return module.global_module.classes[BOOL_TYPE]

        if isinstance(target, (PythonType, PythonModule)):
            if (isinstance(node, ast.Call) and
                    isinstance(target, PythonClass) and
                    target.type_vars):
                # This is a call to a constructor of a generic class; it's not
                # enough to just return the class, we need the entire type with
                # type arguments. We only support that if we can get it directly
                # from mypy, i.e., when the result is assigned to a variable
                # and we can get the variable type.
                if hasattr(node, '_parent') and node._parent and isinstance(node._parent, ast.Assign):
                    return get_type(node._parent.targets[0], containers,
                                    container)
                elif (target.name in (PSEQ_TYPE, PSET_TYPE, PMSET_TYPE) and
                          isinstance(node, ast.Call) and node.args):
                    arg_types = [get_type(arg, containers, container)
                                 for arg in node.args]
                    return GenericType(target, [common_supertype(arg_types)])
                else:
                    error = 'generic.constructor.without.type'
                    raise InvalidProgramException(node, error)
            return target
    if isinstance(node, (ast.Attribute, ast.Name)):
        if isinstance(node, ast.Attribute):
            lhs = _do_get_type(node.value, containers, container)
            if isinstance(lhs, UnionType) and not isinstance(lhs, OptionalType):
                candidates = [find_entry(node.attr, False, [t]) for t in lhs.type_args]
                if all(isinstance(c, (PythonField, PythonVarBase)) for c in candidates):
                    return common_supertype([c.type for c in candidates])
        # All these cases should be handled by get_target, so if we get here,
        # the node refers to something unknown in the given context.
        return None
    if isinstance(node, ast.Num):
        return module.global_module.classes[INT_TYPE]
    elif isinstance(node, ast.Tuple):
        args = [get_type(arg, containers, container) for arg in node.elts]
        return GenericType(module.global_module.classes[TUPLE_TYPE],
                           args)
    elif isinstance(node, ast.Subscript):
        return get_subscript_type(node, module, containers, container)
    elif isinstance(node, ast.Str):
        return module.global_module.classes[STRING_TYPE]
    elif isinstance(node, ast.Bytes):
        return module.global_module.classes[BYTES_TYPE]
    elif isinstance(node, ast.Compare):
        return module.global_module.classes[BOOL_TYPE]
    elif isinstance(node, ast.BoolOp):
        # And and Or always return one of their operands, so we use the common
        # supertype of all arguments.
        # TODO: We could also use a union type, but since support for e.g.
        # calling methods on those isn't amazing yet, we don't do that yet.
        operand_types = [get_type(operand, containers, container)
                         for operand in node.values]
        return common_supertype(operand_types)
    elif isinstance(node, ast.List):
        return _get_collection_literal_type(node, ['elts'], LIST_TYPE, module,
                                            containers, container)
    elif isinstance(node, ast.Set):
        return _get_collection_literal_type(node, ['elts'], SET_TYPE, module,
                                            containers, container)
    elif isinstance(node, ast.Dict):
        return _get_collection_literal_type(node, ['keys', 'values'], DICT_TYPE,
                                            module, containers, container)
    elif isinstance(node, ast.IfExp):
        body_type = get_type(node.body, containers, container)
        else_type = get_type(node.orelse, containers, container)
        return pairwise_supertype(body_type, else_type)
    elif isinstance(node, ast.BinOp):
        left_type = get_type(node.left, containers, container)
        right_type = get_type(node.right, containers, container)
        operator_func = OPERATOR_FUNCTIONS[type(node.op)]
        return left_type.get_func_or_method(operator_func).type
    elif isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.Not):
            return module.global_module.classes[BOOL_TYPE]
        elif isinstance(node.op, ast.USub):
            return module.global_module.classes[INT_TYPE]
        else:
            raise UnsupportedException(node)
    elif isinstance(node, ast.NameConstant):
        if (node.value is True) or (node.value is False):
            return module.global_module.classes[BOOL_TYPE]
        elif node.value is None:
            return module.global_module.classes['NoneType']
        else:
            raise UnsupportedException(node)
    elif isinstance(node, ast.Call):
        return _get_call_type(node, module, current_function, containers,
                              container)
    elif isinstance(node, ast.ListComp):
        if (node._parent and isinstance(node._parent, ast.Assign) and
                    node is node._parent.value):
            # Constructor is assigned to variable;
            # we get the type of the dict from the type of the
            # variable it's assigned to.
            return get_type(node._parent.targets[0], containers,
                            container)
        else:
            raise UnsupportedException(node, 'List comprehensions must be directly '
                                       'assigned to a local variable.')
    else:
        raise UnsupportedException(node)


def _get_collection_literal_type(node: ast.AST, arg_fields: List[str],
                                 coll_type: str, module: PythonModule,
                                 containers: List[ContainerInterface],
                                 container: PythonNode) -> PythonType:
    """
    Assuming ``node`` is a collection literal, ``coll_type`` is the type of the
    collection (e.g. 'list'), and ``arg_fields`` contains the fields of the
    literal which contain the contents of the literal (e.g. 'keys' and 'values'
    for a dict), returns the type of the collection.
    """
    if hasattr(node, '_parent') and isinstance(node._parent, ast.Assign):
        # Constructor is assigned to variable;
        # we get the type of the dict from the type of the
        # variable it's assigned to.
        args = get_type(node._parent.targets[0], containers,
                        container).type_args
    elif all(getattr(node, arg_field) for arg_field in arg_fields):
        args = []
        for arg_field in arg_fields:
            arg_types = [get_type(arg, containers, container) for arg in
                         getattr(node, arg_field)]
            args.append(common_supertype(arg_types))
    else:
        object_class = module.global_module.classes[OBJECT_TYPE]
        args = [object_class for arg_field in arg_fields]
    return GenericType(module.global_module.classes[coll_type],
                       args)


def _get_call_type(node: ast.Call, module: PythonModule,
                   current_function: PythonMethod,
                   containers: List[ContainerInterface],
                   container: PythonNode) -> PythonType:
    func_name = get_func_name(node)
    if func_name == 'super':
        if len(node.args) == 2:
            return module.classes[node.args[0].id].superclass
        elif not node.args:
            return container.cls.superclass
        else:
            raise InvalidProgramException(node, 'invalid.super.call')
    if func_name == 'len':
        return module.global_module.classes[INT_TYPE]
    if func_name in ('token', 'ctoken', 'MustTerminate', 'MustRelease'):
        return module.global_module.classes[BOOL_TYPE]
    if func_name == PSEQ_TYPE:
        return _get_collection_literal_type(node, ['args'], PSEQ_TYPE, module,
                                            containers, container)
    if func_name == PSET_TYPE:
        return _get_collection_literal_type(node, ['args'], PSET_TYPE, module,
                                            containers, container)
    if func_name == PMSET_TYPE:
        return _get_collection_literal_type(node, ['args'], PMSET_TYPE, module,
                                            containers, container)
    if func_name == 'enumerate':
        if len(node.args) != 1:
            raise UnsupportedException(node, 'enumerate only supported with single arg.')
        list_type = module.global_module.classes[LIST_TYPE]
        int_type = module.global_module.classes[INT_TYPE]
        tuple_type = module.global_module.classes[TUPLE_TYPE]
        arg_type = get_type(node.args[0], containers, container)
        iterable_type = _get_iteration_type(arg_type, module, node)
        return GenericType(list_type, [GenericType(tuple_type,
                                                   [int_type, iterable_type])])
    if isinstance(node.func, ast.Name):
        if node.func.id in CONTRACT_FUNCS:
            if node.func.id  == 'Result':
                return current_function.type
            elif node.func.id == 'RaisedException':
                ctxs = [cont for cont in containers if
                        hasattr(cont, 'var_aliases')]
                ctx = ctxs[0] if ctxs else None
                assert ctx
                assert ctx.current_contract_exception is not None
                return ctx.current_contract_exception
            elif node.func.id in ('Acc', 'Rd', 'Read', 'Implies', 'Forall', 'IOForall', 'Exists',
                                  'MayCreate', 'MaySet', 'Low', 'LowVal', 'LowEvent', 'LowExit'):
                return module.global_module.classes[BOOL_TYPE]
            elif node.func.id == 'Declassify':
                return None
            elif node.func.id == 'Old':
                return get_type(node.args[0], containers, container)
            elif node.func.id == 'Unfolding':
                return get_type(node.args[1], containers, container)
            elif node.func.id == 'ToSeq':
                arg_type = get_type(node.args[0], containers, container)
                seq_class = module.global_module.classes[PSEQ_TYPE]
                content_type = _get_iteration_type(arg_type, module, node)
                return GenericType(seq_class, [content_type])
            elif node.func.id == 'Previous':
                arg_type = get_type(node.args[0], containers, container)
                list_class = module.global_module.classes[PSEQ_TYPE]
                return GenericType(list_class, [arg_type])
            elif node.func.id in ('getArg', 'getOld', 'getMethod'):
                object_class = module.global_module.classes[OBJECT_TYPE]
                return object_class
            elif node.func.id == 'Let':
                body_type = get_target(node.args[1], containers, container)
                if isinstance(body_type, PythonType):
                    return body_type
                raise InvalidProgramException(node, 'invalid.let')
            else:
                raise UnsupportedException(node)
        elif node.func.id in BUILTINS:
            if node.func.id in ('isinstance', BOOL_TYPE):
                return module.global_module.classes[BOOL_TYPE]
            elif node.func.id == 'cast':
                return get_target(node.args[0],
                                  containers, container)
            else:
                raise UnsupportedException(node)
        if node.func.id in module.classes:
            return module.global_module.classes[node.func.id]
        elif module.get_func_or_method(node.func.id) is not None:
            target = module.get_func_or_method(node.func.id)
            return target.type
    elif isinstance(node.func, ast.Attribute):
        rectype = get_type(node.func.value, containers, container)
        if isinstance(rectype, UnionType):
            set_of_classes = rectype.get_types() - {None}
            set_of_return_types = {type.get_func_or_method(node.func.attr).type
                                   for type in set_of_classes}
            if len(set_of_return_types) == 1:
                return set_of_return_types.pop()
            elif len(set_of_return_types) == 2 and None in set_of_return_types:
                return OptionalType((set_of_return_types - {None}).pop())
            else:
                return UnionType(list(set_of_return_types))
        elif isinstance(rectype, PythonType):
            target = rectype.get_func_or_method(node.func.attr)
            if target.generic_type != -1:
                return rectype.type_args[target.generic_type]
            else:
                return target.type
    else:
        raise UnsupportedException(node)


def get_subscript_type(node: ast.Subscript, module: PythonModule,
                        containers: List[ContainerInterface],
                        container: PythonNode) -> PythonType:
    if (hasattr(node, '_parent') and node._parent and isinstance(node._parent, ast.Assign) and
            node is node._parent.value):
        # Constructor is assigned to variable;
        # we get the type of the dict from the type of the
        # variable it's assigned to.
        return get_type(node._parent.targets[0], containers,
                        container)
    value_type = get_type(node.value, containers, container)
    return _get_subscript_type(value_type, module, node)


def _get_subscript_type(value_type: PythonType, module: PythonModule,
                        node: ast.AST) -> PythonType:
    if isinstance(value_type, OptionalType):
        value_type = value_type.cls
    if value_type.name == TUPLE_TYPE:
        if isinstance(node, ast.Subscript):
            if isinstance(node.slice, ast.Slice):
                raise UnsupportedException(node, 'tuple slicing')
            if len(value_type.type_args) == 1:
                return value_type.type_args[0]
            if isinstance(node.slice.value, ast.UnaryOp):
                if (isinstance(node.slice.value.op, ast.USub) and
                        isinstance(node.slice.value.operand, ast.Num)):
                    index = -node.slice.value.operand.n
                else:
                    raise UnsupportedException(node, 'dynamic subscript type')
            elif isinstance(node.slice.value, ast.Num):
                index = node.slice.value.n
            return value_type.type_args[index]
        else:
            return common_supertype(value_type.type_args)
    elif value_type.name == LIST_TYPE:
        return value_type.type_args[0]
    elif value_type.name == SET_TYPE:
        return value_type.type_args[0]
    elif value_type.name in (DICT_TYPE, 'defaultdict', 'ExpiringDict'):
        # FIXME: This is very unfortunate, but right now we cannot handle this
        # generically, so we have to hard code these two cases for the moment.
        return value_type.type_args[1]
    elif value_type.name in (RANGE_TYPE, BYTES_TYPE):
        return module.global_module.classes[INT_TYPE]
    elif value_type.name == PSEQ_TYPE:
        return value_type.type_args[0]
    elif value_type.name == PSET_TYPE:
        return value_type.type_args[0]
    elif value_type.name == PMSET_TYPE:
        return value_type.type_args[0]
    elif value_type.python_class.get_func_or_method('__getitem__'):
        return value_type.python_class.get_func_or_method('__getitem__').type
    else:
        raise UnsupportedException(node)


def _get_iteration_type(value_type: PythonType, module: PythonModule,
                        node: ast.AST) -> PythonType:
    # Assuming that value_type is some sort of container which supports iteration,
    # returns the type of the iterator.
    if value_type.name in (DICT_TYPE, 'defaultdict', 'ExpiringDict'):
        # FIXME: This is very unfortunate, but right now we cannot handle this
        # generically, so we have to hard code these two cases for the moment.
        return value_type.type_args[0]
    else:
        return _get_subscript_type(value_type, module, node)


def common_supertype(types: List[PythonType]) -> Optional[PythonType]:
    """
    Returns the common supertype of all types in the list. The list may not
    be empty.
    """
    assert types
    if len(types) == 1:
        return types[0]
    current = types[0]
    for new in types[1:]:
        current = pairwise_supertype(current, new)
    return current


def pairwise_supertype(t1: PythonType, t2: PythonType) -> Optional[PythonType]:
    """
    Returns the common supertype of 't1' and 't2', if any.
    """
    if t1.issubtype(t2):
        return t2
    if t2.issubtype(t1):
        return t1
    if (not t1.superclass and not t2.superclass):
        return None
    if not t1.superclass:
        return pairwise_supertype(t2.superclass, t1)
    return pairwise_supertype(t2, t1.superclass)