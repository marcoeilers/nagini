import ast

from py2viper_translation.lib.constants import END_LABEL
from py2viper_translation.lib.util import (
    flatten,
    get_func_name,
    get_surrounding_try_blocks,
    InvalidProgramException,
    UnsupportedException,
)
from py2viper_translation.translators.abstract import (
    CommonTranslator,
    Context,
    Stmt,
)
from typing import List


class StatementTranslator(CommonTranslator):

    def translate_stmt(self, node: ast.AST, ctx: Context) -> List[Stmt]:
        """
        Generic visitor function for translating statements
        """
        method = 'translate_stmt_' + node.__class__.__name__
        visitor = getattr(self, method, self.translate_generic)
        return visitor(node, ctx)

    def translate_stmt_AugAssign(self, node: ast.AugAssign,
                                 ctx: Context) -> List[Stmt]:
        lhs_stmt, lhs = self.translate_expr(node.target, ctx)
        if lhs_stmt:
            raise InvalidProgramException(node, 'purity.violated')
        rhs_stmt, rhs = self.translate_expr(node.value, ctx)
        if isinstance(node.op, ast.Add):
            newval = self.viper.Add(lhs, rhs,
                                    self.to_position(node, ctx),
                                    self.no_info(ctx))
        elif isinstance(node.op, ast.Sub):
            newval = self.viper.Sub(lhs, rhs,
                                    self.to_position(node, ctx),
                                    self.no_info(ctx))
        elif isinstance(node.op, ast.Mult):
            newval = self.viper.Mul(lhs, rhs,
                                    self.to_position(node, ctx),
                                    self.no_info(ctx))
        else:
            raise UnsupportedException(node)
        position = self.to_position(node, ctx)
        if isinstance(node.target, ast.Name):
            assign = self.viper.LocalVarAssign(lhs, newval, position,
                                               self.no_info(ctx))
        elif isinstance(node.target, ast.Attribute):
            assign = self.viper.FieldAssign(lhs, newval, position,
                                            self.no_info(ctx))
        return rhs_stmt + [assign]

    def translate_stmt_Pass(self, node: ast.Pass, ctx: Context) -> List[Stmt]:
        return []

    def translate_stmt_Try(self, node: ast.Try, ctx: Context) -> List[Stmt]:
        try_block = None
        for block in ctx.actual_function.try_blocks:
            if block.node is node:
                try_block = block
                break
        assert try_block
        code_var = try_block.get_finally_var(self.translator).ref
        zero = self.viper.IntLit(0, self.no_position(ctx), self.no_info(ctx))
        assign = self.viper.LocalVarAssign(code_var, zero, self.no_position(ctx),
                                           self.no_info(ctx))
        body = [assign]
        body += flatten([self.translate_stmt(stmt, ctx) for stmt in node.body])
        if try_block.else_block:
            else_label = ctx.get_label_name(try_block.else_block.name)
            goto = self.viper.Goto(else_label,
                                   self.to_position(node, ctx), self.no_info(ctx))
            body += [goto]
        elif try_block.finally_block:
            finally_name = ctx.get_label_name(try_block.finally_name)
            goto = self.viper.Goto(finally_name,
                                   self.to_position(node, ctx), self.no_info(ctx))
            body += [goto]
        label_name = ctx.get_label_name(try_block.post_name)
        end_label = self.viper.Label(label_name,
                                     self.to_position(node, ctx),
                                     self.no_info(ctx))
        return body + [end_label]

    def translate_stmt_Raise(self, node: ast.Raise, ctx: Context) -> List[Stmt]:
        var = self.get_error_var(node, ctx)
        stmt, exception = self.translate_expr(node.exc, ctx)
        assignment = self.viper.LocalVarAssign(var, exception,
                                               self.to_position(node, ctx),
                                               self.no_info(ctx))
        catchers = self.create_exception_catchers(var,
            ctx.actual_function.try_blocks, node, ctx)
        return stmt + [assignment] + catchers

    def translate_stmt_Call(self, node: ast.Call, ctx: Context) -> List[Stmt]:
        stmt, expr = self.translate_Call(node, ctx)
        if not stmt:
            raise InvalidProgramException(node, 'no.effect')
        return stmt

    def translate_stmt_Expr(self, node: ast.Expr, ctx: Context) -> List[Stmt]:
        if isinstance(node.value, ast.Call):
            return self.translate_stmt(node.value, ctx)
        else:
            raise UnsupportedException(node)

    def translate_stmt_If(self, node: ast.If, ctx: Context) -> List[Stmt]:
        cond_stmt, cond = self.translate_to_bool(node.test, ctx)
        then_body = flatten([self.translate_stmt(stmt, ctx)
                             for stmt in node.body])
        then_block = self.translate_block(then_body,
                                          self.to_position(node, ctx),
                                          self.no_info(ctx))
        else_body = flatten([self.translate_stmt(stmt, ctx)
                             for stmt in node.orelse])
        else_block = self.translate_block(
            else_body,
            self.to_position(node, ctx), self.no_info(ctx))
        position = self.to_position(node, ctx)
        return cond_stmt + [self.viper.If(cond, then_block, else_block,
                                          position, self.no_info(ctx))]

    def translate_stmt_Assign(self, node: ast.Assign,
                              ctx: Context) -> List[Stmt]:
        if len(node.targets) != 1:
            raise UnsupportedException(node)
        if isinstance(node.targets[0], ast.Subscript):
            if not isinstance(node.targets[0].slice, ast.Index):
                raise UnsupportedException(node)
            target_cls = self.get_type(node.targets[0].value, ctx)
            lhs_stmt, target = self.translate_expr(node.targets[0].value, ctx)
            ind_stmt, index = self.translate_expr(node.targets[0].slice.value,
                                                  ctx)
            func = target_cls.get_method('__setitem__')
            func_name = func.sil_name
            rhs_stmt, rhs = self.translate_expr(node.value, ctx)
            args = [target, index, rhs]
            targets = []
            call = self.viper.MethodCall(func_name, args, targets,
                                         self.to_position(node, ctx),
                                         self.no_info(ctx))
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
                            self.no_info(ctx))
        return lhs_stmt + rhs_stmt + [assign]

    def is_invariant(self, stmt: ast.AST) -> bool:
        return get_func_name(stmt) == 'Invariant'

    def translate_stmt_While(self, node: ast.While,
                             ctx: Context) -> List[Stmt]:
        cond_stmt, cond = self.translate_to_bool(node.test, ctx)
        if cond_stmt:
            raise InvalidProgramException(node, 'purity.violated')
        invariants = []
        locals = []
        bodyindex = 0
        while self.is_invariant(node.body[bodyindex]):
            invariants.append(self.translate_contract(node.body[bodyindex],
                                                      ctx))
            bodyindex += 1
        body = flatten(
            [self.translate_stmt(stmt, ctx) for stmt in node.body[bodyindex:]])
        body = self.translate_block(body, self.to_position(node, ctx),
                                    self.no_info(ctx))
        return [self.viper.While(cond, invariants, locals, body,
                                 self.to_position(node, ctx),
                                 self.no_info(ctx))]

    def _translate_return(self, node: ast.Return, ctx: Context) -> List[Stmt]:
        type_ = ctx.actual_function.type
        rhs_stmt, rhs = self.translate_expr(node.value, ctx)
        assign = self.viper.LocalVarAssign(
            ctx.result_var,
            rhs, self.to_position(node, ctx),
            self.no_info(ctx))

        return rhs_stmt + [assign]

    def translate_stmt_Return(self, node: ast.Return,
                              ctx: Context) -> List[Stmt]:
        return_stmts = self._translate_return(node, ctx)
        tries = get_surrounding_try_blocks(ctx.actual_function.try_blocks,
                                           node)
        for try_block in tries:
            if try_block.finally_block:
                lhs = try_block.get_finally_var(self.translator).ref
                rhs = self.viper.IntLit(1, self.no_position(ctx),
                                        self.no_info(ctx))
                finally_assign = self.viper.LocalVarAssign(lhs, rhs,
                    self.no_position(ctx), self.no_info(ctx))
                label_name = ctx.get_label_name(try_block.finally_name)
                jmp = self.viper.Goto(label_name,
                                      self.to_position(node, ctx),
                                      self.no_info(ctx))
                return return_stmts + [finally_assign, jmp]
        end_label = ctx.get_label_name(END_LABEL)
        jmp_to_end = self.viper.Goto(end_label, self.to_position(node, ctx),
                                     self.no_info(ctx))
        return return_stmts + [jmp_to_end]
