import ast

from py2viper_translation.abstract_translator import CommonTranslator, TranslatorConfig, Expr, StmtAndExpr, Stmt
from py2viper_translation.analyzer import PythonClass, PythonMethod, PythonVar, PythonTryBlock
from typing import List, Tuple, Optional, Union, Dict, Any

class PermTranslator(CommonTranslator):

    def translate_perm(self, node: ast.AST, ctx) -> Expr:
        """
        Generic visitor function for translating a permission amount
        """
        method = 'translate_perm_' + node.__class__.__name__
        visitor = getattr(self, method, self.translate_generic)
        return visitor(node, ctx)

    def translate_perm_Num(self, node: ast.Num, ctx) -> Expr:
        if node.n == 1:
            return self.viper.FullPerm(self.to_position(node, ctx),
                                       self.noinfo(ctx))
        raise UnsupportedException(node)

    def translate_perm_BinOp(self, node: ast.BinOp, ctx) -> Expr:
        if isinstance(node.op, ast.Div):
            left_stmt, left = self.translate_expr(node.left, ctx)
            right_stmt, right = self.translate_expr(node.right, ctx)
            if left_stmt or right_stmt:
                raise InvalidProgramException(node, 'purity.violated')
            return self.viper.FractionalPerm(left, right,
                                             self.to_position(node, ctx),
                                             self.noinfo(ctx))
        raise UnsupportedException(node)