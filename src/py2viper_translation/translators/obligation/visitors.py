"""Visitors for collecting information about obligation use.

.. todo:: Vytautas

    Rename this file to something more meaningful.
"""


import ast

from typing import List

from py2viper_translation.lib import expressions as expr
from py2viper_translation.lib.program_nodes import (
    PythonMethod,
    PythonProgram,
    PythonVar,
)
from py2viper_translation.lib.guard_collectors import (
    GuardCollectingVisitor,
)
from py2viper_translation.lib.util import (
    is_io_existential,
    is_invariant,
    UnsupportedException,
)
from py2viper_translation.translators.obligation.manager import (
    ObligationManager,
)
from py2viper_translation.translators.obligation.measures import (
    MeasureMap,
)
from py2viper_translation.translators.obligation.types.base import (
    ObligationInstance,
)


CURRENT_THREAD_NAME = '_cthread'
MEASURES_CALLER_NAME = '_caller_measures'
MEASURES_METHOD_NAME = '_method_measures'
MEASURES_METHOD_CONTENTS_NAME = '_method_measures_contents'
MEASURES_LOOP_NAME = '_loop_measures'
ORIGINAL_MUST_TERMINATE_AMOUNT_NAME = '_original_must_terminate'
INCREASED_MUST_TERMINATE_AMOUNT_NAME = '_increased_must_terminate'
LOOP_CHECK_BEFORE_NAME = '_loop_check_before'


class SilverVar:
    """A silver variable that has no representation in Python.

    This class is a structural subtype of ``PythonVar`` that allows to
    manage variables non-representable with ``PythonVar`` (like the ones
    that have ``Perm`` type) in the same way as all other variables.
    """

    def __init__(self, decl: 'viper_ast.LocalVarDecl',
                 ref: 'viper_ast.LocalVarRef') -> None:
        self.decl = decl
        """A variable declaration."""

        self._ref = ref

    def ref(self) -> 'viper_ast.LocalVarRef':
        """A variable reference."""
        return self._ref


class GuardedObligationInstance:
    """Obligation instance with its guard."""

    def __init__(
            self, guard: List[ast.AST],
            obligation_instance: ObligationInstance) -> None:
        self.guard = guard
        self.obligation_instance = obligation_instance

    def create_guard_expression(self) -> expr.BigAnd:
        """Create a conjunction representing a guard."""
        conjunction = expr.BigAnd([
            expr.PythonBoolExpression(part)
            for part in self.guard
        ])
        return conjunction


class BaseObligationInfo(GuardCollectingVisitor):
    """Info about the obligation use."""

    def __init__(
            self, obligaton_manager: ObligationManager,
            method: PythonMethod) -> None:
        super().__init__()
        self._current_instance_map = None
        self._obligation_manager = obligaton_manager
        self._method = method
        self._all_instances = {}

    def visit_Call(self, node: ast.Call) -> None:
        for obligation in self._obligation_manager.obligations:
            obligation_instance = obligation.check_node(
                node, self, self._method)
            if obligation_instance:
                instance = GuardedObligationInstance(
                    self.current_guard[:], obligation_instance)
                self._current_instance_map[obligation.identifier()].append(
                    instance)
                self._all_instances[node] = instance
                break
        else:
            super().visit_Call(node)

    def get_instance(self, node: ast.Call) -> GuardedObligationInstance:
        """Get ``GuardedObligationInstance`` represented by node."""
        return self._all_instances[node]

    def _get_program(self) -> PythonProgram:
        scope = self._method
        while scope.superscope:
            scope = scope.superscope
        return scope

    def _create_var(
            self, name: str, class_name: str,
            translator: 'Translator') -> PythonVar:
        program = self._get_program()
        cls = program.classes[class_name]
        return self._method.create_variable(
            name, cls, translator, local=False)

    def _create_silver_var(
            self, name: str, translator: 'AbstractTranslator',
            typ: 'viper_ast.Type') -> SilverVar:
        sil_name = self._method.get_fresh_name(name)
        decl = translator.viper.LocalVarDecl(
            sil_name, typ, translator.viper.NoPosition,
            translator.viper.NoInfo)
        ref = translator.viper.LocalVar(
            sil_name, typ, translator.viper.NoPosition,
            translator.viper.NoInfo)
        return SilverVar(decl, ref)

    def _create_perm_var(
            self, name: str,
            translator: 'AbstractTranslator') -> PythonVar:
        return self._create_silver_var(
            name, translator, translator.viper.Perm)

    def _create_seq_var(
            self, name: str,
            translator: 'AbstractTranslator') -> PythonVar:
        return self._create_silver_var(
            name, translator, translator.viper.SeqType(translator.viper.Ref))


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
        self.current_thread_var = self._create_var(
            CURRENT_THREAD_NAME, 'Thread', translator.translator)
        caller_measure_map_var = self._create_var(
            MEASURES_CALLER_NAME, 'object', translator.translator)
        self.caller_measure_map = MeasureMap(caller_measure_map_var)
        method_measure_map_var = self._create_var(
            MEASURES_METHOD_NAME, 'object', translator.translator)
        method_measure_map_contents_var = self._create_seq_var(
            MEASURES_METHOD_CONTENTS_NAME, translator)
        self.method_measure_map = MeasureMap(
            method_measure_map_var, method_measure_map_contents_var)
        self.original_must_terminate_var = self._create_perm_var(
            ORIGINAL_MUST_TERMINATE_AMOUNT_NAME, translator)
        self.increased_must_terminate_var = self._create_perm_var(
            INCREASED_MUST_TERMINATE_AMOUNT_NAME, translator)

    def traverse_preconditions(self) -> None:
        """Collect all needed information about obligations."""
        assert self._current_instance_map is None
        self._current_instance_map = self._precondition_instances
        for precondition, aliases in self._method.precondition:
            self.traverse(precondition)
        self._current_instance_map = None

    def traverse_postconditions(self) -> None:
        """Collect all needed information about obligations."""
        assert self._current_instance_map is None
        self._current_instance_map = self._postcondition_instances
        for postcondition, aliases in self._method.postcondition:
            self.traverse(postcondition)
        self._current_instance_map = None

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


class PythonLoopObligationInfo(BaseObligationInfo):
    """Info about the obligation use in a loop."""

    def __init__(
            self, obligaton_manager: ObligationManager,
            node: ast.While, translator: 'AbstractTranslator',
            method: PythonMethod) -> None:
        super().__init__(obligaton_manager, method)
        self.node = node
        self._instances = dict(
            (obligation.identifier(), [])
            for obligation in self._obligation_manager.obligations)
        loop_measure_map_var = self._create_var(
            MEASURES_LOOP_NAME, 'object', translator.translator)
        self.loop_measure_map = MeasureMap(loop_measure_map_var)
        self.loop_check_before = self._create_var(
            LOOP_CHECK_BEFORE_NAME, 'bool', translator.translator)

    @property
    def current_thread_var(self) -> PythonVar:
        """Return the variable that denotes current thread in method."""
        return self._method.obligation_info.current_thread_var

    def traverse_invariants(self) -> None:
        """Collect all needed information about obligations."""
        assert self._current_instance_map is None
        self._current_instance_map = self._instances
        for statement in self.node.body:
            if is_invariant(statement):
                self.traverse(statement.value.args[0])
            elif is_io_existential(statement):
                # TODO: Implement IOExists in loop.
                raise UnsupportedException(self.node, 'IOExists in loop.')
        self._current_instance_map = None
