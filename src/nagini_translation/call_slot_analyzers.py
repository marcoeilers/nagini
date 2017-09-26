import ast
from typing import Union
from nagini_translation import analyzer as analyzer_pkg
from nagini_translation.lib.program_nodes import (
    PythonModule,
    PythonMethod,
    CallSlot
)
from nagini_translation.lib.util import (
    UnsupportedException,
    InvalidProgramException,
)


class CallSlotAnalyzer:

    def __init__(self, analyzer: 'analyzer_pkg.Analyzer') -> None:
        self.analyzer = analyzer
        self.call_slot = None  # type: CallSlot

    def analyze(self, node: ast.FunctionDef) -> None:
        """
        Preprocess the call slot `node'.
        """
        assert is_call_slot(node)

        analyzer = self.analyzer
        scope = analyzer.module
        assert isinstance(scope, PythonModule)

        if analyzer.current_function is not None:
            raise UnsupportedException(node, 'nested call slots')
        if analyzer.current_class is not None:
            raise UnsupportedException(node, 'call slot as class member')

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
            # TODO: Check uq vars (shadowing of normal vars?)
            body_node._parent = node

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
        # - Only variables from call slot are used (no globals)
        #   - don't want a call slot with a call to a global closure

        self._check_body(body_node.body)

        # cleanup
        if has_uq_vars:
            self.call_slot.precondition = mock_call_slot.precondition
            self.call_slot.postcondition = mock_call_slot.postcondition
            analyzer.outer_functions.pop()
        analyzer.current_function = None

    def _check_body(self, body):
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

            if isinstance(node.value, ast.Call):
                call = node.value
            else:
                raise InvalidProgramException(
                    node,
                    'call_slots.body.invalid_stmt',
                    'Callslot declarations must only consist of contracts and a single call'
                )

            if len(node.targets) > 1:
                raise UnsupportedException(
                    node,
                    "Callslot's call can't have more than one return target"
                )

            assert len(node.targets) == 1

            if isinstance(node.targets[0], ast.Name):
                self.call_slot.return_variables = [node.targets[0]]
            elif isinstance(node.targets[0], ast.Tuple):
                # FIXME: doesn't work with nested destructuring
                # e.g., `a, (b, c), d = f(1, 2, 3)`
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

    def __init__(self, analyzer: 'analyzer_pkg.Analyzer') -> None:
        self.analyzer = analyzer

    def analyze(self, node: ast.FunctionDef) -> None:
        """
        Preprocess the call slot `node'.
        """
        pass  # FIXME: implement


def _check_method_declaration(method: PythonMethod, analyzer: 'analyzer_pkg.Analyzer') -> None:
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
    # TODO: what about defaults?


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
