"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import ast

from nagini_translation.lib.program_nodes import PythonMethod
from nagini_translation.lib.typedefs import (
    Expr,
    Stmt,
    StmtsAndExpr,
)
from nagini_translation.lib.util import (
    InvalidProgramException,
    UnsupportedException,
    get_func_name
)
from nagini_translation.translators.abstract import Context
from nagini_translation.translators.common import CommonTranslator


class PermTranslator(CommonTranslator):

    def translate_perm(self, node: ast.AST, ctx: Context) -> Expr:
        """
        Generic visitor function for translating a permission amount
        """
        method = 'translate_perm_' + node.__class__.__name__
        visitor = getattr(self, method, self.translate_generic)
        return visitor(node, ctx)

    def translate_perm_Constant(self, node: 'ast.Constant', ctx: Context) -> Expr:
        return self.translate_perm_Num(node, ctx)

    def translate_perm_Num(self, node: ast.Num, ctx: Context) -> Expr:
        if node.n == 1:
            return self.viper.FullPerm(self.to_position(node, ctx),
                                       self.no_info(ctx))
        raise UnsupportedException(node)

    def translate_perm_or_int(self, node: ast.AST, ctx: Context):
        num_class = ast.Num
        import sys
        if sys.version_info[1] >= 8:
            num_class = ast.Constant
        if isinstance(node, num_class):
            stmt, int_val = self.translate_expr(node, ctx, self.viper.Int)
            if stmt:
                raise InvalidProgramException(node, 'purity.violated')
            return int_val, True
        else:
            int_or_perm_val = self.translate_perm(node, ctx)
            return int_or_perm_val, int_or_perm_val.typ() == self.viper.Int

    def translate_perm_BinOp(self, node: ast.BinOp, ctx: Context) -> Expr:

        if isinstance(node.op, ast.Div):
            left, left_int = self.translate_perm_or_int(node.left, ctx)
            right_stmt, right = self.translate_expr(node.right, ctx,
                                                    target_type=self.viper.Int)
            if right_stmt:
                raise InvalidProgramException(node, 'purity.violated')

            if left_int:
                return self.viper.FractionalPerm(left, right,
                                                 self.to_position(node, ctx),
                                                 self.no_info(ctx))
            return self.viper.PermDiv(left, right,
                                      self.to_position(node, ctx),
                                      self.no_info(ctx))

        if isinstance(node.op, ast.Mult):
            left, left_int = self.translate_perm_or_int(node.left, ctx)
            right, right_int = self.translate_perm_or_int(node.right, ctx)

            if left_int != right_int and right_int:
                left, left_int, right, right_int = right, right_int, left, left_int

            if left_int and right_int:
                return self.viper.Mul(left, right,
                                      self.to_position(node, ctx),
                                      self.no_info(ctx))
            if left_int or right_int:
                return self.viper.IntPermMul(left, right,
                                             self.to_position(node, ctx),
                                             self.no_info(ctx))

            return self.viper.PermMul(left, right,
                                      self.to_position(node, ctx),
                                      self.no_info(ctx))

        new_node = None
        if isinstance(node.op, ast.Add):
            new_node = self.viper.PermAdd
        elif isinstance(node.op, ast.Sub):
            new_node = self.viper.PermSub

        if new_node:
            left = self.translate_perm(node.left, ctx)
            right = self.translate_perm(node.right, ctx)
            return new_node(left, right,
                            self.to_position(node, ctx),
                            self.no_info(ctx))
        raise UnsupportedException(node)

    def translate_perm_Call(self, node: ast.Call, ctx: Context) -> Expr:
        func_name = get_func_name(node)
        if func_name == 'ARP':
            if not ctx.arp:
                raise UnsupportedException(node, 'ARP not supported. Use --arp flag.')
            if len(node.args) == 0:
                return self.get_arp_for_context(node, ctx)
            elif len(node.args) == 1:
                arg0_stmt, arg0 = self.translate_expr(node.args[0], ctx, self.viper.Int)
                if arg0_stmt:
                    raise InvalidProgramException(node, 'purity.violated')
                formal_arg = self.viper.LocalVarDecl('count', self.viper.Int,
                                                     self.to_position(node, ctx),
                                                     self.no_info(ctx))
                return self.viper.FuncApp('rdc', [arg0], self.to_position(node, ctx),
                                          self.no_info(ctx), self.viper.Perm,
                                          [formal_arg])
        elif func_name == 'getARP':
            if not ctx.arp:
                raise UnsupportedException(node, 'ARP not supported. Use --arp flag.')
            if len(node.args) == 1:
                formal_arg = self.viper.LocalVarDecl(
                    'tk', self.viper.Ref, self.to_position(node, ctx), self.no_info(ctx))
                arg0_stmt, arg0 = self.translate_expr(node.args[0], ctx, self.viper.Ref)
                if arg0_stmt:
                    raise InvalidProgramException(node, 'purity.violated')
                return self.viper.FuncApp('rd_token', [arg0], self.to_position(node, ctx),
                                          self.no_info(ctx), self.viper.Perm,
                                          [formal_arg])

        call_stmt, call = self.translate_expr(node, ctx, self.viper.Int)
        if not call_stmt:
            return call
        raise InvalidProgramException(node, 'purity.violated')

    def translate_perm_Name(self, node: ast.Name, ctx: Context) -> Expr:
        if node.id == 'RD_PRED':
            if not ctx.arp:
                raise UnsupportedException(node, 'ARP not supported. Use --arp flag.')
            return self.viper.FuncApp('globalRd', [], self.to_position(node, ctx),
                                      self.no_info(ctx), self.viper.Perm, {})
        stmt, res = self.translate_expr(node, ctx)
        if stmt:
            raise InvalidProgramException(node, 'purity.violated')
        return  res

    def translate_perm_Attribute(self, node: ast.Attribute, ctx: Context) -> Expr:
        stmt, expr = self.translate_expr(node, ctx, self.viper.Int)
        if not stmt:
            return expr
        raise InvalidProgramException(node, 'purity.violated')

    def get_arp_for_context(self, node: ast.AST, ctx: Context):
        if (ctx.actual_function and isinstance(ctx.actual_function, PythonMethod) and
                ctx.actual_function.pure):
            return self.viper.WildcardPerm(self.to_position(node, ctx), self.no_info(ctx))
        else:
            if not ctx.arp:
                raise UnsupportedException(node, 'ARP not supported. Use --arp flag.')
            if ctx.current_thread_object is not None:
                formal_arg = self.viper.LocalVarDecl('tk', self.viper.Ref,
                                                     self.to_position(node, ctx),
                                                     self.no_info(ctx))
                if ctx.is_thread_start:
                    return self.viper.FuncApp('rd_token_fresh',
                                              [ctx.current_thread_object],
                                              self.to_position(node, ctx),
                                              self.no_info(ctx), self.viper.Perm,
                                              [formal_arg])
                else:
                    return self.viper.FuncApp('rd_token', [ctx.current_thread_object],
                                              self.to_position(node, ctx),
                                              self.no_info(ctx), self.viper.Perm,
                                              [formal_arg])
            else:
                return self.viper.FuncApp('rd', [], self.to_position(node, ctx),
                                          self.no_info(ctx), self.viper.Perm, {})
