"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import ast
from typing import List

from nagini_translation.lib.constants import ARBITRARY_BOOL_FUNC
from nagini_translation.lib.errors import rules
from nagini_translation.lib.program_nodes import PythonClass, PythonTryBlock, PythonVar
from nagini_translation.lib.typedefs import Expr, Position, Seqn, Stmt, Var, VarDecl
from nagini_translation.lib.util import flatten, get_body_indices, get_surrounding_try_blocks
from nagini_translation.translators.abstract import Context
from nagini_translation.translators.statement import StatementTranslator


class SIFStatementTranslator(StatementTranslator):
    """
    Extended AST Version of the StatementTranslator
    """

    def get_error_var(self, stmt: ast.AST, ctx: Context) -> PythonVar:
        return ctx.current_function.error_var

    def _translate_return(self, node: ast.Return, ctx: Context) -> List[Stmt]:
        if node.value:
            rhs_stmt, rhs = self.translate_expr(node.value, ctx)
        else:
            rhs_stmt, rhs = [], self.viper.NullLit(self.no_position(ctx),
                                                   self.no_info(ctx))
        pos = self.to_position(node, ctx)
        info = self.no_info(ctx)
        if ctx.result_var:
            rvar = ctx.result_var.ref(node, ctx)
        else:
            rvar = None
        ret_stmt = self.viper.Return(rhs, rvar, pos, info)
        return rhs_stmt + [ret_stmt]

    def translate_stmt_Return(self, node: ast.Return, ctx: Context) -> List[Stmt]:
        return self._translate_return(node, ctx)

    def translate_stmt_Break(self, node: ast.Break, ctx: Context) -> List[Stmt]:
        return [self.viper.Break(self.to_position(node, ctx), self.no_info(ctx))]

    def translate_stmt_Continue(self, node: ast.Continue, ctx: Context) -> List[Stmt]:
        return [self.viper.Continue(self.to_position(node, ctx), self.no_info(ctx))]

    def _while_postamble(self, node: ast.While, post_label: str,
                         ctx: Context) -> List[Stmt]:
        return self._set_result_none(ctx)

    def _translate_while_body(self, node: ast.While, ctx: Context,
                              end_label: str) -> List[Stmt]:
        start, end = get_body_indices(node.body)
        body = flatten(
            [self.translate_stmt(stmt, ctx) for stmt in node.body[start:end]])
        return body

    def _create_try_handlers(self, node: ast.Try, try_block: PythonTryBlock,
                             ctx: Context) -> List['silver.sif.SIFExceptionHandler']:
        no_pos = self.no_position(ctx)
        no_info = self.no_info(ctx)
        catch_blocks = []
        error_var = self.get_error_var(node, ctx)
        for handler in try_block.handlers:
            error_type_check = self.type_check(
                error_var.ref(), handler.exception, self.to_position(handler.node, ctx),
                ctx, inhale_exhale=False)
            handler_body = []
            if handler.exception_name:
                ctx.var_aliases[handler.exception_name] = error_var

                error_var.type = handler.exception
                handler_body.append(self.set_var_defined(error_var, no_pos, no_info))
            handler_body += flatten([self.translate_stmt(stmt, ctx)
                                     for stmt in handler.body])
            handler_body_seqn = self.viper.Seqn(handler_body, no_pos, no_info)
            catch_blocks.append(self.viper.SIFExceptionHandler(
                error_var.ref(), error_type_check, handler_body_seqn))
            if handler.exception_name:
                del ctx.var_aliases[handler.exception_name]
        return catch_blocks

    def translate_stmt_Try(self, node: ast.Try, ctx: Context) -> List[Stmt]:
        no_pos = self.no_position(ctx)
        no_info = self.no_info(ctx)
        try_block = self._get_try_block(node, ctx)
        assert try_block
        body = flatten([self.translate_stmt(stmt, ctx) for stmt in node.body])
        if try_block.else_block:
            else_block = flatten([self.translate_stmt(stmt, ctx)
                                  for stmt in try_block.else_block.body])
            else_block = self.viper.Seqn(else_block, no_pos, no_info)
        else:
            else_block = None
        if try_block.finally_block:
            finally_block = flatten([self.translate_stmt(stmt, ctx)
                                     for stmt in try_block.finally_block])
            finally_block = self.viper.Seqn(finally_block, no_pos, no_info)
        else:
            finally_block = None
        catch_blocks = self._create_try_handlers(node, try_block, ctx)
        return [self.viper.Try(self.viper.Seqn(body, no_pos, no_info),
                               catch_blocks, else_block, finally_block,
                               self.to_position(node, ctx), no_info)]

    def translate_stmt_Raise(self, node: ast.Raise, ctx: Context) -> List[Stmt]:
        err_var = self.get_error_var(node, ctx).ref()
        stmts = self._translate_stmt_raise_create(node, err_var, ctx)
        ex_type_low = []
        if ctx.sif == 'prob':
            position = self.to_position(node.exc, ctx, rules=rules.EXCEPTION_TYPE_LOW)
            info = self.no_info(ctx)
            exc_expr = stmts[-1].rhs()
            exc_type = self.type_factory.typeof(exc_expr, ctx)

            ex_type_low.append(self.viper.Assert(self.viper.Low(exc_type, None, position, info), position, info))
        return stmts[:-1] + ex_type_low + [
            self.viper.Raise(stmts[-1], self.to_position(node, ctx), self.no_info(ctx))
            ]

    def _translate_With_body(self,
                             try_block: PythonTryBlock,
                             enter_res: PythonVar,
                             ctx: Context) -> List[Stmt]:
        no_pos = self.no_position(ctx)
        no_info = self.no_info(ctx)
        if try_block.with_item.optional_vars:
            as_expr = try_block.with_item.optional_vars
            as_var = ctx.current_function.get_variable(as_expr.id)
            enter_assign = self.viper.LocalVarAssign(as_var.ref(as_expr, ctx),
                                                     enter_res.ref(),
                                                     self.to_position(as_expr,
                                                                      ctx),
                                                     no_info)
            define_var = self.set_var_defined(as_var, no_pos, no_info)
            body = [enter_assign, define_var]
        else:
            body = []
        body += flatten([self.translate_stmt(stmt, ctx) for stmt in try_block.node.body])
        return body

    def _create_With_ecx_var(self, ctx: Context) -> (VarDecl, Var):
        no_pos = self.no_position(ctx)
        no_info = self.no_info(ctx)
        no_exc_name = ctx.current_function.get_fresh_name('exc')
        no_exc_decl = self.viper.LocalVarDecl(no_exc_name, self.viper.Bool, no_pos,
                                              no_info)
        no_exc = self.viper.LocalVar(no_exc_name, self.viper.Bool, no_pos, no_info)
        return no_exc_decl, no_exc

    def _create_With_exception_handler_type_check(self, try_block: PythonTryBlock,
                                                  ctx: Context) -> Expr:
        exception_class = ctx.module.global_module.classes['Exception']
        error_var = self.get_error_var(try_block.node, ctx).ref()
        return self.type_check(error_var, exception_class,
                               self.no_position(ctx), ctx, inhale_exhale=False)

    def _create_With_exception_handler(self, try_block: PythonTryBlock,
                                       exit_res: PythonVar, no_exc: 'viper.ast.LocalVar',
                                       ctx: Context) -> Seqn:
        no_pos = self.no_position(ctx)
        no_info = self.no_info(ctx)
        ctx_type = self.get_type(try_block.with_item.context_expr, ctx)
        error_var = self.get_error_var(try_block.node, ctx).ref()
        err_type_arg = self.type_factory.typeof(error_var, ctx)

        tb_class = ctx.module.global_module.classes['traceback']
        traceback_var = ctx.actual_function.create_variable('tb', tb_class,
                                                            self.translator)
        tb_type = self.type_check(traceback_var.ref(), tb_class, no_pos, ctx)
        inhale_types = self.viper.Inhale(tb_type, no_pos, no_info)

        exit_call_err = self.get_method_call(ctx_type, '__exit__',
                                             [try_block.with_var.ref(), err_type_arg,
                                              error_var,
                                              traceback_var.ref()],
                                             [ctx_type, None, None, None],
                                             [exit_res.ref()],
                                             try_block.with_item.context_expr, ctx)

        exit_method_node = ctx_type.get_method('__exit__').node.returns
        exit_result = self.to_bool(exit_res.ref(), ctx, exit_method_node)
        return self.viper.Seqn([
            self.viper.LocalVarAssign(
                no_exc, self.viper.FalseLit(no_pos, no_info), no_pos, no_info),
            inhale_types
            ] + exit_call_err + [
                self.viper.If(self.viper.Not(exit_result, no_pos, no_info),
                              self.viper.Raise(None, no_pos, no_info),
                              self.viper.Skip(), no_pos, no_info),
            ], no_pos, no_info)

    def _translate_With_inner_try(self,
                                  try_block: PythonTryBlock,
                                  enter_res: PythonVar,
                                  exception_handler,
                                  ctx: Context) -> 'viper.silver.sif.SIFTryCatchStmt':
        no_pos = self.no_position(ctx)
        no_info = self.no_info(ctx)
        body = self._translate_With_body(try_block, enter_res, ctx)
        return self.viper.Try(self.viper.Seqn(body, no_pos, no_info),
                              [exception_handler], None, None, no_pos, no_info)

    def translate_With_finally_block(self, try_block: PythonTryBlock, exit_res: PythonVar,
                                     no_exc: Var, ctx: Context):
        no_pos = self.no_position(ctx)
        no_info = self.no_info(ctx)
        null = self.viper.NullLit(no_pos, no_info)
        exit_call_no_err = self.get_method_call(try_block.with_var.type, '__exit__',
                                                [try_block.with_var.ref(),
                                                 self.type_factory.typeof(
                                                     self.viper.NullLit(no_pos, no_info),
                                                     ctx),
                                                 null, null],
                                                [try_block.with_var.type, None, None, None],
                                                [exit_res.ref()],
                                                try_block.with_item.context_expr, ctx)
        return self.viper.If(no_exc,
                             self.viper.Seqn(exit_call_no_err, no_pos, no_info),
                             self.viper.Skip(), no_pos, no_info)

    def translate_stmt_With(self, node: ast.With, ctx: Context) -> List[Stmt]:
        """
        Transform a with statement into extended AST. See translation from PEP 343:

        with EXPR as VAR:
            BLOCK

        is translated to

        mgr = (EXPR)
        exit = type(mgr).__exit__  # Not calling it yet
        value = type(mgr).__enter__(mgr)
        exc = True
        try:
            try:
                VAR = value  # Only if "as VAR" is present
                BLOCK
            except:
                # The exceptional case is handled here
                exc = False
                if not exit(mgr, *sys.exc_info()):
                    raise
                # The exception is swallowed if exit() returns true
        finally:
            # The normal and non-local-goto cases are handled here
            if exc:
                exit(mgr, None, None, None)
        """
        try_block = self._get_try_block(node, ctx)
        assert try_block
        pos = self.to_position(node, ctx)
        no_pos = self.no_position(ctx)
        no_info = self.no_info(ctx)
        # Get context mgr
        ctx_stmt, ctx_mgr = self.translate_expr(try_block.with_item.context_expr, ctx)
        ctx_type = self.get_type(try_block.with_item.context_expr, ctx)
        # Create and assign temp variable
        with_ctx = ctx.current_function.create_variable('with_ctx', ctx_type, self.translator)
        try_block.with_var = with_ctx
        ctx_assign = self.viper.LocalVarAssign(with_ctx.ref(), ctx_mgr, no_pos, no_info)
        # Call __enter__ method
        enter_method_type = ctx_type.get_method('__enter__').type
        enter_res = ctx.current_function.create_variable('enter_res',
                                                         enter_method_type,
                                                         self.translator)
        enter_call = self.get_method_call(ctx_type, '__enter__',
                                          [with_ctx.ref()],
                                          [ctx_type],
                                          [enter_res.ref(node, ctx)], node, ctx)
        # Create ecx variable for checking if we raise an exception (see docstring)
        no_exc_decl, no_exc = self._create_With_ecx_var(ctx)
        exc_assign = self.viper.LocalVarAssign(
            no_exc, self.viper.TrueLit(no_pos, no_info), no_pos, no_info)
        # Create variable to take result of __exit__
        exit_res = ctx.current_function.create_variable(
            'exit_res', ctx_type.get_method('__exit__').type, self.translator)
        # Create inner try block
        handler = self._create_With_exception_handler(try_block, exit_res, no_exc, ctx)
        error_type_check = self._create_With_exception_handler_type_check(try_block, ctx)
        exception_handler = self.viper.SIFExceptionHandler(
            self.get_error_var(node, ctx).ref(), error_type_check, handler)
        inner_try = self._translate_With_inner_try(try_block, enter_res, exception_handler,
                                                   ctx)
        # Create outer try block
        finally_block = self.translate_With_finally_block(try_block, exit_res, no_exc, ctx)
        outer_try = self.viper.Try(self.viper.Seqn([inner_try], no_pos, no_info), [], None,
                                   self.viper.Seqn([finally_block], no_pos, no_info), pos,
                                   no_info)

        return [self.viper.Seqn(ctx_stmt + [ctx_assign] +
                                enter_call + [exc_assign, outer_try],
                                pos, no_info, locals=[no_exc_decl])]
