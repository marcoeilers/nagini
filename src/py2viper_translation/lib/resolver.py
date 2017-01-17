import ast

from py2viper_contracts.contracts import CONTRACT_FUNCS
from py2viper_translation.lib.constants import (
    BOOL_TYPE,
    BOXED_PRIMITIVES,
    BUILTINS,
    DICT_TYPE,
    END_LABEL,
    INT_TYPE,
    LIST_TYPE,
    OBJECT_TYPE,
    OPERATOR_FUNCTIONS,
    PRIMITIVE_INT_TYPE,
    PRIMITIVE_PREFIX,
    PRIMITIVES,
    RANGE_TYPE,
    RESULT_NAME,
    SET_TYPE,
    STRING_TYPE,
    TUPLE_TYPE,
    UNION_TYPE,
)
from py2viper_translation.lib.program_nodes import (
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
    UnionType,
)
from py2viper_translation.lib.util import (
    get_func_name,
    UnsupportedException,
)
from typing import List, Optional


def get_target(node: ast.AST,
               containers: List[ContainerInterface],
               container: PythonNode) -> Optional[PythonNode]:
    """
    Finds the PythonNode that the given ``node`` refers to, e.g. a PythonClass
    or a PythonVar, if the immediate container (e.g. a PythonMethod) of the node
    is ``container``, by looking in the given ``containers`` (can be e.g.
    PythonMethods, the Context, PythonModules, etc).
    """
    if isinstance(node, ast.Name):
        return _find_entry(node.id, True, containers)
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
        lhs = get_type(node.value, containers, container)
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
        return _find_entry(node.attr, False, containers)
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
            if type_class:
                args = []
                if isinstance(node.slice.value, ast.Tuple):
                    args = [get_target(arg, containers, container)
                            for arg in node.slice.value.elts]
                elif isinstance(node.slice.value, ast.Name):
                    args = [get_target(node.slice.value, containers, container)]
                else:
                    assert False
                return GenericType(type_class, args)
    else:
        return None


def _find_entry(target_name: str, only_top: bool,
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
        module = container.get_module()
        current_function = container
    else:
        module = container
        current_function = None
    target = get_target(node, containers, container)
    if target:
        if isinstance(target, PythonVarBase):
            return target.get_specific_type(node)
        if isinstance(target, PythonMethod):
            if isinstance(node.func, ast.Attribute):
                rec_target = get_target(node.func.value, containers, container)
                if not isinstance(rec_target, PythonModule):
                    rectype = get_type(node.func.value, containers, container)
                    if target.generic_type != -1:
                        return rectype.type_args[target.generic_type]
            return target.type
        if isinstance(target, PythonField):
            return target.type
        if target:
            return target
    if isinstance(node, (ast.Attribute, ast.Name)):
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
        return _get_subscript_type(node, module, containers, container)
    elif isinstance(node, ast.Str):
        return module.global_module.classes[STRING_TYPE]
    elif isinstance(node, ast.Compare):
        return module.global_module.classes[BOOL_TYPE]
    elif isinstance(node, ast.BoolOp):
        return module.global_module.classes[BOOL_TYPE]
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
            return module.global_module.classes[OBJECT_TYPE]
        else:
            raise UnsupportedException(node)
    elif isinstance(node, ast.Call):
        return _get_call_type(node, module, containers, container)
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
    if all(getattr(node, arg_field) for arg_field in arg_fields):
        args = []
        for arg_field in arg_fields:
            arg_types = [get_type(arg, containers, container) for arg in
                         getattr(node, arg_field)]
            args.append(common_supertype(arg_types))
    elif node._parent and isinstance(node._parent, ast.Assign):
        # Empty constructor is assigned to variable;
        # we get the type of the empty dict from the type of the
        # variable it's assigned to.
        args = get_type(node._parent.targets[0], containers,
                        container).type_args
    else:
        object_class = module.global_module.classes[OBJECT_TYPE]
        args = [object_class for arg_field in arg_fields]
    return GenericType(module.global_module.classes[coll_type],
                       args)


def _get_call_type(node: ast.Call, module: PythonModule,
                   containers: List[ContainerInterface],
                   container: PythonNode) -> PythonType:
    func_name = get_func_name(node)
    if func_name == 'super':
        if len(node.args) == 2:
            return module.classes[node.args[0].id].superclass
        elif not node.args:
            return current_class.superclass
        else:
            raise InvalidProgramException(node, 'invalid.super.call')
    if func_name == 'len':
        return module.global_module.classes[INT_TYPE]
    if isinstance(node.func, ast.Name):
        if node.func.id in CONTRACT_FUNCS:
            if node.func.id == 'Result':
                return current_function.type
            elif node.func.id == 'RaisedException':
                ctxs = [cont for cont in containers if
                        hasattr(cont, 'var_aliases')]
                ctx = ctxs[0] if ctxs else None
                assert ctx
                assert ctx.current_contract_exception is not None
                return ctx.current_contract_exception
            elif node.func.id in ('Acc', 'Implies', 'Forall', 'Exists'):
                return module.global_module.classes[BOOL_TYPE]
            elif node.func.id == 'Old':
                return get_type(node.args[0], containers, container)
            elif node.func.id == 'Unfolding':
                return get_type(node.args[1], containers, container)
            elif node.func.id == 'Previous':
                arg_type = get_type(node.args[0], containers, container)
                list_class = module.global_module.classes[LIST_TYPE]
                return GenericType(list_class, [arg_type])
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
        if isinstance(rectype, PythonType):
            target = rectype.get_func_or_method(node.func.attr)
            if target.generic_type != -1:
                return rectype.type_args[target.generic_type]
            else:
                return target.type


def _get_subscript_type(node: ast.Subscript, module: PythonModule,
                        containers: List[ContainerInterface],
                        container: PythonNode) -> PythonType:
    value_type = get_type(node.value, containers, container)
    if value_type.name == TUPLE_TYPE:
        if len(value_type.type_args) == 1:
            return value_type.type_args[0]
        return value_type.type_args[node.slice.value.n]
    elif value_type.name == LIST_TYPE:
        return value_type.type_args[0]
    elif value_type.name == SET_TYPE:
        return value_type.type_args[0]
    elif value_type.name == DICT_TYPE:
        return value_type.type_args[1]
    elif value_type.name == RANGE_TYPE:
        return module.global_module.classes[INT_TYPE]
    else:
        raise UnsupportedException(node)


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