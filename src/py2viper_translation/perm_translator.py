import ast

from py2viper_translation.abstract_translator import (
    CommonTranslator,
    Context,
    Expr,
)
from py2viper_translation.util import (
    InvalidProgramException,
    UnsupportedException,
)


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
            left_stmt, left = self.translate_expr(node.left, ctx)
            right_stmt, right = self.translate_expr(node.right, ctx)
            if left_stmt or right_stmt:
                raise InvalidProgramException(node, 'purity.violated')
            return self.viper.FractionalPerm(left, right,
                                             self.to_position(node, ctx),
                                             self.no_info(ctx))
        raise UnsupportedException(node)