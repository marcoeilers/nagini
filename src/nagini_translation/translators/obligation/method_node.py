"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Code for constructing Silver Method nodes with obligation stuff."""


import ast
from typing import List, Optional

from nagini_translation.lib import silver_nodes as sil
from nagini_translation.lib.config import obligation_config
from nagini_translation.lib.context import Context
from nagini_translation.lib.errors import rules
from nagini_translation.lib.program_nodes import (
    PythonMethod,
    PythonVar,
)
from nagini_translation.lib.typedefs import (
    Expr,
    Info,
    Method,
    Position,
    Stmt,
    VarDecl,
)
from nagini_translation.lib.viper_ast import ViperAST
from nagini_translation.sif.lib.viper_ast_extended import ViperASTExtended
from nagini_translation.translators.obligation.manager import (
    ObligationManager,
)
from nagini_translation.translators.obligation.obligation_info import (
    PythonMethodObligationInfo,
)
from nagini_translation.translators.obligation.utils import (
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

    def prepend_arg(self, arg: VarDecl, viper: Optional[ViperASTExtended] = None) -> None:
        """Prepend ``arg`` to the argument list."""
        if viper:
            info = viper.SIFInfo([], obligation_var=True)
            arg = viper.LocalVarDecl(arg.name(), arg.typ(), arg.pos(), info)
        self.args.insert(0, arg)

    def prepend_return(self, arg: VarDecl, viper: Optional[ViperASTExtended]) -> None:
        """Prepend ``arg`` to the return list."""
        if viper:
            info = viper.SIFInfo([], obligation_var=True)
            arg = viper.LocalVarDecl(arg.name(), arg.typ(), arg.pos(), info)
        self.returns.insert(0, arg)

    def prepend_body(self, statements: List[Stmt]) -> None:
        """Prepend ``statements`` to body."""
        if self.body is not None:
            self.body[0:0] = statements

    def prepend_precondition(self, preconditions: List[Expr]) -> None:
        """Prepend ``preconditions`` to precondition list."""
        self.pres[0:0] = preconditions

    def append_preconditions(self, preconditions: List[Expr]) -> None:
        """Append ``preconditions`` to precondition list."""
        self.pres.extend(preconditions)

    def append_postconditions(self, postconditions: List[Expr]) -> None:
        """Append ``postconditions`` to postcondition list."""
        self.posts.extend(postconditions)

    def prepend_postcondition(self, postcondition: Expr) -> None:
        """Prepend ``postcondition`` to postcondition list."""
        self.posts.insert(0, postcondition)

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
        res = self._viper.Method(
            method.name, method.args, method.returns,
            method.pres, method.posts, method.local_vars, body_block,
            self._position, self._info)
        return res

    def add_obligations(self) -> None:
        """Add obligation stuff to Method."""
        self._add_additional_parameters()
        self._add_additional_returns()
        self._add_additional_variables()
        self._add_additional_preconditions()
        self._add_additional_postconditions()
        if not self._need_skip_body():
            self._set_up_measures()
            self._bound_obligations()
            self._add_body_leak_check()
            self._obligation_method.append_postconditions(
                self._obligation_info.get_additional_postconditions())
        self._add_caller_leak_check()

    def _is_body_native_silver(self) -> bool:
        """Check if body is already in Silver."""
        return (self._obligation_method.body is None or isinstance(
            self._obligation_method.body,
            self._translator.jvm.viper.silver.ast.Seqn))

    def _need_skip_body(self) -> bool:
        """Check if altering body should not be done."""
        return (self._is_body_native_silver() or
                (self._python_method.contract_only and
                 not self._overriding_check))

    def _add_additional_parameters(self) -> None:
        """Add current thread, caller measures, and residue parameters."""
        if obligation_config.disable_all:
            return
        viper = self._viper if isinstance(self._viper, ViperASTExtended) else None
        self._obligation_method.prepend_arg(
            self._obligation_info.residue_level.decl)
        if not obligation_config.disable_measures:
            self._obligation_method.prepend_arg(
                self._obligation_info.caller_measure_map.get_var().decl, viper)
        self._obligation_method.prepend_arg(
            self._obligation_info.current_thread_var.decl, viper)

    def _add_additional_returns(self) -> None:
        """Add current wait level ghost return."""
        if obligation_config.disable_waitlevel_check:
            return
        viper = self._viper if isinstance(self._viper, ViperASTExtended) else None
        self._obligation_method.prepend_return(
            self._obligation_info.current_wait_level.decl, viper)

    def _add_additional_variables(self) -> None:
        """Add current wait level ghost target."""
        if obligation_config.disable_waitlevel_check:
            return
        self._obligation_method.add_local(
            self._obligation_info.current_wait_level_target)

    def _add_additional_preconditions(self) -> None:
        """Add preconditions about current thread and caller measures."""
        preconditions = []
        if not obligation_config.disable_all:
            cthread_var = self._obligation_info.current_thread_var
            cthread = sil.RefVar(cthread_var)
            preconditions.append(cthread != None)
        position = self._position
        if (self._is_body_native_silver() and
                not obligation_config.disable_termination_check):
            # Add obligations described in interface_dict.
            assert self._python_method.interface
            for obligation in self._obligation_manager.obligations:
                preconditions.extend(
                    obligation.generate_axiomatized_preconditions(
                        self._obligation_info,
                        self._python_method.interface_dict))
            func_node = self.get_function_node()
            position = self._translator.to_position(func_node, self._ctx,
                rules=rules.OBLIGATION_CALL_LEAK_CHECK_FAIL)
        translated = [
            precondition.translate(
                self._translator, self._ctx, position, self._info)
            for precondition in preconditions]
        if not obligation_config.disable_all:
            translated.append(self._translator.var_type_check(
                cthread_var.sil_name, cthread_var.type, self._position,
                self._ctx))
        self._obligation_method.prepend_precondition(translated)
        self._obligation_method.append_preconditions(
            self._obligation_info.get_additional_preconditions())

    def _add_additional_postconditions(self) -> None:
        """Initialize current wait level for the caller."""
        if obligation_config.disable_waitlevel_check:
            return
        postcondition = self._translator.initialize_current_wait_level(
            sil.PermVar(self._obligation_info.current_wait_level),
            sil.PermVar(self._obligation_info.residue_level),
            self._ctx)
        translated = postcondition.translate(
            self._translator, self._ctx, self._position, self._info)
        self._obligation_method.prepend_postcondition(translated)

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
        self._obligation_method.append_postconditions([postcondition])

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
        node = self.get_function_node()
        position = self._translator.to_position(
            node, self._ctx, rules=rules.OBLIGATION_CALL_LEAK_CHECK_FAIL)
        info = self._translator.to_info(["Caller side leak check"], self._ctx)
        precondition = check.translate(
            self._translator, self._ctx, position, info)
        self._obligation_method.append_preconditions([precondition])

    def get_function_node(self):
        """
        Returns a Python AST node representing the method. If there is no existing one
        (which is the case for interface methods defined directly in Silver), creates
        a dummy node with the correct name.
        """
        if self._python_method.node is None:
            node = ast.FunctionDef()
            if self._python_method.interface_name is not None:
                node.name = self._python_method.interface_name
            else:
                node.name = self._python_method.name
            node.lineno = 0
            node.col_offset = 0
        else:
            node = self._python_method.node
        return node

    @property
    def _obligation_info(self) -> PythonMethodObligationInfo:
        return self._python_method.obligation_info

    @property
    def _viper(self) -> ViperAST:
        return self._translator.viper
