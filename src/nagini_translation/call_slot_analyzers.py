import ast
from typing import Union, List, Set
from nagini_contracts.contracts import (
    CONTRACT_WRAPPER_FUNCS,
    CONTRACT_FUNCS
)
from nagini_translation.lib.program_nodes import (
    PythonModule
)
from nagini_translation.lib.util import (
    UnsupportedException,
    InvalidProgramException,
)


class _CallSlotBaseAnalyzer:

    # TODO: pure call slots

    __ILLEGAL_VARIABLE_NAMES = set(CONTRACT_FUNCS + CONTRACT_WRAPPER_FUNCS)

    def __init__(self, analyzer: 'Analyzer') -> None:
        self.analyzer = analyzer
        self.call_slot = None  # type: CallSlotBase

    def analyze(self, node: ast.FunctionDef) -> None:
        """
        Preprocess the call slot `node'.
        """

        old_current_function = self.analyzer.current_function
        if old_current_function is not None:
            self.analyzer.outer_functions.append(old_current_function)
        self._pre_process(node)

        self.analyzer.current_function = self.call_slot
        self._check_method_declaration(self.call_slot)

        body_node = node

        has_uq_vars = _is_uq_vars(node.body)
        if has_uq_vars:
            body_node = node.body[0]
            mock_call_slot = self.analyzer.node_factory.create_call_slot(
                body_node.name,
                body_node,
                self.call_slot,
                self.analyzer.node_factory
            )

            self.analyzer.outer_functions.append(self.call_slot)
            self.analyzer.current_function = mock_call_slot

            self._check_method_declaration(mock_call_slot)
            self.call_slot.uq_variables = mock_call_slot.args

            body_node._parent = node

        self.call_slot.body = body_node.body
        for child in body_node.body:
            self.analyzer.visit(child, body_node)

        self._check_body(body_node.body)

        self._check_variables()

        # cleanup
        if has_uq_vars:
            self.call_slot._locals = mock_call_slot._locals
            self.call_slot.precondition = mock_call_slot.precondition
            self.call_slot.postcondition = mock_call_slot.postcondition
            self.analyzer.outer_functions.pop()

        self.call_slot.type = self.call_slot.locals[self.call_slot.return_variables[0].id].type
        self.analyzer.current_function = old_current_function
        if old_current_function is not None:
            self.analyzer.outer_functions.pop()

    def _check_method_declaration(self, call_slot: 'CallSlotBase') -> None:
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

        analyzer = self.analyzer

        if analyzer._is_illegal_magic_method_name(call_slot.node.name):
            raise InvalidProgramException(call_slot.node, 'illegal.magic.method')

        _type = analyzer.convert_type(
            analyzer.module.get_func_type(call_slot.scope_prefix))

        if _type is not None:
            raise InvalidProgramException(
                call_slot.node,
                'call_slots.return.not_none',
                "Method '%s' doesn't return 'None'" % call_slot.node.name
            )

        if 0 < len(call_slot.node.args.defaults):
            raise InvalidProgramException(
                call_slot.node.args.defaults[0],
                'call_slots.parameters.default',
                "Method '%s' has a default parameter" % call_slot.node.name
            )

        analyzer.visit(call_slot.node.args, call_slot.node)

        if call_slot.var_arg is not None:
            raise InvalidProgramException(
                call_slot.node,
                'call_slots.parameters.var_args',
                ("Method '%s' contains illegal variadic parameters"
                    % call_slot.node.name)
            )

        if call_slot.kw_arg is not None:
            raise InvalidProgramException(
                call_slot.node,
                'call_slots.parameters.kw_args',
                ("Method '%s' contains illegal keyword parameters"
                    % call_slot.node.name)
            )

    def _pre_process(self, node: ast.FunctionDef) -> None:
        """
        Abstract method for pre processing.
        Has to initialize self.call_slot
        """
        raise NotImplementedError()

    def _check_body(self, body: List[ast.stmt]) -> None:
        """
        Abstract method to check whether the body is valid.
        """
        raise NotImplementedError()

    def _check_variables(self) -> None:

        # argument variables
        argv = self.call_slot.args
        # universally quantified variables
        uqv = self.call_slot.uq_variables
        # return variables
        rtv = self.call_slot.return_variables

        shadowed_variables = argv.keys() & uqv.keys()

        if 0 < len(shadowed_variables):
            shadowed_variable_name = next(iter(shadowed_variables))
            raise InvalidProgramException(
                uqv[shadowed_variable_name].node,
                "call_slots.parameters.illegal_shadowing",
                "UQ variable '%s' illegally shadows an outer variable" % shadowed_variable_name
            )

        all_variable_names = argv.keys() | uqv.keys()

        assert rtv is not None
        if 0 < len(rtv):

            assert len(rtv) == 1
            return_variable = rtv[0]
            assert isinstance(return_variable, ast.Name)

            if return_variable.id in all_variable_names:
                raise InvalidProgramException(
                    return_variable,
                    "call_slots.parameters.illegal_shadowing",
                    "return variable '%s' illegally shadows an outer variable" % return_variable.id
                )

            all_variable_names.add(return_variable.id)

        invalid_variable_names = all_variable_names & _CallSlotBaseAnalyzer.__ILLEGAL_VARIABLE_NAMES

        if 0 < len(invalid_variable_names):
            illegal_variable_name = next(iter(invalid_variable_names))

            if illegal_variable_name in argv:
                illegal_variable = argv[illegal_variable_name].node
            elif illegal_variable_name in uqv:
                illegal_variable = uqv[illegal_variable_name].node
            else:
                illegal_variable = rtv[0]

            raise InvalidProgramException(
                illegal_variable,
                "call_slots.parameters.illegal_name",
                "Variable '%s' has an illegal name" % illegal_variable_name
            )


class CallSlotAnalyzer(_CallSlotBaseAnalyzer):

    def _pre_process(self, node: ast.FunctionDef) -> None:

        assert is_call_slot(node)
        scope = self.analyzer.module
        assert isinstance(scope, PythonModule)

        if self.analyzer.current_function is not None:
            raise InvalidProgramException(
                node,
                'call_slots.nested.declaration',
                "Callslot '%s' occurs inside a method" % node.name
            )
        if self.analyzer.current_class is not None:
            raise InvalidProgramException(
                node,
                'call_slots.nested.declaration',
                "Callslot '%s' occurs inside a class" % node.name
            )

        self.analyzer.define_new(scope, node.name, node)

        self.call_slot = self.analyzer.node_factory.create_call_slot(
            node.name,
            node,
            scope,
            self.analyzer.node_factory
        )

        scope.call_slots[node.name] = self.call_slot

    def _check_body(self, body: List[ast.stmt]) -> None:
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

        if self.call_slot.return_variables is None:
            raise InvalidProgramException(
                self.call_slot.node,
                'call_slots.no.call',
                "Callslot '%s' doesn't declare a call" % self.call_slot.node.name
            )

    def _check_call_declaration(self, node: Union[ast.Call, ast.Assign]) -> None:

        if self.call_slot.return_variables is not None:
            raise InvalidProgramException(
                node,
                'call_slots.multiple.calls',
                "Callslot '%s' declares more than one call" % self.call_slot.node.name
            )

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
            else:
                raise UnsupportedException(
                    node,
                    "Callslot's call supports only a single variable as return target"
                )
        else:
            self.call_slot.return_variables = []
            call = node

        self._check_call(call)

    def _check_call(self, call: ast.Call) -> None:
        self.call_slot.call = call

        if not isinstance(call.func, ast.Name):
            raise InvalidProgramException(
                call.func,
                'call_slots.call_declaration.invalid_target',
                "Callslot '%s' has an invalid call target" % self.call_slot.node.name
            )
        if call.func.id not in self.call_slot.args:
            raise InvalidProgramException(
                call.func,
                'call_slots.call_declaration.invalid_target',
                ("Callslot '%s' has an invalid call target (target must be a normal variable)" %
                    self.call_slot.node.name)
            )


class CallSlotProofAnalyzer(_CallSlotBaseAnalyzer):

    def _pre_process(self, node: ast.FunctionDef) -> None:
        assert is_call_slot_proof(node)

        if self.analyzer.current_function is None:
            raise InvalidProgramException(
                node,
                'call_slots.proof.outside_method',
                "Callslotproof '%s' occurs outside a method" % node.name
            )

        assert len(node.decorator_list) == 1
        assert isinstance(node.decorator_list[0], ast.Call)
        assert isinstance(node.decorator_list[0].func, ast.Name)
        assert node.decorator_list[0].func.id == 'CallSlotProof'

        proof_annotation = node.decorator_list[0]  # type: ast.Call

        assert len(proof_annotation.args) == 1

        call_slot_instantiation = proof_annotation.args[0]
        if not isinstance(call_slot_instantiation, ast.Call):
            raise InvalidProgramException(
                proof_annotation,
                'call_slots.proof_annotation.invalid_arg',
                "Callslot proof '%s' doesn't have a valid call slot instantiation"
            )

        if not isinstance(call_slot_instantiation.func, ast.Name):
            raise InvalidProgramException(
                proof_annotation,
                'call_slots.proof_annotation.invalid_arg',
                "Callslot proof '%s' doesn't have a valid call slot instantiation"
            )

        if len(call_slot_instantiation.args) != len(node.args.args):
            raise InvalidProgramException(
                proof_annotation,
                'call_slots.proof_annotation.invalid_arg',
            )

        self.call_slot = self.analyzer.node_factory.create_call_slot_proof(
            node.name,
            node,
            self.analyzer.current_function,
            self.analyzer.node_factory,
            call_slot_instantiation
        )

        self.analyzer.current_function.call_slot_proofs[node] = self.call_slot

    def _check_body(self, body: List[ast.stmt]) -> None:

        # Possible extensions:
        # - local variables with assignments
        # - while loops
        # - new statements (for local variables)
        # - restricted method calls (only for 'local state')

        for child in body:

            if isinstance(child, ast.Expr) and isinstance(child.value, ast.Call):
                if is_precondition(child.value) or is_postcondition(child.value):
                    continue
                if is_fold(child.value) or is_unfold(child.value):
                    continue
                if is_assume(child.value):
                    continue
                self._check_call_declaration(child.value)

            elif isinstance(child, ast.Assign):
                self._check_call_declaration(child)

            elif isinstance(child, ast.Assert):
                continue

            elif isinstance(child, ast.FunctionDef):
                if not is_call_slot_proof(child):
                    # NOTE: dead code, Analyzer will throw before we can reach this
                    raise InvalidProgramException(
                        child,
                        'call_slots.proof_body.invalid_stmt',
                        "Illegal statement in call slot proof '%s'" % self.call_slot.node.name
                    )
                # other call slot proof checks are done elsewhere

            elif isinstance(child, ast.If):
                # check purity of condition later
                self._check_body(child.body)
                self._check_body(child.orelse)

            else:
                raise InvalidProgramException(
                    child,
                    'call_slots.proof_body.invalid_stmt',
                    "Illegal statement in call slot proof '%s'" % self.call_slot.node.name
                )

    def _check_call_declaration(self, node: Union[ast.Call, ast.Assign]) -> None:

        if isinstance(node, ast.Assign):

            if not isinstance(node.value, ast.Call):
                raise InvalidProgramException(
                    node,
                    'call_slots.proof_body.invalid_stmt',
                    "Callslot proof '%s' contains an illegal assignment" % self.call_slot.node.name
                )
            call = node.value

            if len(node.targets) > 1:
                raise UnsupportedException(
                    node,
                    "Callslot proof's call can't have more than one return target"
                )

            assert len(node.targets) == 1

            if isinstance(node.targets[0], ast.Name):
                if self.call_slot.return_variables is None:
                    self.call_slot.return_variables = [node.targets[0]]
                elif (
                    len(self.call_slot.return_variables) != 1 or
                    self.call_slot.return_variables[0].id != node.targets[0].id
                ):
                    raise InvalidProgramException(
                        node,
                        'call_slots.proof_body.different_return_variables',
                        "Callslot proof '%s' uses different return variables" % self.call_slot.node.name
                    )
            else:
                raise UnsupportedException(
                    node,
                    "Callslot proof's call supports only a single variable as return target"
                )
        else:
            if self.call_slot.return_variables is None:
                self.call_slot.return_variables = []
            elif len(self.call_slot.return_variables) != 0:
                raise InvalidProgramException(
                    node,
                    'call_slots.proof_body.different_return_variables',
                    "Callslot proof '%s' uses different return variables" % self.call_slot.node.name
                )
            call = node

        self._check_closure_call(call)

    def _check_closure_call(self, closureCall: ast.Call) -> None:

        if not is_closure_call(closureCall):
            raise InvalidProgramException(
                closureCall,
                'call_slots.proof_call.not_closure_call',
                "Callslot proof '%s' has a call which is not a ClosureCall" % self.call_slot.node.name
            )

        assert len(closureCall.args) == 2  # guaranteed by type checker
        assert isinstance(closureCall.args[0], ast.Call)

        self._check_call(closureCall.args[0])

    def _check_call(self, call: ast.Call) -> None:

        if not isinstance(call.func, ast.Name):
            raise InvalidProgramException(
                call.func,
                'call_slots.proof_call.invalid_target',
                "Callslot proof '%s' has an invalid call target" % self.call_slot.node.name
            )
        if call.func.id not in self.call_slot.args:
            raise InvalidProgramException(
                call.func,
                'call_slots.proof_call.invalid_target',
                "Callslot '%s' has an invalid call target" % self.call_slot.node.name
            )


def check_closure_call(closureCall: ast.Call) -> None:
    assert is_closure_call(closureCall)
    assert len(closureCall.args) == 2  # guaranteed by type checker

    if not isinstance(closureCall.args[0], ast.Call):
        raise InvalidProgramException(
            closureCall.args[0],
            'call_slots.closure_call.invalid_call',
            "ClosureCall's first argument has to be a call of a closure"
        )

    justification = closureCall.args[1]

    if not isinstance(justification, (ast.Name, ast.Call)):
        raise InvalidProgramException(
            justification,
            'call_slots.closure_call.invalid_justification',
            "ClosureCall's justification has to be either a call slot or static dispatch"
        )

    if isinstance(justification, ast.Call):
        if not isinstance(justification.func, ast.Call):
            raise InvalidProgramException(
                justification,
                'call_slots.closure_call.invalid_justification',
                "ClosureCall's justification has to instatiate uq variables if it's a call slot"
            )

        if not isinstance(justification.func.func, ast.Name):
            raise InvalidProgramException(
                justification,
                'call_slots.closure_call.invalid_justification',
                "ClosureCall's justification has to be a named if it's a call slot"
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
    return _has_single_decorator_name(node, 'CallSlot')


def is_universally_quantified(node: ast.FunctionDef) -> bool:
    """
    Whether a function introduces universally quantified variables
    """
    return _has_single_decorator_name(node, 'UniversallyQuantified')


def is_call_slot_proof(node: ast.FunctionDef) -> bool:
    """
    Whether a function introduces universally quantified variables
    """
    return _has_single_decorator_call(node, 'CallSlotProof')


def _has_single_decorator_name(node: ast.FunctionDef, decorator_name: str) -> bool:
    """
    Whether `node' has only one decorator that equals to `decorator'
    """
    if len(node.decorator_list) != 1:
        return False

    decorator = node.decorator_list[0]
    if not isinstance(decorator, ast.Name):
        return False

    return decorator.id == decorator_name


def _has_single_decorator_call(node: ast.FunctionDef, decorator_name: str) -> bool:
    """
    Whether `node' has only one decorator that equals to `decorator'
    """
    if len(node.decorator_list) != 1:
        return False
    decorator = node.decorator_list[0]

    if not isinstance(decorator, ast.Call):
        return False

    return isinstance(decorator.func, ast.Name) and decorator.func.id == decorator_name


def is_closure_call(call: ast.Call) -> bool:
    return is_named_call(call, 'ClosureCall')


def is_precondition(call: ast.Call) -> bool:
    return is_named_call(call, 'Requires')


def is_postcondition(call: ast.Call) -> bool:
    return is_named_call(call, 'Ensures')


def is_fold(call: ast.Call) -> bool:
    return is_named_call(call, 'Unfold')


def is_unfold(call: ast.Call) -> bool:
    return is_named_call(call, 'Fold')


def is_assume(call: ast.Call) -> bool:
    return is_named_call(call, 'Assume')


def is_named_call(call: ast.Call, name: str) -> bool:
    return isinstance(call.func, ast.Name) and call.func.id == name
