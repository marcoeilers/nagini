import ast
from typing import Union, List, Dict, Set
from nagini_contracts.contracts import (
    CONTRACT_WRAPPER_FUNCS,
    CONTRACT_FUNCS
)
from nagini_translation.lib.program_nodes import (
    PythonModule,
    PythonMethod,
    PythonVar
)
from nagini_translation.lib.util import (
    UnsupportedException,
    InvalidProgramException,
)


class CallSlotAnalyzer:

    def __init__(self, analyzer: 'Analyzer') -> None:
        self.analyzer = analyzer
        self.call_slot = None  # type: CallSlot
        self.allowed_variables_checker = _AllowedVariablesChecker()

    def analyze(self, node: ast.FunctionDef) -> None:
        """
        Preprocess the call slot `node'.
        """

        # FIXME: refactor this method
        # preferably we can refactor it so that we can have a base class
        # for both the CallSlotAnalyzer and CallSlotProofAnalyzer
        # Basically, the CallSlotProofAnalyzer has to do almost the same as
        # the CallSlotAnalyzer, except that more statements are allowed
        # in its body
        assert is_call_slot(node)

        analyzer = self.analyzer
        scope = analyzer.module
        assert isinstance(scope, PythonModule)

        if analyzer.current_function is not None:
            raise InvalidProgramException(
                node,
                'call_slots.nested.declaration',
                "Callslot '%s' occurs inside a method" % node.name
            )
        if analyzer.current_class is not None:
            raise InvalidProgramException(
                node,
                'call_slots.nested.declaration',
                "Callslot '%s' occurs inside a class" % node.name
            )

        analyzer.define_new(scope, node.name, node)

        self.call_slot = analyzer.node_factory.create_call_slot(
            node.name,
            node,
            scope,
            analyzer.node_factory
        )

        scope.call_slots[node.name] = self.call_slot

        analyzer.current_function = self.call_slot
        _check_method_declaration(self.call_slot, analyzer)

        body_node = node

        has_uq_vars = _is_uq_vars(node.body)
        if has_uq_vars:
            body_node = node.body[0]
            mock_call_slot = analyzer.node_factory.create_call_slot(
                body_node.name,
                body_node,
                self.call_slot,
                analyzer.node_factory
            )

            analyzer.outer_functions.append(self.call_slot)
            analyzer.current_function = mock_call_slot

            _check_method_declaration(mock_call_slot, analyzer)
            self.call_slot.uq_variables = mock_call_slot.args

            body_node._parent = node

        # FIXME: disallow shadowing through return variables?
        _check_variables(
            self.call_slot.args,
            self.call_slot.uq_variables,
            ILLEGAL_VARIABLE_NAMES
        )

        for child in body_node.body:
            analyzer.visit(child, body_node)

        # TODO: pure call slots
        # TODO: other call slot preprocessing/checks
        # - body consists only of
        #   - Preconditions (done)
        #   - Postconditions (done)
        #   - One single call declaration
        #     - check 'well-formedness' of call
        # - gather return values (save in CallSlot?)

        self._check_body(body_node.body)

        valid_varible_uses = (
            self.call_slot.args.keys() |
            self.call_slot.uq_variables.keys() |
            ILLEGAL_VARIABLE_NAMES |
            set(map(lambda name: name.id, self.call_slot.return_variables))
        )
        self.allowed_variables_checker.reset(valid_varible_uses)
        illegal_variable_uses = self.allowed_variables_checker.check(node)
        if 0 < len(illegal_variable_uses):
            raise InvalidProgramException(
                illegal_variable_uses[0],
                'call_slot.names.non_local',
                "Illegal reference to non-local name '%s'" % illegal_variable_uses[0].id
            )

        # cleanup
        if has_uq_vars:
            self.call_slot.precondition = mock_call_slot.precondition
            self.call_slot.postcondition = mock_call_slot.postcondition
            analyzer.outer_functions.pop()
        analyzer.current_function = None

    def _check_body(self, body: List[ast.stmt]):
        self.has_call = False
        for child in body:

            if isinstance(child, ast.Expr) and isinstance(child.value, ast.Call):
                if is_precondition(child.value) or is_postcondition(child.value):
                    continue
                self._check_call_declaration(child.value)

            elif isinstance(child, ast.Assign):
                self._check_call_declaration(child)

            else:
                raise InvalidProgramException(
                    child,
                    'call_slots.body.invalid_stmt',
                    'Callslot declarations must only consist of contracts and a single call'
                )

        if not self.has_call:
            raise InvalidProgramException(
                self.call_slot.node,
                'call_slots.no.call',
                "Callslot '%s' doesn't declare a call" % self.call_slot.node.name
            )

    def _check_call_declaration(self, node: Union[ast.Call, ast.Assign]) -> None:

        if isinstance(node, ast.Assign):

            if not isinstance(node.value, ast.Call):
                raise InvalidProgramException(
                    node,
                    'call_slots.body.invalid_stmt',
                    'Callslot declarations must only consist of contracts and a single call'
                )
            call = node.value

            if len(node.targets) > 1:
                raise UnsupportedException(
                    node,
                    "Callslot's call can't have more than one return target"
                )

            assert len(node.targets) == 1

            if isinstance(node.targets[0], ast.Name):
                self.call_slot.return_variables = [node.targets[0]]
            elif isinstance(node.targets[0], ast.Tuple):

                # NOTE: could add support for nested destructuring
                # e.g., `a, (b, c), d = f(1, 2, 3)`
                # currently we only support simple tuple assignments
                for target in node.targets[0].elts:
                    if not isinstance(target, ast.Name):
                        raise UnsupportedException(
                            target,
                            "Callslots only support simple tuple assignments"
                        )

                self.call_slot.return_variables = node.targets[0].elts
            else:
                raise UnsupportedException(
                    node,
                    "Callslot's call has an unsupported return target"
                )
        else:
            call = node

        self._check_call(call)

    def _check_call(self, node: ast.Call) -> None:
        if self.has_call:
            raise InvalidProgramException(
                node,
                'call_slots.multiple.calls',
                "Callslot '%s' declares more than one call" % self.call_slot.node.name
            )
        self.has_call = True
        self.call_slot.call = node


# FIXME: check call slot application


class CallSlotProofAnalyzer:

    # NOTE: we can probably reuse a lot from CallSlotAnalyzer

    def __init__(self, analyzer: 'Analyzer') -> None:
        self.analyzer = analyzer

    def analyze(self, node: ast.FunctionDef) -> None:
        """
        Preprocess the call slot `node'.
        """
        pass  # FIXME: implement


ILLEGAL_VARIABLE_NAMES = set(CONTRACT_FUNCS + CONTRACT_WRAPPER_FUNCS)


def _check_variables(
    normal_variables: Dict[str, PythonVar],
    uq_variables: Dict[str, PythonVar],
    illegal_variable_names: Set[str]
) -> None:

    shadowed_variables = normal_variables.keys() & uq_variables.keys()

    if 0 < len(shadowed_variables):
        shadowed_variable_name = next(iter(shadowed_variables))
        raise InvalidProgramException(
            uq_variables[shadowed_variable_name].node,
            "call_slots.parameters.illegal_shadowing",
            "UQ variable '%s' illegally shadows an outer variable" % shadowed_variable_name
        )

    all_variable_names = normal_variables.keys() | uq_variables.keys()
    illegal_variable_names = all_variable_names & illegal_variable_names

    if 0 < len(illegal_variable_names):
        illegal_variable_name = next(iter(illegal_variable_names))

        illegal_variable = (
            normal_variables[illegal_variable_name] if
            illegal_variable_name in normal_variables else
            uq_variables[illegal_variable_name]
        )
        raise InvalidProgramException(
            illegal_variable.node,
            "call_slots.parameters.illegal_name",
            "Variable '%s' has an illegal name" % illegal_variable_name
        )


class _AllowedVariablesChecker(ast.NodeVisitor):

    # NOTE: CallSlotProofAnalyzer will require adjustments:
    # In callslot proofs there can be nested call slot proofs which introduce
    # new valid variables.

    def __init__(self, allowed_variables: Set[str] = set()) -> None:
        self.reset(allowed_variables)

    def reset(self, allowed_variables: Set[str]) -> None:
        self.offending_nodes = []  # type: List[ast.Name]
        self.allowed_variables = allowed_variables

    def check(self, node: ast.AST) -> List[ast.Name]:
        self.visit(node)
        return self.offending_nodes

    def visit_Name(self, name: ast.Name) -> None:
        if name.id not in self.allowed_variables:
            self.offending_nodes.append(name)

    def visit_arg(self, arg: ast.arg) -> None:
        return  # ignore annotations


def _check_method_declaration(method: PythonMethod, analyzer: 'Analyzer') -> None:
    """
    Checks whether `node' is a method declaration valid for a call slot or
    universally quantified variables. If not raises an appropriate
    exception. Expects analyzer.{current_function, outer_functions} to be
    set correctly.

    * No magic name ('__...__')
    * Return type = None
    * No *args
    * No **kwargs
    """

    # NOTE: needs tests

    if analyzer._is_illegal_magic_method_name(method.node.name):
        raise InvalidProgramException(method.node, 'illegal.magic.method')

    method.type = analyzer.convert_type(
        analyzer.module.get_func_type(method.scope_prefix))

    if method.type is not None:
        raise InvalidProgramException(
            method.node,
            'call_slots.return.not_none',
            "Method '%s' doesn't return 'None'" % method.node.name
        )

    if 0 < len(method.node.args.defaults):
        raise InvalidProgramException(
            method.node.args.defaults[0],
            'call_slots.parameters.default',
            "Method '%s' has a default parameter" % method.node.name
        )

    analyzer.visit(method.node.args, method.node)

    if method.var_arg is not None:
        raise InvalidProgramException(
            method.node,
            'call_slots.parameters.var_args',
            ("Method '%s' contains illegal variadic parameters"
                % method.node.name)
        )

    if method.kw_arg is not None:
        raise InvalidProgramException(
            method.node,
            'call_slots.parameters.kw_args',
            ("Method '%s' contains illegal keyword parameters"
                % method.node.name)
        )


def _is_uq_vars(body) -> bool:
    return (
        len(body) == 1 and
        isinstance(body[0], ast.FunctionDef) and
        is_universally_quantified(body[0])
    )


def is_call_slot(node: ast.FunctionDef) -> bool:
    """
    Whether node is a call slot declaration.
    """
    return _has_single_decorator(node, 'CallSlot')


def is_universally_quantified(node: ast.FunctionDef) -> bool:
    """
    Whether a function introduces universally quantified variables
    """
    return _has_single_decorator(node, 'UniversallyQuantified')


def is_call_slot_proof(node: ast.FunctionDef) -> bool:
    """
    Whether a function introduces universally quantified variables
    """
    return _has_single_decorator(node, 'CallSlotProof')


def _has_single_decorator(node: ast.FunctionDef, decorator_name: str) -> bool:
    """
    Whether `node' has only one decorator that equals to `decorator'
    """
    # NOTE: could be refactored out into a nagini 'util' package
    if len(node.decorator_list) != 1:
        return False
    decorator = node.decorator_list[0]

    if isinstance(decorator, ast.Name):
        return decorator.id == decorator_name

    if isinstance(decorator, ast.Call):
        return decorator.func.id == decorator_name

    # FIXME: should probably raise instead
    return False


def is_precondition(call: ast.Call) -> bool:
    return call.func.id == 'Requires'


def is_postcondition(call: ast.Call) -> bool:
    return call.func.id == 'Ensures'
