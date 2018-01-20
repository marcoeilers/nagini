import ast

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

    def translate_perm_Num(self, node: ast.Num, ctx: Context) -> Expr:
        if node.n == 1:
            return self.viper.FullPerm(self.to_position(node, ctx),
                                       self.no_info(ctx))
        raise UnsupportedException(node)

    def translate_perm_BinOp(self, node: ast.BinOp, ctx: Context) -> Expr:
        if isinstance(node.op, ast.Div):
            left_stmt, left = self.translate_expr(node.left, ctx,
                                                  self.viper.Int)
            right_stmt, right = self.translate_expr(node.right, ctx,
                                                    self.viper.Int)
            if left_stmt or right_stmt:
                raise InvalidProgramException(node, 'purity.violated')
            return self.viper.FractionalPerm(left, right,
                                             self.to_position(node, ctx),
                                             self.no_info(ctx))

        if isinstance(node.op, ast.Mult):
            func, other = None, None
            if isinstance(node.left, ast.Call):
                func, other = node.left, node.right
            elif isinstance(node.right, ast.Call):
                func, other = node.right, node.left
            left_stmt, left = self.translate_expr(other, ctx, self.viper.Int)
            right = self.translate_perm(func, ctx)
            if left_stmt:
                raise InvalidProgramException(node, 'purity.violated')
            return self.viper.IntPermMul(left, right,
                                         self.to_position(node, ctx),
                                         self.no_info(ctx))

        newnode = None
        if isinstance(node.op, ast.Add):
            newnode = self.viper.PermAdd
        elif isinstance(node.op, ast.Sub):
            newnode = self.viper.PermSub

        if newnode:
            left = self.translate_perm(node.left, ctx)
            right = self.translate_perm(node.right, ctx)
            return newnode(left, right,
                           self.to_position(node, ctx),
                           self.no_info(ctx))
        raise UnsupportedException(node)

    def translate_perm_Call(self, node: ast.Call, ctx: Context) -> Expr:
        func_name = get_func_name(node)
        if func_name == 'ARP':
            if len(node.args) == 0:
                return self.viper.FuncApp('rd', [], self.to_position(node, ctx),
                                          self.no_info(ctx), self.viper.Ref, {})
            elif len(node.args) == 1:
                arg0_stmt, arg0 = self.translate_expr(node.args[0], ctx, self.viper.Int)
                if arg0_stmt:
                    raise InvalidProgramException(node, 'purity.violated')
                # arg = self.viper.IntLit(node.args[0].n, self.to_position(node, ctx), self.no_info(ctx))
                formal_arg = self.viper.LocalVarDecl('count', self.viper.Int, self.to_position(node, ctx), self.no_info(ctx))
                return self.viper.FuncApp('rdc', [arg0], self.to_position(node, ctx),
                                          self.no_info(ctx), self.viper.Perm, [formal_arg])
        raise UnsupportedException(node)
