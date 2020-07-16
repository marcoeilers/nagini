"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Public interface to obligation translator."""


import ast

from typing import List, Tuple, Union

from nagini_translation.lib import silver_nodes as sil
from nagini_translation.lib.context import Context
from nagini_translation.lib.jvmaccess import JVM
from nagini_translation.lib.program_nodes import (
    PythonMethod,
    PythonVar,
)
from nagini_translation.lib.typedefs import (
    Expr,
    Info,
    Field,
    Method,
    Position,
    Predicate,
    Stmt,
    StmtsAndExpr,
    VarDecl,
)
from nagini_translation.lib.typeinfo import TypeInfo
from nagini_translation.lib.util import (
    get_func_name,
    InvalidProgramException,
    UnsupportedException,
)
from nagini_translation.lib.viper_ast import ViperAST
from nagini_translation.translators.abstract import TranslatorConfig
from nagini_translation.translators.common import CommonTranslator
from nagini_translation.translators.obligation.loop import (
    LoopObligationTranslator,
)
from nagini_translation.translators.obligation.manager import (
    ObligationManager,
)
from nagini_translation.translators.obligation.method import (
    MethodObligationTranslator,
)
from nagini_translation.translators.obligation.obligation_info import (
    PythonMethodObligationInfo,
)
from nagini_translation.translators.obligation.waitlevel import (
    WaitLevelTranslator,
)


class ObligationTranslator(CommonTranslator):
    """Translator for obligations."""

    def __init__(self, config: TranslatorConfig, jvm: JVM, source_file: str,
                 type_info: TypeInfo, viper_ast: ViperAST) -> None:
        super().__init__(config, jvm, source_file, type_info, viper_ast)
        self._obligation_manager = ObligationManager()
        self._method_translator = MethodObligationTranslator(
            config, jvm, source_file, type_info, viper_ast,
            self._obligation_manager)
        self._loop_translator = LoopObligationTranslator(
            config, jvm, source_file, type_info, viper_ast,
            self._obligation_manager)
        self._wait_level_translator = WaitLevelTranslator(
            config, jvm, source_file, type_info, viper_ast,
            self._obligation_manager)

    def enter_loop_translation(
            self, node: Union[ast.While, ast.For], ctx: Context,
            err_var: PythonVar = None) -> None:
        """Update context with info needed to translate loop."""
        self._loop_translator.enter_loop_translation(node, ctx, err_var)

    def leave_loop_translation(self, ctx: Context) -> None:
        """Remove loop translation info from context."""
        self._loop_translator.leave_loop_translation(ctx)

    def create_while_node(
            self, ctx: Context, cond: Expr,
            invariants: List[Expr],
            local_vars: List[VarDecl],
            body: Stmt, node: Union[ast.While, ast.For]) -> List[Stmt]:
        """Construct a while loop AST node with obligation stuff."""
        return self._loop_translator.create_while_node(
            ctx, cond, invariants, local_vars, body, node)

    def translate_obligation_contractfunc_call(
            self, node: ast.Call, ctx: Context, impure: bool) -> StmtsAndExpr:
        """Translate a call to obligation contract function."""
        func_name = get_func_name(node)
        if func_name == 'MustTerminate':
            if not impure:
                raise InvalidProgramException(node, 'invalid.contract.position')
            return self._translate_must_terminate(node, ctx)
        elif func_name == 'MustRelease':
            if not impure:
                raise InvalidProgramException(node, 'invalid.contract.position')
            return self._translate_must_release(node, ctx)
        elif func_name == 'WaitLevel':
            raise InvalidProgramException(
                node, 'invalid.wait_level.use')
        elif func_name == 'Level':
            raise InvalidProgramException(
                node, 'invalid.level.use')
        else:
            raise UnsupportedException(
                node, 'Unsupported contract function.')

    def translate_must_invoke_token(
            self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """Translate a call to ``token``."""
        if ctx.obligation_context.is_translating_loop():
            return self._loop_translator.translate_must_invoke(node, ctx)
        else:
            return self._method_translator.translate_must_invoke(node, ctx)

    def translate_must_invoke_ctoken(
            self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """Translate a call to ``ctoken``."""
        if ctx.obligation_context.is_translating_loop():
            return self._loop_translator.translate_may_invoke(
                node, ctx)
        elif ctx.obligation_context.is_translating_posts:
            if ctx.actual_function.name != 'Gap':
                raise InvalidProgramException(
                    node, 'invalid.postcondition.ctoken_not_allowed')
            else:
                return self._method_translator.translate_may_invoke(
                    node, ctx)
        else:
            return self._method_translator.translate_may_invoke(
                node, ctx)

    def is_wait_level_comparison(self, node: ast.Compare,
                                 ctx: Context) -> bool:
        """Check if we are comparing with ``WaitLevel``."""
        return self._wait_level_translator.is_wait_level_comparison(
            node, ctx)

    def translate_wait_level_comparison(self, node: ast.Compare,
                                        ctx: Context) -> StmtsAndExpr:
        """Translate comparison with ``WaitLevel``."""
        return self._wait_level_translator.translate_wait_level_comparison(
            node, ctx)

    def create_level_call(self, expr: sil.RefExpression) -> sil.PermExpression:
        return self._wait_level_translator.create_level_call(expr)

    def create_level_below(
            self, expr: sil.PermExpression,
            residue_level_var: sil.PermExpression,
            ctx: Context) -> sil.BoolExpression:
        return self._wait_level_translator.create_level_below(
            expr, residue_level_var, ctx)

    def initialize_current_wait_level(
            self, current_wait_level: sil.PermExpression,
            residue_level_var: sil.PermExpression,
            ctx: Context) -> sil.BoolExpression:
        return self._wait_level_translator.initialize_current_wait_level(
            current_wait_level, residue_level_var, ctx)

    def _translate_must_terminate(
            self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """Translate a call to ``MustTerminate``."""
        if ctx.obligation_context.is_translating_loop():
            return self._loop_translator.translate_must_terminate(node, ctx)
        elif ctx.obligation_context.is_translating_posts:
            raise InvalidProgramException(
                node, 'obligation.must_terminate.in_postcondition')
        else:
            return self._method_translator.translate_must_terminate(node, ctx)

    def _translate_must_release(
            self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """Translate a call to ``MustRelease``."""
        if ctx.obligation_context.is_translating_loop():
            return self._loop_translator.translate_must_release(node, ctx)
        else:
            return self._method_translator.translate_must_release(node, ctx)

    def get_obligation_preamble(
            self,
            ctx: Context) -> Tuple[List[Predicate], List[Field]]:
        """Construct obligation preamble.

        To track each obligation we use predicates which are defined in
        this preamble.
        """
        predicates = self._obligation_manager.create_predicates(self)
        fields = self._obligation_manager.create_fields(self)
        return predicates, fields

    def create_method_node(     # pylint: disable=too-many-arguments
            self, ctx: Context, name: str,
            args: List[VarDecl], returns: List[VarDecl],
            pres: List[Expr], posts: List[Expr],
            local_vars: List[VarDecl], body: List[Stmt],
            position: Position, info: Info,
            method: PythonMethod = None,
            overriding_check: bool = False) -> Method:
        """Construct method AST node with additional obligation stuff."""
        return self._method_translator.create_method_node(
            ctx, name, args, returns, pres, posts, local_vars, body,
            position, info, method, overriding_check)

    def create_method_call_node(
            self, ctx: Context, method_name: str, args: List[Expr],
            targets: List[Expr], position: Position, info: Info,
            target_method: PythonMethod = None,
            target_node: ast.Call = None) -> List[Stmt]:
        """Construct a method call AST node with obligation stuff."""
        return self._method_translator.create_method_call_node(
            ctx, method_name, args, targets, position, info,
            target_method, target_node)

    def create_method_fork(self, ctx: Context, targets, thread: Expr,
                           position: Position, info: Info,
                           target_node: ast.Call = None) -> List[Stmt]:
        return self._method_translator.create_method_fork(
            ctx, targets, thread, position, info, target_node)

    def create_obligation_info(self, method: PythonMethod) -> object:
        """Create obligation info for the method."""
        info = PythonMethodObligationInfo(
            self._obligation_manager, method, self)
        info.traverse_contract()
        return info
