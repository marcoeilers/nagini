import ast

from py2viper_translation.abstract_translator import CommonTranslator, TranslatorConfig, Expr, StmtAndExpr, Stmt
from py2viper_translation.analyzer import PythonClass, PythonMethod, PythonVar, PythonTryBlock
from py2viper_translation.util import InvalidProgramException, get_func_name, flatten
from typing import List, Tuple, Optional, Union, Dict, Any

class StatementTranslator(CommonTranslator):

    def translate_stmt(self, node: ast.AST, ctx) -> List[Stmt]:
        """
        Generic visitor function for translating statements
        """
        method = 'translate_stmt_' + node.__class__.__name__
        visitor = getattr(self, method, self.translate_generic)
        return visitor(node, ctx)

    def translate_stmt_AugAssign(self,
                                 node: ast.AugAssign, ctx) -> List[Stmt]:
        lhs_stmt, lhs = self.translate_expr(node.target, ctx)
        if lhs_stmt:
            raise InvalidProgramException(node, 'purity.violated')
        rhs_stmt, rhs = self.translate_expr(node.value, ctx)
        if isinstance(node.op, ast.Add):
            newval = self.viper.Add(lhs, rhs,
                                    self.to_position(node, ctx),
                                    self.noinfo(ctx))
        elif isinstance(node.op, ast.Sub):
            newval = self.viper.Sub(lhs, rhs,
                                    self.to_position(node, ctx),
                                    self.noinfo(ctx))
        elif isinstance(node.op, ast.Mult):
            newval = self.viper.Mul(lhs, rhs,
                                    self.to_position(node, ctx),
                                    self.noinfo(ctx))
        else:
            raise UnsupportedException(node)
        position = self.to_position(node, ctx)
        if isinstance(node.target, ast.Name):
            assign = self.viper.LocalVarAssign(lhs, newval, position,
                                               self.noinfo(ctx))
        elif isinstance(node.target, ast.Attribute):
            assign = self.viper.FieldAssign(lhs, newval, position,
                                            self.noinfo(ctx))
        return rhs_stmt + [assign]

    def translate_stmt_Try(self, node: ast.Try, ctx) -> List[Stmt]:
        try_block = None
        for block in ctx.current_function.try_blocks:
            if block.node is node:
                try_block = block
                break
        assert try_block
        body = flatten([self.translate_stmt(stmt, ctx) for stmt in node.body])
        if try_block.else_block:
            goto = self.viper.Goto(try_block.else_block.name,
                                   self.to_position(node, ctx), self.noinfo(ctx))
            body += [goto]
        elif try_block.finally_block:
            goto = self.viper.Goto(try_block.finally_name,
                                   self.to_position(node, ctx), self.noinfo(ctx))
            body += [goto]
        end_label = self.viper.Label('post_' + node.sil_name,
                                     self.to_position(node, ctx),
                                     self.noinfo(ctx))
        return body + [end_label]

    def translate_stmt_Raise(self, node: ast.Raise, ctx) -> List[Stmt]:
        var = self._get_error_var(node, ctx)
        stmt, exception = self.translate_expr(node.exc, ctx)
        assignment = self.viper.LocalVarAssign(var, exception,
                                               self.to_position(node, ctx),
                                               self.noinfo(ctx))
        catchers = self.create_exception_catchers(var,
            ctx.current_function.try_blocks, node, ctx)
        return stmt + [assignment] + catchers

    def translate_stmt_Call(self, node: ast.Call, ctx) -> List[Stmt]:
        if get_func_name(node) == 'Assert':
            assert len(node.args) == 1
            stmt, expr = self.translate_expr(node.args[0], ctx)
            assertion = self.viper.Assert(expr, self.to_position(node, ctx),
                                          self.noinfo(ctx))
            return stmt + [assertion]
        else:
            stmt, expr = self.translate_Call(node, ctx)
            if not stmt:
                raise InvalidProgramException(node, 'no.effect')
            return stmt

    def translate_stmt_Expr(self, node: ast.Expr, ctx) -> List[Stmt]:
        if isinstance(node.value, ast.Call):
            return self.translate_stmt(node.value, ctx)
        else:
            raise UnsupportedException(node)

    def translate_stmt_If(self, node: ast.If, ctx) -> List[Stmt]:
        cond_stmt, cond = self.translate_to_bool(node.test, ctx)
        then_body = flatten([self.translate_stmt(stmt, ctx) for stmt in node.body])
        then_block = self.translate_block(then_body, self.to_position(node, ctx),
                                          self.noinfo(ctx))
        else_body = flatten([self.translate_stmt(stmt, ctx) for stmt in node.orelse])
        else_block = self.translate_block(
            else_body,
            self.to_position(node, ctx), self.noinfo(ctx))
        position = self.to_position(node, ctx)
        return cond_stmt + [self.viper.If(cond, then_block, else_block,
                                          position, self.noinfo(ctx))]

    def translate_stmt_Assign(self, node: ast.Assign, ctx) -> List[Stmt]:
        if len(node.targets) != 1:
            raise UnsupportedException(node)
        if isinstance(node.targets[0], ast.Subscript):
            if not isinstance(node.targets[0].slice, ast.Index):
                raise UnsupportedException(node)
            target_cls = self.get_type(node.targets[0].value, ctx)
            lhs_stmt, target = self.translate_expr(node.targets[0].value, ctx)
            ind_stmt, index = self.translate_expr(node.targets[0].slice.value, ctx)
            func = target_cls.get_method('__setitem__')
            func_name = func.sil_name
            rhs_stmt, rhs = self.translate_expr(node.value, ctx)
            args = [target, index, rhs]
            targets = []
            call = self.viper.MethodCall(func_name, args, targets,
                                         self.to_position(node, ctx), self.noinfo(ctx))
            return lhs_stmt + ind_stmt + rhs_stmt + [call]
        target = node.targets[0]
        lhs_stmt, var = self.translate_expr(target, ctx)
        if isinstance(target, ast.Name):
            assignment = self.viper.LocalVarAssign
        else:
            assignment = self.viper.FieldAssign
        rhs_stmt, rhs = self.translate_expr(node.value, ctx)
        assign = assignment(var,
                            rhs, self.to_position(node, ctx),
                            self.noinfo(ctx))
        return lhs_stmt + rhs_stmt + [assign]

    def is_invariant(self, stmt: ast.AST) -> bool:
        return get_func_name(stmt) == 'Invariant'

    def translate_stmt_While(self, node: ast.While, ctx) -> List[Stmt]:
        cond_stmt, cond = self.translate_to_bool(node.test, ctx)
        if cond_stmt:
            raise InvalidProgramException(node, 'purity.violated')
        invariants = []
        locals = []
        bodyindex = 0
        while self.is_invariant(node.body[bodyindex]):
            invariants.append(self.translate_contract(node.body[bodyindex], ctx))
            bodyindex += 1
        body = flatten(
            [self.translate_stmt(stmt, ctx) for stmt in node.body[bodyindex:]])
        body = self.translate_block(body, self.to_position(node, ctx),
                                    self.noinfo(ctx))
        return [self.viper.While(cond, invariants, locals, body,
                                 self.to_position(node, ctx),
                                 self.noinfo(ctx))]

    def translate_stmt_Return(self,
                              node: ast.Return, ctx) -> List[Stmt]:
        type = ctx.current_function.type
        rhs_stmt, rhs = self.translate_expr(node.value, ctx)
        assign = self.viper.LocalVarAssign(
            self.viper.LocalVar('_res', self.translate_type(type, ctx),
                                self.noposition(ctx), self.noinfo(ctx)),
            rhs, self.to_position(node, ctx),
            self.noinfo(ctx))
        tries = self._get_surrounding_try_blocks(
            ctx.current_function.try_blocks, node)
        for try_block in tries:
            if try_block.finally_block:
                lhs = try_block.get_finally_var(self.translator).ref
                rhs = self.viper.IntLit(1, self.noposition(ctx), self.noinfo(ctx))
                finally_assign = self.viper.LocalVarAssign(lhs, rhs,
                                                           self.noposition(ctx),
                                                           self.noinfo(ctx))
                jmp = self.viper.Goto(try_block.finally_name,
                                      self.to_position(node, ctx),
                                      self.noinfo(ctx))
                return rhs_stmt + [assign, finally_assign, jmp]
        jmp_to_end = self.viper.Goto("__end", self.to_position(node, ctx),
                                     self.noinfo(ctx))
        return rhs_stmt + [assign, jmp_to_end]
