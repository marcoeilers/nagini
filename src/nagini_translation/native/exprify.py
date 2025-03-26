import ast
from typing import Tuple, Union, List


class Exprifier:
    def __init__(self):
        pass

    def exprify_generic(self, node: ast.stmt, expr: ast.expr) -> ast.expr:
        thedict = {
            ast.If: self.exprifyIf,
            ast.Assign: self.exprifyAssign,
            ast.Return: self.exprifyReturn
        }
        return thedict[type(node)](node, expr)

    def exprifyBody(self, body: List[ast.stmt], expr: ast.expr) -> ast.expr:
        for s in reversed(body):
            expr = self.exprify_generic(s, expr)
        return expr

    def exprifyIf(self, node: ast.If, expr: ast.expr) -> ast.expr:
        return ast.IfExp(
            test=node.test,
            body=self.exprifyBody(node.body, expr),
            orelse=self.exprifyBody(node.orelse, expr))
            

    def exprifyAssign(self, node: ast.Assign, expr: ast.expr) -> ast.expr:
        for t in node.targets:
            class TransformName(ast.NodeTransformer):
                def visit_Name(self, vnode):
                    if vnode.id == t.id:
                        return node.value
                    else:
                        return vnode
            expr = TransformName().visit(expr)
        return expr

    def exprifyReturn(self, node: ast.Return, expr: ast.expr) -> ast.expr:
        return node.value
