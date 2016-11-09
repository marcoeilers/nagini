"""Information about obligation use in contracts."""


import abc
import ast

from typing import List

from py2viper_translation.lib import silver_nodes as sil
from py2viper_translation.lib.config import obligation_config
from py2viper_translation.lib.context import Context
from py2viper_translation.lib.program_nodes import (
    PythonMethod,
    PythonVar,
)
from py2viper_translation.lib.guard_collectors import (
    GuardCollectingVisitor,
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
LOOP_TERMINATION_FLAG_NAME = '_loop_termination_flag'
LOOP_ORIGINAL_MUST_TERMINATE_AMOUNT_NAME = '_loop_original_must_terminate'


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
        conjunction = sil.BigAnd([
            sil.PythonBoolExpression(part)
            for part in self.guard
        ])
        return conjunction


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

    def _create_var(
            self, name: str, class_name: str,
            translator: 'Translator', local: bool = False) -> PythonVar:
        module = self._method.get_module()
        cls = module.global_module.classes[class_name]
        return self._method.create_variable(
            name, cls, translator, local=local)

    def _create_silver_var(
            self, name: str, translator: 'AbstractTranslator',
            typ: 'viper_ast.Type', local: bool = False) -> SilverVar:
        sil_name = self._method.get_fresh_name(name)
        decl = translator.viper.LocalVarDecl(
            sil_name, typ, translator.viper.NoPosition,
            translator.viper.NoInfo)
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
        self.current_thread_var = self._create_var(
            CURRENT_THREAD_NAME, 'Thread', translator.translator)
        caller_measure_map_var = self._create_measure_var(
            MEASURES_CALLER_NAME, translator)
        self.caller_measure_map = MeasureMap(caller_measure_map_var)
        method_measure_map_var = self._create_measure_var(
            MEASURES_METHOD_NAME, translator)
        self.method_measure_map = MeasureMap(
            method_measure_map_var)

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
        self.loop_check_before_var = self._create_var(
            LOOP_CHECK_BEFORE_NAME, 'bool', translator.translator,
            local=True)
        self.termination_flag_var = self._create_var(
            LOOP_TERMINATION_FLAG_NAME, 'bool', translator.translator,
            local=True)
        self.original_must_terminate_var = self._create_perm_var(
            LOOP_ORIGINAL_MUST_TERMINATE_AMOUNT_NAME, translator,
            local=True)
        self.iteration_err_var = err_var
        """In the for loop translation holds ``__iter__`` result."""

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
