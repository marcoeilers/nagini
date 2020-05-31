"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Information about obligation use in contracts."""


import abc
import ast
from typing import List

from nagini_translation.lib import silver_nodes as sil
from nagini_translation.lib.config import obligation_config
from nagini_translation.lib.constants import PRIMITIVE_BOOL_TYPE
from nagini_translation.lib.context import Context
from nagini_translation.lib.guard_collectors import (
    GuardCollectingVisitor,
)
from nagini_translation.lib.program_nodes import (
    PythonMethod,
    PythonVar,
)
from nagini_translation.lib.typedefs import (
    Expr,
    Stmt,
    Type,
)
from nagini_translation.sif.lib.viper_ast_extended import ViperASTExtended
from nagini_translation.translators.obligation.manager import (
    ObligationManager,
)
from nagini_translation.translators.obligation.measures import (
    MeasureMap,
)
from nagini_translation.translators.obligation.types.base import (
    ObligationInstance,
)

CURRENT_THREAD_NAME = '_cthread'
RESIDUE_LEVEL_METHOD_NAME = '_residue'
RESIDUE_LEVEL_LOOP_NAME = '_residue'
CURRENT_WAIT_LEVEL_NAME = '_current_wait_level'
CURRENT_WAIT_LEVEL_TARGET_NAME = '_cwl'
MEASURES_CALLER_NAME = '_caller_measures'
MEASURES_METHOD_NAME = '_method_measures'
MEASURES_LOOP_NAME = '_loop_measures'
LOOP_CHECK_BEFORE_NAME = '_loop_check_before'
LOOP_TERMINATION_FLAG_NAME = '_loop_termination_flag'
LOOP_ORIGINAL_MUST_TERMINATE_AMOUNT_NAME = '_loop_original_must_terminate'


def _create_guard_expression(parts: List[ast.AST]) -> sil.BigAnd:
    """Transform guarding sequence into the guard expression."""
    conjunction = sil.BigAnd([
        sil.PythonBoolExpression(part)
        for part in parts
    ])
    return conjunction


@PythonVar.register         # pylint: disable=no-member
class SilverVar:
    """A silver variable that has no representation in Python.

    This class is a structural subtype of ``PythonVar`` that allows to
    manage variables non-representable with ``PythonVar`` (like the ones
    that have ``Perm`` type) in the same way as all other variables.
    """

    def __init__(self, name: str, decl: 'viper_ast.LocalVarDecl',
                 ref: 'viper_ast.LocalVarRef') -> None:
        self.name = name
        self.sil_name = name
        self.decl = decl
        """A variable declaration."""

        self._ref = ref
        self.show_in_ce = False

    def ref(self, node: ast.AST = None,                         # pylint: disable=unused-argument
            ctx: Context = None) -> 'viper_ast.LocalVarRef':    # pylint: disable=unused-argument
        """A variable reference.

        Arguments are ignored.
        """
        return self._ref

    def process(self, sil_name: str, translator: 'Translator') -> None:
        """Just do nothing."""


class GuardedObligationInstance:
    """Obligation instance with its guard."""

    def __init__(
            self, guard: List[ast.AST],
            obligation_instance: ObligationInstance) -> None:
        self.guard = guard
        self.obligation_instance = obligation_instance

    def create_guard_expression(self) -> sil.BigAnd:
        """Create a conjunction representing a guard."""
        return _create_guard_expression(self.guard)


class BaseObligationInfo(GuardCollectingVisitor):
    """Info about the obligation use in loop/method contract."""

    def __init__(
            self, obligaton_manager: ObligationManager,
            method: PythonMethod) -> None:
        super().__init__()
        self._current_instance_map = None
        self._obligation_manager = obligaton_manager
        self._method = method
        self._all_instances = {}
        self._wait_level_guards = {}

    def visit_Call(self, node: ast.Call) -> None:
        for obligation in self._obligation_manager.obligations:
            obligation_instance = obligation.check_node(
                node, self, self._method)
            if obligation_instance:
                guard = self.current_guard[:]
                if (isinstance(node.func, ast.Name) and
                        node.func.id == "TerminatesSif"):
                    guard.append(node.args[0])
                instance = GuardedObligationInstance(
                    guard, obligation_instance)
                self._current_instance_map[obligation.identifier()].append(
                    instance)
                self._all_instances[node] = instance
                break
        else:
            if isinstance(node.func, ast.Name) and node.func.id == 'WaitLevel':
                self._wait_level_guards[node] = self.current_guard[:]
            else:
                super().visit_Call(node)

    def get_instance(self, node: ast.Call) -> GuardedObligationInstance:
        """Get ``GuardedObligationInstance`` represented by node."""
        return self._all_instances[node]

    @abc.abstractmethod
    def _get_must_terminate_instances(self) -> List[GuardedObligationInstance]:
        """Get all ``MustTerminate`` obligation instances."""

    @abc.abstractmethod
    def _check_must_terminate_measure_decrease(
            self, measure: sil.IntExpression) -> sil.BoolExpression:
        """Create a check if provided measure is smaller than current."""

    def create_termination_check(
            self, ignore_measures: bool) -> sil.BoolExpression:
        """Create a check if callee is going to terminate.

        This method is essentially a ``tcond`` macro as defined in
        ``MustTerminate`` documentation.
        """
        disjuncts = []
        for instance in self._get_must_terminate_instances():
            guard = instance.create_guard_expression()
            if ignore_measures:
                disjuncts.append(guard)
            else:
                measure_check = self._check_must_terminate_measure_decrease(
                    instance.obligation_instance.get_measure())
                disjuncts.append(sil.BigAnd([guard, measure_check]))
        return sil.BigOr(disjuncts)

    def get_wait_level_guard(self, node: ast.Call) -> sil.BigAnd:
        """Return a guard for the given WaitLevel expression."""
        return _create_guard_expression(self._wait_level_guards[node])

    def _create_var(
            self, name: str, class_name: str,
            translator: 'Translator', local: bool = False) -> PythonVar:
        module = self._method.module
        cls = module.global_module.classes[class_name]
        return self._method.create_variable(
            name, cls, translator, local=local)

    def _create_silver_var(
            self, name: str, translator: 'AbstractTranslator',
            typ: Type, local: bool = False) -> SilverVar:
        sil_name = self._method.get_fresh_name(name)
        if isinstance(translator.viper, ViperASTExtended):
            info = translator.viper.SIFInfo([], obligation_var=True)
        else:
            info = translator.viper.NoInfo
        decl = translator.viper.LocalVarDecl(
            sil_name, typ, translator.viper.NoPosition, info)
        ref = translator.viper.LocalVar(
            sil_name, typ, translator.viper.NoPosition,
            translator.viper.NoInfo)
        var = SilverVar(sil_name, decl, ref)
        if local:
            self._method.add_local(sil_name, var)
        return var

    def _create_perm_var(
            self, name: str, translator: 'AbstractTranslator',
            local: bool = False) -> PythonVar:
        return self._create_silver_var(
            name, translator, translator.viper.Perm, local=local)

    def _create_seq_var(
            self, name: str,
            translator: 'AbstractTranslator') -> PythonVar:
        return self._create_silver_var(
            name, translator, translator.viper.SeqType(translator.viper.Ref))

    def _create_measure_var(
            self, name: str, translator: 'AbstractTranslator',
            local: bool = False) -> PythonVar:
        typ = translator.viper.SeqType(
            translator.viper.DomainType('Measure$', {}, []))
        return self._create_silver_var(name, translator, typ, local=local)


class PythonMethodObligationInfo(BaseObligationInfo):
    """Info about the obligation use in a specific method."""

    def __init__(
            self, obligaton_manager: ObligationManager,
            method: PythonMethod, translator: 'AbstractTranslator') -> None:
        super().__init__(obligaton_manager, method)
        self._precondition_instances = {}
        self._postcondition_instances = {}
        for obligation in self._obligation_manager.obligations:
            obligation_id = obligation.identifier()
            self._precondition_instances[obligation_id] = []
            self._postcondition_instances[obligation_id] = []
        self._variables = {
            CURRENT_THREAD_NAME: self._create_var(
                CURRENT_THREAD_NAME, 'Thread', translator.translator),
            RESIDUE_LEVEL_METHOD_NAME: self._create_perm_var(
                RESIDUE_LEVEL_METHOD_NAME, translator),
            CURRENT_WAIT_LEVEL_NAME: self._create_perm_var(
                CURRENT_WAIT_LEVEL_NAME, translator),
            CURRENT_WAIT_LEVEL_TARGET_NAME: self._create_perm_var(
                CURRENT_WAIT_LEVEL_TARGET_NAME, translator),
        }
        caller_measure_map_var = self._create_measure_var(
            MEASURES_CALLER_NAME, translator)
        self.caller_measure_map = MeasureMap(caller_measure_map_var)
        method_measure_map_var = self._create_measure_var(
            MEASURES_METHOD_NAME, translator)
        self.method_measure_map = MeasureMap(
            method_measure_map_var)
        self._additional_preconditions = []
        self._additional_postconditions = []

    @property
    def current_thread_var(self) -> PythonVar:
        """Return variable that represents current thread argument."""
        return self._variables[CURRENT_THREAD_NAME]

    @property
    def residue_level(self) -> PythonVar:
        """Return variable that represents the residue level argument."""
        return self._variables[RESIDUE_LEVEL_METHOD_NAME]

    @property
    def current_wait_level(self) -> PythonVar:
        """Return variable that represents current wait level return value."""
        return self._variables[CURRENT_WAIT_LEVEL_NAME]

    @property
    def current_wait_level_target(self) -> PythonVar:
        """Return target variable to which the current wait level is assigned.

        .. note::
            In the wait level use in method calls encoding, we need to
            have the fresh variable that denotes the current thread's
            wait level after the precondition was exhaled, but before
            the postcondition is inhaled. We use an additional ghost
            return variable ``CURRENT_WAIT_LEVEL_NAME`` for this:

            .. code-block:: silver

                method foo(...) returns (..., _current_wait_level: Perm)

            However, when this method ``foo`` is called, we need a
            variable to which we can assign this return value.
            Therefore, we introduce a local variable
            ``CURRENT_WAIT_LEVEL_TARGET_NAME`` in each method for this
            purpose:

            .. code-block:: silver

                ..., _cwl := foo(...)

            Note that this variable ``CURRENT_WAIT_LEVEL_TARGET_NAME``
            is otherwise not used.
        """
        return self._variables[CURRENT_WAIT_LEVEL_TARGET_NAME]

    def traverse_contract(self) -> None:
        """Collect all needed information about obligations."""
        self._traverse_preconditions()
        self._traverse_postconditions()
        self._traverse_declared_exceptions()

    def _traverse_preconditions(self) -> None:
        """Collect all needed information about obligations."""
        assert self._current_instance_map is None
        self._current_instance_map = self._precondition_instances
        for precondition, _ in self._method.precondition:
            self.traverse(precondition)
        self._current_instance_map = None

    def _traverse_postconditions(self) -> None:
        """Collect all needed information about obligations."""
        assert self._current_instance_map is None
        self._current_instance_map = self._postcondition_instances
        for postcondition, _ in self._method.postcondition:
            self.traverse(postcondition)
        self._current_instance_map = None

    def _traverse_declared_exceptions(self) -> None:
        """Collect all needed information about obligations."""
        assert self._current_instance_map is None
        self._current_instance_map = self._postcondition_instances
        for postconditions in self._method.declared_exceptions.values():
            for postcondition, _ in postconditions:
                self.traverse(postcondition)
        self._current_instance_map = None

    def _get_must_terminate_instances(self) -> List[GuardedObligationInstance]:
        return self.get_precondition_instances(
            self._obligation_manager.must_terminate_obligation.identifier())

    def _check_must_terminate_measure_decrease(
            self, measure: sil.IntExpression) -> sil.BoolExpression:
        return self.caller_measure_map.check(
            sil.RefVar(self.current_thread_var), measure)

    def get_precondition_instances(
            self, obligation_id: str) -> List[ObligationInstance]:
        """Return precondition instances of specific obligation type."""
        return self._precondition_instances[obligation_id]

    def get_all_precondition_instances(self) -> List[ObligationInstance]:
        """Return all precondition instances."""
        all_instances = []
        for instances in self._precondition_instances.values():
            all_instances.extend(instances)
        return all_instances

    def add_precondition(self, expr: Expr) -> None:
        """Add additional precondition at the end."""
        self._additional_preconditions.append(expr)

    def get_additional_preconditions(self) -> List[Expr]:
        """Return additional preconditions."""
        return self._additional_preconditions

    def add_postcondition(self, expr: Expr) -> None:
        """Add additional postcondition at the end."""
        self._additional_postconditions.append(expr)

    def get_additional_postconditions(self) -> List[Expr]:
        """Return additional postconditions."""
        return self._additional_postconditions


class PythonLoopObligationInfo(BaseObligationInfo):
    """Info about the obligation use in a loop."""

    def __init__(
            self, obligaton_manager: ObligationManager,
            node: ast.While, translator: 'AbstractTranslator',
            method: PythonMethod, err_var: PythonVar = None) -> None:
        super().__init__(obligaton_manager, method)
        self.node = node
        self._instances = dict(
            (obligation.identifier(), [])
            for obligation in self._obligation_manager.obligations)
        loop_measure_map_var = self._create_measure_var(
            MEASURES_LOOP_NAME, translator,
            local=not obligation_config.disable_measures)
        self.loop_measure_map = MeasureMap(loop_measure_map_var)
        self._variables = {
            LOOP_CHECK_BEFORE_NAME: self._create_var(
                LOOP_CHECK_BEFORE_NAME, PRIMITIVE_BOOL_TYPE,
                translator.translator, local=True),
            LOOP_TERMINATION_FLAG_NAME: self._create_var(
                LOOP_TERMINATION_FLAG_NAME, PRIMITIVE_BOOL_TYPE,
                translator.translator, local=True),
            LOOP_ORIGINAL_MUST_TERMINATE_AMOUNT_NAME: self._create_perm_var(
                LOOP_ORIGINAL_MUST_TERMINATE_AMOUNT_NAME, translator,
                local=True),
            RESIDUE_LEVEL_LOOP_NAME: self._create_perm_var(
                RESIDUE_LEVEL_LOOP_NAME, translator, local=True),
        }
        self.iteration_err_var = err_var
        """In the for loop translation holds ``__iter__`` result."""
        self._additional_invariants = []
        self._prepend_body = []
        self._after_loop = []

    @property
    def loop_check_before_var(self) -> PythonVar:
        """Return variable that indicates exhaling before loop."""
        return self._variables[LOOP_CHECK_BEFORE_NAME]

    @property
    def termination_flag_var(self) -> PythonVar:
        """Return variable that indicates if loop promised to terminate."""
        return self._variables[LOOP_TERMINATION_FLAG_NAME]

    @property
    def original_must_terminate_var(self) -> PythonVar:
        """Return variable that holds original termination amount."""
        return self._variables[LOOP_ORIGINAL_MUST_TERMINATE_AMOUNT_NAME]

    @property
    def residue_level(self) -> PythonVar:
        """Return variable that represents the residue level."""
        return self._variables[RESIDUE_LEVEL_LOOP_NAME]

    @property
    def current_thread_var(self) -> PythonVar:
        """Return the variable that denotes current thread in method."""
        return self._method.obligation_info.current_thread_var

    def traverse_invariants(self) -> None:
        """Collect all needed information about obligations."""
        assert self._current_instance_map is None
        self._current_instance_map = self._instances
        for invariant, _ in self._method.loop_invariants[self.node]:
            if isinstance(invariant, ast.Expr):
                self.traverse(invariant.value.args[0])
            else:
                self.traverse(invariant.args[0])
        self._current_instance_map = None

    def _get_must_terminate_instances(self) -> List[GuardedObligationInstance]:
        return self.get_instances(
            self._obligation_manager.must_terminate_obligation.identifier())

    def _check_must_terminate_measure_decrease(
            self, measure: sil.IntExpression) -> sil.BoolExpression:
        return self.loop_measure_map.check(
            sil.RefVar(self.current_thread_var), measure)

    def get_all_instances(self) -> List[ObligationInstance]:
        """Return all invariant instances."""
        return list(self._all_instances.values())

    def get_instances(self, obligation_id: str) -> List[ObligationInstance]:
        """Return invariant instances of specific obligation type."""
        return self._instances[obligation_id]

    def construct_loop_condition(self) -> sil.BoolExpression:
        """Construct loop condition."""
        if isinstance(self.node, ast.While):
            return sil.PythonBoolExpression(self.node.test)
        else:
            return sil.RefVar(self.iteration_err_var) == None  # noqa: E711

    def prepend_body(self, stmt: Stmt) -> None:
        """Add statement at the beginning of loop body."""
        self._prepend_body.append(stmt)

    def get_prepend_body(self) -> List[Stmt]:
        """Return statements to be prepended to the loop body."""
        return self._prepend_body

    def append_after_loop(self, stmt: Stmt) -> None:
        """Add statement after the loop."""
        self._after_loop.append(stmt)

    def get_after_loop(self) -> List[Stmt]:
        """Get statements to be appended after the loop."""
        return self._after_loop

    def add_invariant(self, expr: Expr) -> None:
        """Add the additional invariant at the end."""
        self._additional_invariants.append(expr)

    def get_additional_invariants(self) -> List[Expr]:
        """Return additional invariants."""
        return self._additional_invariants
