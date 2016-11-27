"""Code for constructing Silver Method nodes with obligation stuff."""


import ast

from typing import List

from py2viper_translation.lib import silver_nodes as sil
from py2viper_translation.lib.config import obligation_config
from py2viper_translation.lib.context import Context
from py2viper_translation.lib.errors import rules
from py2viper_translation.lib.program_nodes import (
    PythonMethod,
    PythonVar,
)
from py2viper_translation.lib.typedefs import (
    Expr,
    Info,
    Method,
    Position,
    Stmt,
    VarDecl,
)
from py2viper_translation.lib.viper_ast import ViperAST
from py2viper_translation.translators.obligation.manager import (
    ObligationManager,
)
from py2viper_translation.translators.obligation.obligation_info import (
    PythonMethodObligationInfo,
)
from py2viper_translation.translators.obligation.utils import (
    bound_obligations,
)


class ObligationMethod:
    """Info for generating Silver ``Method`` AST node."""

    def __init__(
            self, name: str, args: List[VarDecl], returns: List[VarDecl],
            pres: List[Expr], posts: List[Expr], local_vars: List[VarDecl],
            body: List[Stmt]) -> None:
        self.name = name
        self.args = args
        self.returns = returns
        self.pres = pres
        self.posts = posts
        self.local_vars = local_vars
        self.body = body

    def prepend_arg(self, arg: VarDecl) -> None:
        """Prepend ``args`` to the argument list."""
        self.args.insert(0, arg)

    def prepend_body(self, statements: List[Stmt]) -> None:
        """Prepend ``statements`` to body."""
        self.body[0:0] = statements

    def prepend_precondition(self, preconditions: List[Expr]) -> None:
        """Prepend ``preconditions`` to precondition list."""
        self.pres[0:0] = preconditions

    def append_precondition(self, precondition: Expr) -> None:
        """Append ``precondition`` to precondition list."""
        self.pres.append(precondition)

    def append_postcondition(self, postcondition: Expr) -> None:
        """Append ``postcondition`` to postcondition list."""
        self.posts.append(postcondition)

    def add_local(self, var: PythonVar) -> None:
        """Add local variable to variables list."""
        self.local_vars.append(var.decl)


class ObligationMethodNodeConstructor:
    """A class that creates a method node with obligation stuff."""

    def __init__(
            self, obligation_method: ObligationMethod,
            python_method: PythonMethod, translator: 'AbstractTranslator',
            ctx: Context, obligation_manager: ObligationManager,
            position: Position, info: Info, overriding_check: bool) -> None:
        self._obligation_method = obligation_method
        self._python_method = python_method
        self._translator = translator
        self._ctx = ctx
        self._obligation_manager = obligation_manager
        self._position = position
        self._info = info
        self._overriding_check = overriding_check
        """Are we translating a behavioral subtyping check?"""

    def construct_node(self) -> Method:
        """Construct a Silver node that represents a method."""
        method = self._obligation_method
        body = method.body
        if self._is_body_native_silver():
            # Axiomatized method, do nothing with body.
            body_block = body
        else:
            # Convert body to Scala.
            body_block = self._translator.translate_block(
                body, self._position, self._info)
        return self._viper.Method(
            method.name, method.args, method.returns,
            method.pres, method.posts, method.local_vars, body_block,
            self._position, self._info)

    def add_obligations(self) -> None:
        """Add obligation stuff to Method."""
        self._add_aditional_parameters()
        self._add_additional_preconditions()
        if not self._need_skip_body():
            self._set_up_measures()
            self._bound_obligations()
            self._add_body_leak_check()
        self._add_caller_leak_check()

    def _is_body_native_silver(self) -> bool:
        """Check if body is already in Silver."""
        return isinstance(
            self._obligation_method.body,
            self._translator.jvm.viper.silver.ast.Seqn)

    def _need_skip_body(self) -> bool:
        """Check if altering body should not be done."""
        return (self._is_body_native_silver() or
                (self._python_method.contract_only and
                 not self._overriding_check))

    def _add_aditional_parameters(self) -> None:
        """Add current thread and caller measures parameters."""
        if not obligation_config.disable_measures:
            self._obligation_method.prepend_arg(
                self._obligation_info.caller_measure_map.get_var().decl)
        self._obligation_method.prepend_arg(
            self._obligation_info.current_thread_var.decl)

    def _add_additional_preconditions(self) -> None:
        """Add preconditions about current thread and caller measures."""
        cthread_var = self._obligation_info.current_thread_var
        cthread = sil.RefVar(cthread_var)
        preconditions = [
            cthread != None,        # noqa: E711
        ]
        if (self._is_body_native_silver() and
                not obligation_config.disable_termination_check):
            # Add obligations described in interface_dict.
            assert self._python_method.interface
            for obligation in self._obligation_manager.obligations:
                preconditions.extend(
                    obligation.generate_axiomatized_preconditions(
                        self._obligation_info,
                        self._python_method.interface_dict))
        translated = [
            precondition.translate(
                self._translator, self._ctx, self._position, self._info)
            for precondition in preconditions]
        translated.append(self._translator.var_type_check(
            cthread_var.sil_name, cthread_var.type, self._position,
            self._ctx))
        self._obligation_method.prepend_precondition(translated)

    def _set_up_measures(self) -> None:
        """Create and initialize method's measure map."""
        if obligation_config.disable_measures:
            return
        instances = self._obligation_info.get_all_precondition_instances()
        statements = self._obligation_info.method_measure_map.initialize(
            instances, self._translator, self._ctx, self._overriding_check)
        self._obligation_method.prepend_body(statements)
        self._obligation_method.add_local(
            self._obligation_info.method_measure_map.get_var())

    def _bound_obligations(self) -> None:
        """Convert all unbounded obligations to bounded ones."""
        if self._overriding_check:
            return
        statements = bound_obligations(
            self._obligation_info.get_all_precondition_instances(),
            self._translator, self._ctx, self._position, self._info)
        self._obligation_method.prepend_body(statements)

    def _add_body_leak_check(self) -> None:
        """Add a leak check.

        Check that method body does not leak obligations.
        """
        if obligation_config.disable_method_body_leak_check:
            return
        reference_name = self._python_method.get_fresh_name('_r')
        check = sil.InhaleExhale(
            sil.TrueLit(),
            self._obligation_manager.create_leak_check(reference_name))
        node = self._python_method.node
        assert node
        position = self._translator.to_position(
            node, self._ctx, rules=rules.OBLIGATION_BODY_LEAK_CHECK_FAIL)
        info = self._translator.to_info(["Body leak check."], self._ctx)
        postcondition = check.translate(
            self._translator, self._ctx, position, info)
        self._obligation_method.append_postcondition(postcondition)

    def _add_caller_leak_check(self) -> None:
        """Add a leak check.

        Check that if callee is not terminating, caller has no
        obligations.
        """
        if obligation_config.disable_call_context_leak_check:
            return
        # MustTerminate leak check.
        must_terminate = self._obligation_manager.must_terminate_obligation
        cthread = self._obligation_info.current_thread_var
        predicate = must_terminate.create_predicate_access(cthread)
        termination_leak_check = sil.CurrentPerm(predicate) == sil.NoPerm()
        # Other obligations leak check.
        reference_name = self._python_method.get_fresh_name('_r')
        leak_check = self._obligation_manager.create_leak_check(
            reference_name)
        if self._python_method.interface:
            if must_terminate.is_interface_method_terminating(
                    self._python_method.interface_dict):
                exhale = self._obligation_info.caller_measure_map.check(
                    sil.RefVar(self._obligation_info.current_thread_var),
                    sil.RawIntExpression(1))
            else:
                exhale = sil.BigAnd([termination_leak_check, leak_check])
        else:
            # Termination condition.
            tcond = self._obligation_info.create_termination_check(False)
            # Combination.
            exhale = sil.BigOr([
                tcond,
                sil.BigAnd([termination_leak_check, leak_check])
            ])
        check = sil.InhaleExhale(sil.TrueLit(), exhale)
        # Translate to Silver.
        if self._python_method.node is None:
            # TODO: Handle interface methods properly.
            node = ast.AST()
            node.lineno = 0
            node.col_offset = 0
        else:
            node = self._python_method.node
        position = self._translator.to_position(
            node, self._ctx, rules=rules.OBLIGATION_CALL_LEAK_CHECK_FAIL)
        info = self._translator.to_info(["Caller side leak check"], self._ctx)
        precondition = check.translate(
            self._translator, self._ctx, position, info)
        self._obligation_method.append_precondition(precondition)

    @property
    def _obligation_info(self) -> PythonMethodObligationInfo:
        return self._python_method.obligation_info

    @property
    def _viper(self) -> ViperAST:
        return self._translator.viper
