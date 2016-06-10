import ast

from py2viper_translation.lib.constants import END_LABEL, PRIMITIVES, TUPLE_TYPE
from py2viper_translation.lib.program_nodes import PythonType
from py2viper_translation.lib.typedefs import (
    Expr,
    Stmt,
    StmtsAndExpr,
)
from py2viper_translation.lib.util import (
    flatten,
    get_func_name,
    get_surrounding_try_blocks,
    InvalidProgramException,
    UnsupportedException,
)
from py2viper_translation.translators.abstract import Context
from py2viper_translation.translators.common import CommonTranslator
from typing import List, Optional


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
        code_var = try_block.get_finally_var(self.translator)
        if code_var.sil_name in ctx.var_aliases:
            code_var = ctx.var_aliases[code_var.sil_name]
        code_var = code_var.ref
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
        if expr:
            type = self.get_type(node, ctx)
            var = ctx.current_function.create_variable('expr', type,
                                                       self.translator)
            assign = self.viper.LocalVarAssign(var.ref, expr,
                                               self.to_position(node, ctx),
                                               self.no_info(ctx))
            stmt.append(assign)
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

    def assign_to(self, lhs: ast.AST, rhs: Expr, rhs_index: Optional[int],
                  rhs_type: PythonType, node: ast.AST,
                  ctx: Context) -> List[Stmt]:
        if rhs_index is not None:
            index_lit = self.viper.IntLit(rhs_index, self.no_position(ctx),
                                          self.no_info(ctx))
            args = [rhs, index_lit]
            arg_types = [rhs_type, None]
            rhs = self.get_function_call(rhs_type, '__getitem__', args,
                                         arg_types, node, ctx)
            rhs_index_type = rhs_type.type_args[rhs_index]
            if rhs_index_type.name in PRIMITIVES:
                rhs = self.unbox_primitive(rhs, rhs_index_type, node, ctx)
        if isinstance(lhs, ast.Subscript):
            if not isinstance(node.targets[0].slice, ast.Index):
                raise UnsupportedException(node)
            target_cls = self.get_type(lhs.value, ctx)
            lhs_stmt, target = self.translate_expr(lhs.value, ctx)
            ind_stmt, index = self.translate_expr(lhs.slice.value, ctx)
            index_type = self.get_type(lhs.slice.value, ctx)

            args = [target, index, rhs]
            arg_types = [None, index_type, rhs_type]
            call = self.get_method_call(target_cls, '__setitem__', args,
                                        arg_types, [], node, ctx)
            return lhs_stmt + ind_stmt + [call]
        target = lhs
        lhs_stmt, var = self.translate_expr(target, ctx)
        if isinstance(target, ast.Name):
            assignment = self.viper.LocalVarAssign
        else:
            assignment = self.viper.FieldAssign
        assign = assignment(var,
                            rhs, self.to_position(node, ctx),
                            self.no_info(ctx))
        return lhs_stmt + [assign]

    def translate_stmt_Assign(self, node: ast.Assign,
                              ctx: Context) -> List[Stmt]:
        rhs_type = self.get_type(node.value, ctx)
        rhs_stmt, rhs = rhs_stmt, rhs = self.translate_expr(node.value, ctx)
        assign_stmts = []
        for target in node.targets:
            assign_stmts += self.translate_single_assign(target, rhs, rhs_type,
                                                         node, ctx)
        return rhs_stmt + assign_stmts

    def translate_single_assign(self, target: ast.AST, rhs: Expr,
                                rhs_type: PythonType, node: ast.AST,
                                ctx: Context) -> List[Stmt]:
        stmt = []
        if isinstance(target, ast.Tuple):
            if (rhs_type.name != TUPLE_TYPE or
                    len(rhs_type.type_args) != len(node.targets[0].elts)):
                raise InvalidProgramException(node, 'invalid.assign')
            # translate rhs
            for index in range(len(target.elts)):
                stmt += self.assign_to(target.elts[index], rhs,
                                       index, rhs_type,
                                       node, ctx)
            return stmt
        lhs_stmt = self.assign_to(target, rhs, None, rhs_type, node, ctx)
        return lhs_stmt

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
        if not ctx.actual_function:
            return []
        type_ = ctx.actual_function.type
        rhs_stmt, rhs = self.translate_expr(node.value, ctx)
        assign = self.viper.LocalVarAssign(
            ctx.result_var.ref,
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
