import ast

from py2viper_translation.lib.constants import END_LABEL, PRIMITIVES
from py2viper_translation.lib.program_nodes import (
    PythonClass,
    PythonField,
    PythonTryBlock,
    PythonVar
)
from py2viper_translation.lib.util import (
    get_surrounding_try_blocks,
    InvalidProgramException,
    UnsupportedException,
)
from py2viper_translation.translators.abstract import (
    CommonTranslator,
    Context,
    Expr,
    StmtsAndExpr,
    Stmt
)
from typing import List, Optional


class ExpressionTranslator(CommonTranslator):

    def translate_expr(self, node: ast.AST, ctx: Context) -> StmtsAndExpr:
        """
        Generic visitor function for translating an expression
        """
        method = 'translate_' + node.__class__.__name__
        visitor = getattr(self, method, self.translate_generic)
        return visitor(node, ctx)

    def translate_Return(self, node: ast.Return, ctx: Context) -> StmtsAndExpr:
        return self.translate_expr(node.value, ctx)

    def translate_Num(self, node: ast.Num, ctx: Context) -> StmtsAndExpr:
        return ([], self.viper.IntLit(node.n, self.to_position(node, ctx),
                                      self.no_info(ctx)))

    def translate_Dict(self, node: ast.Dict, ctx: Context) -> StmtsAndExpr:
        args = []
        res_var = ctx.current_function.create_variable('dict',
            ctx.program.classes['dict'], self.translator)
        targets = [res_var.ref]
        constr_call = self.viper.MethodCall('dict___init__', args, targets,
                                            self.to_position(node, ctx),
                                            self.no_info(ctx))
        stmt = [constr_call]
        for key, val in zip(node.keys, node.values):
            key_stmt, key_val = self.translate_expr(key, ctx)
            val_stmt, val_val = self.translate_expr(val, ctx)
            append_call = self.viper.MethodCall('dict___setitem__',
                                                [res_var.ref, key_val, val_val],
                                                [], self.to_position(node, ctx),
                                                self.no_info(ctx))
            stmt += key_stmt + val_stmt + [append_call]
        return stmt, res_var.ref

    def translate_Set(self, node: ast.Set, ctx: Context) -> StmtsAndExpr:
        args = []
        res_var = ctx.current_function.create_variable('set',
            ctx.program.classes['set'], self.translator)
        targets = [res_var.ref]
        constr_call = self.viper.MethodCall('set___init__', args, targets,
                                            self.to_position(node, ctx),
                                            self.no_info(ctx))
        stmt = [constr_call]
        for el in node.elts:
            el_stmt, el_val = self.translate_expr(el, ctx)
            append_call = self.viper.MethodCall('set_add',
                                                [res_var.ref, el_val], [],
                                                self.to_position(node, ctx),
                                                self.no_info(ctx))
            stmt += el_stmt + [append_call]
        return stmt, res_var.ref

    def translate_List(self, node: ast.List, ctx: Context) -> StmtsAndExpr:
        args = []
        res_var = ctx.current_function.create_variable('list',
            ctx.program.classes['list'], self.translator)
        targets = [res_var.ref]
        constr_call = self.viper.MethodCall('list___init__', args, targets,
                                            self.to_position(node, ctx),
                                            self.no_info(ctx))
        stmt = [constr_call]
        for element in node.elts:
            el_stmt, el = self.translate_expr(element, ctx)
            append_call = self.viper.MethodCall('list_append',
                                                [res_var.ref, el], [],
                                                self.to_position(node, ctx),
                                                self.no_info(ctx))
            stmt += el_stmt + [append_call]
        return stmt, res_var.ref

    def _get_string_value(self, string: str) -> int:
        result = 0
        for index in range(len(string)):
            result += pow(256, index) * ord(string[index])
        return result

    def translate_Str(self, node: ast.Str, ctx: Context) -> StmtsAndExpr:
        length = len(node.s)
        length_arg = self.viper.IntLit(length, self.no_position(ctx),
                                       self.no_info(ctx))
        val_arg = self.viper.IntLit(self._get_string_value(node.s),
                                    self.no_position(ctx), self.no_info(ctx))
        args = [length_arg, val_arg]
        type = self.viper.Ref
        length_param = self.viper.LocalVarDecl('length', self.viper.Int,
                                               self.no_position(ctx),
                                               self.no_info(ctx))
        val_param = self.viper.LocalVarDecl('val', self.viper.Int,
                                            self.no_position(ctx),
                                            self.no_info(ctx))
        formal_args = [length_param, val_param]
        call = self.viper.FuncApp('str___create__', args,
                                  self.to_position(node, ctx),
                                  self.no_info(ctx), type, formal_args)
        return [], call

    def translate_Tuple(self, node: ast.Tuple, ctx: Context) -> StmtsAndExpr:
        stmts = []
        vals = []
        for el in node.elts:
            el_stmt, el_val = self.translate_to_reference(el, ctx)
            stmts += el_stmt
            vals.append(el_val)
        elements = self.viper.ExplicitSeq(vals, self.to_position(node, ctx),
                                          self.no_info(ctx))
        type = self.viper.Ref
        el_arg = self.viper.LocalVarDecl('seq',
                                         self.viper.SeqType(self.viper.Ref),
                                         self.no_position(ctx),
                                         self.no_info(ctx))
        call = self.viper.FuncApp('Tuple___init__', [elements],
                                  self.to_position(node, ctx),
                                  self.no_info(ctx), type, [el_arg])
        return stmts, call

    def translate_Subscript(self, node: ast.Subscript,
                            ctx: Context) -> StmtsAndExpr:
        if not isinstance(node.slice, ast.Index):
            raise UnsupportedException(node)
        target_stmt, target = self.translate_expr(node.value, ctx)
        index_stmt, index = self.translate_expr(node.slice.value, ctx)
        args = [target, index]
        call = self.get_function_call(node.value, '__getitem__', args, node,
                                      ctx)
        return target_stmt + index_stmt, call

    def create_exception_catchers(self, var: PythonVar,
                                  try_blocks: List[PythonTryBlock],
                                  call: ast.Call, ctx: Context) -> List[Stmt]:
        """
        Creates the code for catching an exception, i.e. redirecting control
        flow to the handlers, to a finally block, or giving the exception to
        the caller function.
        """
        if isinstance(var, PythonVar):
            var = var.ref
        cases = []
        position = self.to_position(call, ctx)
        err_var = ctx.error_var
        relevant_try_blocks = get_surrounding_try_blocks(try_blocks, call)
        goto_finally = self._create_goto_finally(relevant_try_blocks, ctx)
        if goto_finally:
            uncaught_option = goto_finally
        else:
            if ctx.actual_function.declared_exceptions:
                assignerror = self.viper.LocalVarAssign(err_var, var, position,
                                                        self.no_info(ctx))
                end_label = ctx.get_label_name(END_LABEL)
                gotoend = self.viper.Goto(end_label, position,
                                          self.no_info(ctx))
                uncaught_option = self.translate_block([assignerror, gotoend],
                                                       position,
                                                       self.no_info(ctx))
            else:
                uncaught_option = self.viper.Exhale(
                    self.viper.FalseLit(position, self.no_info(ctx)), position,
                    self.no_info(ctx))

        for block in relevant_try_blocks:
            for handler in block.handlers:
                condition = self.type_factory.type_check(var, handler.exception,
                                                         ctx)
                label_name = ctx.get_label_name(handler.name)
                goto = self.viper.Goto(label_name,
                                       self.to_position(handler.node, ctx),
                                       self.no_info(ctx))
                cases.insert(0, (condition, goto))
            if block.finally_block:
                break

        result = None
        for cond, goto in cases:
            if result is None:
                result = self.viper.If(cond, goto,
                                       uncaught_option,
                                       self.to_position(handler.node, ctx),
                                       self.no_info(ctx))
            else:
                result = self.viper.If(cond, goto, result,
                                       self.to_position(handler.node, ctx),
                                       self.no_info(ctx))
        if result is None:
            error_case = uncaught_option
        else:
            error_case = result
        errnotnull = self.viper.NeCmp(var,
                                      self.viper.NullLit(self.no_position(ctx),
                                                         self.no_info(ctx)),
                                      position, self.no_info(ctx))
        emptyblock = self.translate_block([], self.no_position(ctx),
                                          self.no_info(ctx))
        errcheck = self.viper.If(errnotnull, error_case, emptyblock,
                                 position,
                                 self.no_info(ctx))
        return [errcheck]

    def _create_goto_finally(self, tries: List[PythonTryBlock],
                             ctx: Context) -> Optional[Stmt]:
        """
        If any of the blocks in tries has a finally-block, creates and
        returns the statements to jump there.
        """
        for try_ in tries:
            if try_.finally_block:
                # propagate return value
                var_next = try_.get_finally_var(self.translator)
                if var_next.sil_name in ctx.var_aliases:
                    var_next = ctx.var_aliases[var_next.sil_name]
                number_two = self.viper.IntLit(2, self.no_position(ctx),
                                               self.no_info(ctx))
                next_assign = self.viper.LocalVarAssign(var_next.ref,
                                                        number_two,
                                                        self.no_position(ctx),
                                                        self.no_info(ctx))
                # goto finally block
                label_name = ctx.get_label_name(try_.finally_name)
                goto_next = self.viper.Goto(label_name,
                                            self.no_position(ctx),
                                            self.no_info(ctx))
                return_block = [next_assign, goto_next]
                result = self.translate_block(return_block,
                                              self.no_position(ctx),
                                              self.no_info(ctx))
                return result
        return None

    def translate_to_bool(self, node: ast.AST, ctx: Context) -> StmtsAndExpr:
        """
        Translates node as a normal expression, then applies Python's auto-
        conversion to a boolean value (using the __bool__ function)
        """
        stmt, res = self.translate_expr(node, ctx)
        type = self.get_type(node, ctx)
        if type is ctx.program.classes['bool']:
            return stmt, res
        args = [res]
        call = self.get_function_call(node, '__bool__', args, node, ctx)
        return stmt, call

    def translate_to_reference(self, node: ast.AST,
                               ctx: Context) -> StmtsAndExpr:
        stmt, val = self.translate_expr(node, ctx)
        type = self.get_type(node, ctx)
        if type.name in PRIMITIVES:
            var = ctx.current_function.create_variable('box',
                ctx.program.classes['__boxed_' + type.name], self.translator)
            field = self.viper.Field(type.name + '_value___',
                                     self.translate_type(type, ctx),
                                     self.no_position(ctx), self.no_info(ctx))
            new = self.viper.NewStmt(var.ref, [field],
                                     self.to_position(node, ctx),
                                     self.no_info(ctx))
            field_acc = self.viper.FieldAccess(var.ref, field,
                                               self.to_position(node, ctx),
                                               self.no_info(ctx))
            assign = self.viper.FieldAssign(field_acc, val,
                                            self.to_position(node, ctx),
                                            self.no_info(ctx))
            stmt.append(new)
            stmt.append(assign)
            val = var.ref
        return stmt, val

    def translate_Expr(self, node: ast.Expr, ctx: Context) -> StmtsAndExpr:
        return self.translate_expr(node.value, ctx)

    def translate_Name(self, node: ast.Name, ctx: Context) -> StmtsAndExpr:
        if node.id in ctx.program.global_vars:
            var = ctx.program.global_vars[node.id]
            type = self.translate_type(var.type, ctx)
            func_app = self.viper.FuncApp(var.sil_name, [],
                                          self.to_position(node, ctx),
                                          self.no_info(ctx), type, [])
            return [], func_app
        else:
            if node.id in ctx.var_aliases:
                return [], ctx.var_aliases[node.id].ref
            else:
                return [], ctx.current_function.get_variable(node.id).ref

    def _lookup_field(self, node: ast.Attribute, ctx: Context) -> PythonField:
        """
        Returns the PythonField for a given ast.Attribute node.
        """
        recv = self.get_type(node.value, ctx)
        field = recv.get_field(node.attr)
        if not field:
            raise InvalidProgramException(node, 'field.nonexistant')
        while field.inherited is not None:
            field = field.inherited
        if field.is_mangled() and (field.cls is not ctx.current_class and
                                   field.cls is not ctx.actual_function.cls):
            raise InvalidProgramException(node, 'private.field.access')

        return field

    def translate_Attribute(self, node: ast.Attribute,
                            ctx: Context) -> StmtsAndExpr:
        stmt, receiver = self.translate_expr(node.value, ctx)
        field = self._lookup_field(node, ctx)
        return (stmt, self.viper.FieldAccess(receiver, field.sil_field,
                                             self.to_position(node, ctx),
                                             self.no_info(ctx)))

    def translate_UnaryOp(self, node: ast.UnaryOp,
                          ctx: Context) -> StmtsAndExpr:
        if isinstance(node.op, ast.Not):
            stmt, expr = self.translate_to_bool(node.operand, ctx)
            return (stmt, self.viper.Not(expr, self.to_position(node, ctx),
                                         self.no_info(ctx)))
        stmt, expr = self.translate_expr(node.operand, ctx)
        if isinstance(node.op, ast.USub):
            return (stmt, self.viper.Minus(expr, self.to_position(node, ctx),
                                           self.no_info(ctx)))
        else:
            raise UnsupportedException(node)

    def translate_IfExp(self, node: ast.IfExp, ctx: Context) -> StmtsAndExpr:
        position = self.to_position(node, ctx)
        cond_stmt, cond = self.translate_to_bool(node.test, ctx)
        then_stmt, then = self.translate_expr(node.body, ctx)
        else_stmt, else_ = self.translate_expr(node.orelse, ctx)
        if then_stmt or else_stmt:
            then_block = self.translate_block(then_stmt, position,
                                              self.no_info(ctx))
            else_block = self.translate_block(else_stmt, position,
                                              self.no_info(ctx))
            if_stmt = self.viper.If(cond, then_block, else_block, position,
                                    self.no_info(ctx))
            bodystmt = [if_stmt]
        else:
            bodystmt = []
        cond_exp = self.viper.CondExp(cond, then, else_,
                                      self.to_position(node, ctx),
                                      self.no_info(ctx))
        return cond_stmt + bodystmt, cond_exp

    def translate_BinOp(self, node: ast.BinOp, ctx: Context) -> StmtsAndExpr:
        left_stmt, left = self.translate_expr(node.left, ctx)
        right_stmt, right = self.translate_expr(node.right, ctx)
        stmt = left_stmt + right_stmt
        left_type = self.get_type(node.left, ctx)
        if left_type.name != 'int':
            call = self.get_function_call(node.left, '__add__', [left, right],
                                          node, ctx)
            return stmt, call
        if isinstance(node.op, ast.Add):
            return (stmt, self.viper.Add(left, right,
                                         self.to_position(node, ctx),
                                         self.no_info(ctx)))
        elif isinstance(node.op, ast.Sub):
            return (stmt, self.viper.Sub(left, right,
                                         self.to_position(node, ctx),
                                         self.no_info(ctx)))
        elif isinstance(node.op, ast.Mult):
            return (stmt, self.viper.Mul(left, right,
                                         self.to_position(node, ctx),
                                         self.no_info(ctx)))
        elif isinstance(node.op, ast.FloorDiv):
            return (stmt, self.viper.Div(left, right,
                                         self.to_position(node, ctx),
                                         self.no_info(ctx)))
        elif isinstance(node.op, ast.Mod):
            return (stmt, self.viper.Mod(left, right,
                                         self.to_position(node, ctx),
                                         self.no_info(ctx)))
        else:
            raise UnsupportedException(node)

    def translate_Compare(self, node: ast.Compare,
                          ctx: Context) -> StmtsAndExpr:
        if len(node.ops) != 1 or len(node.comparators) != 1:
            raise UnsupportedException(node)
        left_stmt, left = self.translate_expr(node.left, ctx)
        right_stmt, right = self.translate_expr(node.comparators[0], ctx)
        stmts = left_stmt + right_stmt
        if isinstance(node.ops[0], ast.Eq):
            # TODO: because get_type doesn't work on all expressions, this
            # currently breaks everything
            # if self.get_type(node.left, ctx).name not in PRIMITIVES:
            #     call = self.get_function_call(node.left, '__eq__',
            #                                   [left, right], node, ctx)
            #     return stmts, call
            return (stmts, self.viper.EqCmp(left, right,
                                            self.to_position(node, ctx),
                                            self.no_info(ctx)))
        elif isinstance(node.ops[0], ast.Is):
            return (stmts, self.viper.EqCmp(left, right,
                                            self.to_position(node, ctx),
                                            self.no_info(ctx)))
        elif isinstance(node.ops[0], ast.Gt):
            return (stmts, self.viper.GtCmp(left, right,
                                            self.to_position(node, ctx),
                                            self.no_info(ctx)))
        elif isinstance(node.ops[0], ast.GtE):
            return (stmts, self.viper.GeCmp(left, right,
                                            self.to_position(node, ctx),
                                            self.no_info(ctx)))
        elif isinstance(node.ops[0], ast.Lt):
            return (stmts, self.viper.LtCmp(left, right,
                                            self.to_position(node, ctx),
                                            self.no_info(ctx)))
        elif isinstance(node.ops[0], ast.LtE):
            return (stmts, self.viper.LeCmp(left, right,
                                            self.to_position(node, ctx),
                                            self.no_info(ctx)))
        elif isinstance(node.ops[0], ast.NotEq):
            return (stmts, self.viper.NeCmp(left, right,
                                            self.to_position(node, ctx),
                                            self.no_info(ctx)))
        elif isinstance(node.ops[0], ast.IsNot):
            return (stmts, self.viper.NeCmp(left, right,
                                            self.to_position(node, ctx),
                                            self.no_info(ctx)))
        elif isinstance(node.ops[0], ast.In):
            args = [right, left]
            app = self.get_function_call(node.comparators[0], '__contains__',
                                         args, node, ctx)
            return stmts, app
        else:
            raise UnsupportedException(node.ops[0])

    def translate_NameConstant(self, node: ast.NameConstant,
                               ctx: Context) -> StmtsAndExpr:
        if node.value is True:
            return ([], self.viper.TrueLit(self.to_position(node, ctx),
                                           self.no_info(ctx)))
        elif node.value is False:
            return ([], self.viper.FalseLit(self.to_position(node, ctx),
                                            self.no_info(ctx)))
        elif node.value is None:
            return ([],
                    self.viper.NullLit(self.to_position(node, ctx),
                                       self.no_info(ctx)))
        else:
            raise UnsupportedException(node)

    def translate_BoolOp(self, node: ast.BoolOp, ctx: Context) -> StmtsAndExpr:
        if len(node.values) != 2:
            raise UnsupportedException(node)
        position = self.to_position(node, ctx)
        left_stmt, left = self.translate_expr(node.values[0], ctx)
        right_stmt, right = self.translate_expr(node.values[1], ctx)
        if left_stmt or right_stmt:
            # TODO: Something important breaks if we run this normally
            # with an acc() as left and a method call on the rhs. If this
            # happens in a test, all tests afterwards fail. Either catch all
            # such cases here, or fix it in Silver.
            if isinstance(left, self.jvm.viper.silver.ast.FieldAccessPredicate):
                return left_stmt + right_stmt, right
            cond = left
            if isinstance(node.op, ast.Or):
                cond = self.viper.Not(cond, position, self.no_info(ctx))
            then_block = self.translate_block(right_stmt, position,
                                              self.no_info(ctx))
            else_block = self.translate_block([], position, self.no_info(ctx))
            if_stmt = self.viper.If(cond, then_block, else_block, position,
                                   self.no_info(ctx))
            stmt = left_stmt + [if_stmt]
        else:
            stmt = []
        if isinstance(node.op, ast.And):
            return (stmt, self.viper.And(left,
                                         right,
                                         self.to_position(node, ctx),
                                         self.no_info(ctx)))
        elif isinstance(node.op, ast.Or):
            return (stmt, self.viper.Or(left,
                                        right,
                                        self.to_position(node, ctx),
                                        self.no_info(ctx)))
        else:
            raise UnsupportedException(node)

    def translate_pythonvar_decl(self, var: PythonVar,
                                 ctx: Context) -> 'silver.ast.LocalVarDecl':
        """
        Creates a variable declaration for the given PythonVar.
        To be called during the processing phase by the Analyzer.
        """
        return self.viper.LocalVarDecl(var.sil_name,
                                       self.translate_type(var.type, ctx),
                                       self.no_position(ctx), self.no_info(ctx))

    def translate_pythonvar_ref(self, var: PythonVar, ctx: Context) -> Expr:
        """
        Creates a variable reference for the given PythonVar.
        To be called during the processing phase by the Analyzer.
        """
        return self.viper.LocalVar(var.sil_name,
                                   self.translate_type(var.type, ctx),
                                   self.no_position(ctx), self.no_info(ctx))