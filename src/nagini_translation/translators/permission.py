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
        def translate_node(node):
            if isinstance(node, ast.Num):
                stmt, nodeprime = self.translate_expr(node, ctx, self.viper.Int)
                if stmt:
                    raise InvalidProgramException(node, 'purity.violated')
                return nodeprime, True
            else:
                perm = self.translate_perm(node, ctx)
                return perm, perm.typ() == self.viper.Int

        if isinstance(node.op, ast.Div):
            left, left_int = translate_node(node.left)
            right, right_int = translate_node(node.right)

            if left_int and right_int:
                return self.viper.FractionalPerm(left, right,
                                                 self.to_position(node, ctx),
                                                 self.no_info(ctx))

            return self.viper.PermDiv(left, right,
                                      self.to_position(node, ctx),
                                      self.no_info(ctx))

        if isinstance(node.op, ast.Mult):
            left, left_int = translate_node(node.left)
            right, right_int = translate_node(node.right)

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

        call_stmt, call = self.translate_expr(node, ctx, self.viper.Int)
        if not call_stmt:
            return call
        raise InvalidProgramException(node, 'purity.violated')

    def translate_perm_Attribute(self, node: ast.Attribute, ctx: Context) -> Expr:
        stmt, expr = self.translate_expr(node, ctx, self.viper.Int)
        if not stmt:
            return expr
        raise InvalidProgramException(node, 'purity.violated')
