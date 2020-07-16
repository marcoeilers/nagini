"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import ast

from abc import ABCMeta
from nagini_translation.lib import silver_nodes as sil
from nagini_translation.lib.context import Context
from nagini_translation.lib.program_nodes import (
    PythonClass,
    PythonExceptionHandler,
    PythonGlobalVar,
    PythonIOOperation,
    PythonMethod,
    PythonModule,
    PythonTryBlock,
    PythonType,
    PythonVar,
)
from nagini_translation.lib.jvmaccess import JVM
from nagini_translation.lib.typedefs import (
    Expr,
    Info,
    Field,
    VarDecl,
    Predicate,
    Position,
    Stmt,
    StmtsAndExpr,
)
from nagini_translation.lib.typeinfo import TypeInfo
from nagini_translation.lib.util import (
    get_surrounding_try_blocks,
    InvalidProgramException,
    UnsupportedException
)
from nagini_translation.lib.viper_ast import ViperAST
from typing import List, Tuple, Union


class TranslatorConfig:
    """
    Contains the configuration of the translator, i.e. all the parts
    (specialized translates) it consists of.
    """

    def __init__(self, translator: 'Translator'):
        self.expr_translator = None
        self.stmt_translator = None
        self.call_translator = None
        self.contract_translator = None
        self.perm_translator = None
        self.pure_translator = None
        self.type_translator = None
        self.pred_translator = None
        self.io_operation_translator = None
        self.obligation_translator = None
        self.prog_translator = None
        self.method_translator = None
        self.type_factory = None
        self.translator = translator


class AbstractTranslator(metaclass=ABCMeta):
    """
    Abstract class which all specialized translators extend. Provides a number
    of interface methods through which specialized translators can interact, and
    forwards calls to those methods to the respective translators.
    """

    def __init__(self, config: TranslatorConfig, jvm: JVM, source_file: str,
                 type_info: TypeInfo, viper_ast: ViperAST) -> None:
        self.config = config
        self.viper = viper_ast
        self.jvm = jvm

    @property
    def type_factory(self):
        return self.config.type_factory

    @property
    def translator(self):
        return self.config.translator

    def translate_expr(self, node: ast.AST, ctx: Context,
                       target_type: object = None,
                       impure: bool = False,
                       as_read: bool = False) -> StmtsAndExpr:
        return self.config.expr_translator.translate_expr(
            node, ctx, target_type, impure, as_read)

    def translate_stmt(self, node: ast.AST, ctx: Context) -> List[Stmt]:
        return self.config.stmt_translator.translate_stmt(node, ctx)

    def translate_contract(self, node: ast.AST, ctx: Context) -> Expr:
        return self.config.contract_translator.translate_contract(node, ctx)

    def translate_perm(self, node: ast.AST, ctx: Context) -> Expr:
        return self.config.perm_translator.translate_perm(node, ctx)

    def get_arp_for_context(self, node: ast.AST, ctx: Context) -> Expr:
        return self.config.perm_translator.get_arp_for_context(node, ctx)

    def translate_exprs(self, nodes: List[ast.AST],
                        function: PythonMethod, ctx: Context) -> Expr:
        return self.config.pure_translator.translate_exprs(nodes, function, ctx)

    def get_type(self, node: ast.AST, ctx: Context) -> PythonClass:
        return self.config.type_translator.get_type(node, ctx)

    def translate_type(self, cls: PythonClass,
                       ctx: Context) -> 'silver.ast.Type':
        return self.config.type_translator.translate_type(cls, ctx)

    def translate_Call(self, node: ast.Call, ctx: Context, impure=False,
                       statement=False) -> StmtsAndExpr:
        return self.config.call_translator.translate_Call(node, ctx, impure, statement)

    def translate_constructor_call(self, target_class: PythonClass,
                                   node: ast.Call, args: List, arg_stmts: List,
                                   ctx: Context) -> StmtsAndExpr:
        return self.config.call_translator.translate_constructor_call(
            target_class, node, args, arg_stmts, ctx)

    def translate_predicate(self, pred: PythonMethod,
                            ctx: Context) -> 'ast.silver.Predicate':
        return self.config.pred_translator.translate_predicate(pred, ctx)

    def translate_static_field_access(self, field: PythonGlobalVar,
                                      receiver: Union[Expr, PythonType],
                                      node, ctx: Context) -> Expr:
        return self.config.expr_translator.translate_static_field_access(field, receiver,
                                                                         node, ctx)

    def translate_global_var_reference(self, target: PythonGlobalVar, node: ast.AST,
                                       ctx: Context) -> Expr:
        return self.config.expr_translator.translate_global_var_reference(target, node,
                                                                          ctx)

    def translate_io_operation(
            self,
            operation: PythonIOOperation,
            ctx: Context,
            ) -> Tuple[
                'ast.silver.Predicate',
                List['ast.silver.Function'],
                List['ast.silver.Method'],
                ]:
        return self.config.io_operation_translator.translate_io_operation(
            operation,
            ctx)

    def translate_method(self, method: PythonMethod,
                         ctx: Context) -> 'silver.ast.Method':
        return self.config.method_translator.translate_method(method, ctx)

    def translate_main_method(self, modules: List[PythonModule],
                              ctx: Context) -> 'silver.ast.Method':
        return self.config.method_translator.translate_main_method(modules, ctx)

    def translate_function(self, func: PythonMethod,
                           ctx: Context) -> 'silver.ast.Function':
        return self.config.method_translator.translate_function(func, ctx)

    def translate_predicate_family(self, root: PythonMethod,
            preds: List[PythonMethod], ctx: Context) -> 'ast.silver.Predicate':
        return self.config.pred_translator.translate_predicate_family(root,
                                                                      preds,
                                                                      ctx)

    def translate_operator(self, left: Expr, right: Expr, left_type: PythonType,
                           right_type: PythonType, node: ast.AST,
                           ctx: Context) -> StmtsAndExpr:
        return self.config.expr_translator.translate_operator(
            left, right, left_type, right_type, node, ctx)

    def create_exception_catchers(self, var: PythonVar,
                                  try_blocks: List[PythonTryBlock],
                                  call: ast.Call, ctx: Context) -> List[Stmt]:
        return self.config.expr_translator.create_exception_catchers(var,
                                                                     try_blocks,
                                                                     call, ctx)

    def extract_contract(self, method: PythonMethod, errorvarname: str,
                         is_constructor: bool,
                         ctx: Context) -> Tuple[List[Expr], List[Expr]]:
        return self.config.method_translator.extract_contract(method,
                                                              errorvarname,
                                                              is_constructor,
                                                              ctx)

    def inline_method(self, method: PythonMethod, args: List[PythonVar],
                      result_var: PythonVar, error_var: PythonVar,
                      ctx: Context) -> List[Stmt]:
        return self.config.call_translator.inline_method(method, args,
                                                         result_var, error_var,
                                                         ctx)

    def translate_contractfunc_call(self, node: ast.Call, ctx: Context,
                                    impure=False, statement=False) -> StmtsAndExpr:
        return self.config.contract_translator.translate_contractfunc_call(node, ctx,
                                                                           impure,
                                                                           statement)

    def translate_normal_call(self, target: PythonMethod, arg_stmts: List[Stmt],
                              args: List[Expr], arg_types: List[PythonType],
                              node: ast.AST, ctx: Context, impure=False) -> StmtsAndExpr:
        return self.config.call_translator.translate_normal_call(target, arg_stmts, args,
                                                                 arg_types, node, ctx,
                                                                 impure)

    def translate_normal_call_node(self, node: ast.Call, ctx: Context,
                                   impure=False) -> StmtsAndExpr:
        return self.config.call_translator.translate_normal_call_node(node, ctx, impure)

    def translate_io_contractfunc_call(self, node: ast.Call,
                                       ctx: Context, impure: bool, statement: bool) -> StmtsAndExpr:
        translator = self.config.io_operation_translator
        return translator.translate_io_contractfunc_call(node, ctx, impure, statement)

    def translate_io_operation_call(self, node: ast.Call,
                                    ctx: Context) -> StmtsAndExpr:
        translator = self.config.io_operation_translator
        return translator.translate_io_operation_call(node, ctx)

    def is_io_existential_defining_equality(self, node: ast.Expr,
                                            ctx: Context) -> bool:
        translator = self.config.io_operation_translator
        return translator.is_io_existential_defining_equality(node, ctx)

    def define_io_existential(self, node: ast.Expr, ctx: Context) -> None:
        translator = self.config.io_operation_translator
        translator.define_io_existential(node, ctx)

    def translate_get_ghost_output(self, node: ast.Expr,
                                   ctx: Context) -> List[Stmt]:
        translator = self.config.io_operation_translator
        return translator.translate_get_ghost_output(node, ctx)

    def translate_obligation_contractfunc_call(self, node: ast.Call,
                                               ctx: Context, impure: bool = False) -> StmtsAndExpr:
        translator = self.config.obligation_translator
        return translator.translate_obligation_contractfunc_call(node, ctx, impure)

    def translate_must_invoke_token(self, node: ast.Call,
                                    ctx: Context) -> StmtsAndExpr:
        translator = self.config.obligation_translator
        return translator.translate_must_invoke_token(node, ctx)

    def translate_must_invoke_ctoken(self, node: ast.Call,
                                     ctx: Context) -> StmtsAndExpr:
        translator = self.config.obligation_translator
        return translator.translate_must_invoke_ctoken(node, ctx)

    def get_obligation_preamble(
            self,
            ctx: Context) -> Tuple[List[Predicate], List[Field]]:
        translator = self.config.obligation_translator
        return translator.get_obligation_preamble(ctx)

    def is_wait_level_comparison(self, node: ast.Compare,
                                 ctx: Context) -> bool:
        translator = self.config.obligation_translator
        return translator.is_wait_level_comparison(node, ctx)

    def translate_wait_level_comparison(self, node: ast.Compare,
                                        ctx: Context) -> StmtsAndExpr:
        translator = self.config.obligation_translator
        return translator.translate_wait_level_comparison(node, ctx)

    def create_level_call(self, expr: sil.RefExpression) -> sil.PermExpression:
        translator = self.config.obligation_translator
        return translator.create_level_call(expr)

    def create_level_below(
            self, expr: sil.PermExpression,
            residue_level_var: sil.PermExpression,
            ctx: Context) -> sil.BoolExpression:
        translator = self.config.obligation_translator
        return translator.create_level_below(expr, residue_level_var, ctx)

    def initialize_current_wait_level(
            self, current_wait_level: sil.PermExpression,
            residue_level_var: sil.PermExpression,
            ctx: Context) -> sil.BoolExpression:
        translator = self.config.obligation_translator
        return translator.initialize_current_wait_level(
            current_wait_level, residue_level_var, ctx)

    def create_method_node(
            self, ctx: Context, name: str,
            args: List[VarDecl], returns: List[VarDecl],
            pres: List[Expr], posts: List[Expr],
            locals: List[VarDecl], body: List[Stmt],
            position: Position, info: Info,
            method: PythonMethod = None,
            overriding_check: bool = False) -> List[Stmt]:
        translator = self.config.obligation_translator
        return translator.create_method_node(
            ctx, name, args, returns, pres, posts, locals, body,
            position, info, method, overriding_check)

    def create_method_call_node(
            self, ctx: Context, methodname: str, args: List[Expr],
            targets: List[Expr], position: Position, info: Info,
            target_method: PythonMethod = None,
            target_node: ast.Call = None) -> List[Stmt]:
        if target_method is not None:
            if target_method.cls and target_method.cls.interface:
                self.viper.mark_class_used(target_method.cls.sil_name)
        translator = self.config.obligation_translator
        return translator.create_method_call_node(
            ctx, methodname, args, targets, position, info, target_method,
            target_node)

    def create_method_fork(self, ctx: Context, targets, thread: Expr,
                           position: Position, info: Info,
                           target_node: ast.Call = None) -> List[Stmt]:
        translator = self.config.obligation_translator
        return translator.create_method_fork(ctx, targets, thread, position, info,
                                             target_node)

    def enter_loop_translation(
            self, node: Union[ast.While, ast.For], ctx: Context,
            err_var: PythonVar = None) -> None:
        translator = self.config.obligation_translator
        return translator.enter_loop_translation(node, ctx, err_var)

    def leave_loop_translation(self, ctx: Context) -> None:
        translator = self.config.obligation_translator
        return translator.leave_loop_translation(ctx)

    def create_while_node(
            self, ctx: Context, cond: Expr,
            invariants: List[Expr],
            locals: List[VarDecl],
            body: Stmt, node: Union[ast.While, ast.For]) -> List[Stmt]:
        translator = self.config.obligation_translator
        return translator.create_while_node(
            ctx, cond, invariants, locals, body, node)

    def translate_handler(self, handler: PythonExceptionHandler,
                          ctx: Context) -> List[Stmt]:
        return self.config.method_translator.translate_handler(handler, ctx)

    def translate_finally(self, block: PythonTryBlock,
                          ctx: Context) -> List[Stmt]:
        return self.config.method_translator.translate_finally(block, ctx)

    def type_check(self, lhs: Expr, type: PythonType,
                   position: 'silver.ast.Position', ctx: Context,
                   inhale_exhale: bool=True) -> Expr:
        return self.config.type_translator.type_check(
            lhs, type, position, ctx, inhale_exhale=inhale_exhale)

    def bind_type_vars(self, method: PythonMethod, ctx: Context) -> None:
        return self.config.method_translator.bind_type_vars(method, ctx)

    def create_tuple(self, vals: List[Expr], val_types: List[PythonType],
                     node: ast.AST, ctx: Context) -> Expr:
        return self.config.expr_translator.create_tuple(vals, val_types, node,
                                                        ctx)

    def translate_string(self, s: str, node: ast.AST, ctx: Context) -> Expr:
        return self.config.expr_translator.translate_string(s, node, ctx)

    def translate_args(self, target: PythonMethod, arg_nodes: List,
                       keywords: List, node: ast.AST, ctx: Context,
                       implicit_receiver=None) -> Tuple[List[Stmt], List[Expr],
                                                        List[PythonType]]:
        return self.config.call_translator.translate_args(target, arg_nodes,
                                                          keywords, node, ctx,
                                                          implicit_receiver)

