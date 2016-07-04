import ast

from py2viper_translation.lib.constants import (
    BOOL_TYPE,
    DICT_TYPE,
    END_LABEL,
    INT_TYPE,
    LIST_TYPE,
    PRIMITIVES,
    SET_TYPE,
    STRING_TYPE,
    TUPLE_TYPE,
)
from py2viper_translation.lib.program_nodes import (
    PythonClass,
    PythonField,
    PythonTryBlock,
    PythonType,
    PythonVar
)
from py2viper_translation.lib.typedefs import (
    Expr,
    Stmt,
    StmtsAndExpr,
)
from py2viper_translation.lib.util import (
    get_surrounding_try_blocks,
    InvalidProgramException,
    UnsupportedException,
)
from py2viper_translation.translators.abstract import Context
from py2viper_translation.translators.common import CommonTranslator
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
            ctx.program.classes[DICT_TYPE], self.translator)
        dict_class = ctx.program.classes[DICT_TYPE]
        arg_types = []
        constr_call = self.get_method_call(dict_class, '__init__', [],
                                           [], [res_var.ref()],
                                           node, ctx)
        stmt = [constr_call]
        for key, val in zip(node.keys, node.values):
            key_stmt, key_val = self.translate_expr(key, ctx)
            key_type = self.get_type(key, ctx)
            val_stmt, val_val = self.translate_expr(val, ctx)
            val_type = self.get_type(val, ctx)
            args = [res_var.ref(), key_val, val_val]
            arg_types = [None, key_type, val_type]
            append_call = self.get_method_call(dict_class, '__setitem__', args,
                                               arg_types, [], node, ctx)
            stmt += key_stmt + val_stmt + [append_call]
        return stmt, res_var.ref(node, ctx)

    def translate_Set(self, node: ast.Set, ctx: Context) -> StmtsAndExpr:
        set_class = ctx.program.classes[SET_TYPE]
        res_var = ctx.current_function.create_variable(SET_TYPE,
            set_class, self.translator)
        constr_call = self.get_method_call(set_class, '__init__', [], [],
                                           [res_var.ref()], node, ctx)
        stmt = [constr_call]
        for el in node.elts:
            el_stmt, el_val = self.translate_expr(el, ctx)
            el_type = self.get_type(el, ctx)
            args = [res_var.ref(), el_val]
            arg_types = [None, el_type]
            append_call = self.get_method_call(set_class, 'add', args,
                                               arg_types, [], node, ctx)
            stmt += el_stmt + [append_call]
        return stmt, res_var.ref(node, ctx)

    def translate_List(self, node: ast.List, ctx: Context) -> StmtsAndExpr:
        list_class = ctx.program.classes[LIST_TYPE]
        res_var = ctx.current_function.create_variable(LIST_TYPE,
            list_class, self.translator)
        targets = [res_var.ref()]

        constr_call = self.get_method_call(list_class, '__init__', [], [],
                                           [res_var.ref()], node, ctx)
        stmt = [constr_call]
        for element in node.elts:
            el_stmt, el = self.translate_expr(element, ctx)
            el_type = self.get_type(element, ctx)
            args = [res_var.ref(), el]
            arg_types = [None, el_type]
            append_call = self.get_method_call(list_class, 'append', args,
                                               arg_types, [], node, ctx)
            stmt += el_stmt + [append_call]
        return stmt, res_var.ref(node, ctx)

    def translate_Str(self, node: ast.Str, ctx: Context) -> StmtsAndExpr:
        length = len(node.s)
        length_arg = self.viper.IntLit(length, self.no_position(ctx),
                                       self.no_info(ctx))
        val_arg = self.viper.IntLit(self._get_string_value(node.s),
                                    self.no_position(ctx), self.no_info(ctx))
        args = [length_arg, val_arg]
        arg_types = [None, None]
        str_type = ctx.program.classes[STRING_TYPE]
        func_name = '__create__'
        call = self.get_function_call(str_type, func_name, args, arg_types,
                                      node, ctx)
        return [], call

    def translate_Tuple(self, node: ast.Tuple, ctx: Context) -> StmtsAndExpr:
        stmts = []
        vals = []
        val_types = []
        for el in node.elts:
            el_stmt, el_val = self.translate_expr(el, ctx)
            stmts += el_stmt
            vals.append(el_val)
            val_types.append(self.get_type(el, ctx))
        tuple_class = ctx.program.classes[TUPLE_TYPE]
        func_name = '__create' + str(len(node.elts)) + '__'
        call = self.get_function_call(tuple_class, func_name, vals, val_types,
                                      node, ctx)
        return stmts, call

    def translate_Subscript(self, node: ast.Subscript,
                            ctx: Context) -> StmtsAndExpr:
        if not isinstance(node.slice, ast.Index):
            raise UnsupportedException(node)
        target_stmt, target = self.translate_expr(node.value, ctx)
        target_type = self.get_type(node.value, ctx)
        index_stmt, index = self.translate_expr(node.slice.value, ctx)
        index_type = self.get_type(node.slice.value, ctx)
        args = [target, index]
        arg_types = [target_type, index_type]
        call = self.get_function_call(target_type, '__getitem__', args,
                                      arg_types, node, ctx)
        result = call
        result_type = self.get_type(node, ctx)
        if result_type.name in PRIMITIVES:
            result = self.unbox_primitive(result, result_type, node, ctx)
        return target_stmt + index_stmt, result

    def create_exception_catchers(self, var: PythonVar,
                                  try_blocks: List[PythonTryBlock],
                                  call: ast.Call, ctx: Context) -> List[Stmt]:
        """
        Creates the code for catching an exception, i.e. redirecting control
        flow to the handlers, to a finally block, or giving the exception to
        the caller function.
        """
        if isinstance(var, PythonVar):
            var = var.ref()
        cases = []
        position = self.to_position(call, ctx)
        err_var = ctx.error_var.ref()
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
                error_string = '"method raises no exceptions"'
                error_pos = self.to_position(call, ctx, error_string)
                uncaught_option = self.viper.Exhale(
                    self.viper.FalseLit(error_pos, self.no_info(ctx)), error_pos,
                    self.no_info(ctx))

        for block in relevant_try_blocks:
            for handler in block.handlers:
                condition = self.type_check(var, handler.exception,
                                            self.to_position(handler.node, ctx),
                                            ctx, inhale_exhale=False)
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
                next_assign = self.viper.LocalVarAssign(var_next.ref(),
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
        if type is ctx.program.classes[BOOL_TYPE]:
            return stmt, res
        args = [res]
        arg_type = self.get_type(node, ctx)
        arg_types = [arg_type]
        call = self.get_function_call(arg_type, '__bool__', args, arg_types,
                                      node, ctx)
        return stmt, call

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
                return [], ctx.var_aliases[node.id].ref(node, ctx)
            else:
                return [], ctx.current_function.get_variable(node.id).ref(node,
                                                                          ctx)

    def _lookup_field(self, node: ast.Attribute, ctx: Context) -> PythonField:
        """
        Returns the PythonField for a given ast.Attribute node.
        """
        recv = self.get_type(node.value, ctx)
        field = recv.get_field(node.attr)
        if not field:
            recv = self.get_type(node.value, ctx)
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
        right_type = self.get_type(node.right, ctx)
        if left_type.name != INT_TYPE:
            call = self.get_function_call(left_type, '__add__', [left, right],
                                          [left_type, right_type], node, ctx)
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
        left_type = self.get_type(node.left, ctx)
        right_stmt, right = self.translate_expr(node.comparators[0], ctx)
        right_type = self.get_type(node.comparators[0], ctx)
        stmts = left_stmt + right_stmt
        if isinstance(node.ops[0], (ast.Eq, ast.NotEq)):
            # TODO: this is a workaround for the moment, but doesn't work in
            # general. If the static left type is e.g. object, but the runtime
            # type is e.g. str, we will use reference equality instead of
            # calling __eq__.
            is_not = isinstance(node.ops[0], ast.NotEq)
            if left_type.get_function('__eq__'):
                call = self.get_function_call(left_type, '__eq__',
                                              [left, right],
                                              [left_type, right_type],
                                              node, ctx)
                if is_not:
                    call = self.viper.Not(call, self.to_position(node, ctx),
                                          self.no_info(ctx))
                return stmts, call
            constr = self.viper.NeCmp if is_not else self.viper.EqCmp
            return (stmts, constr(left, right, self.to_position(node, ctx),
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
        elif isinstance(node.ops[0], ast.IsNot):
            return (stmts, self.viper.NeCmp(left, right,
                                            self.to_position(node, ctx),
                                            self.no_info(ctx)))
        elif isinstance(node.ops[0], (ast.In, ast.NotIn)):
            args = [right, left]
            arg_types = [right_type, left_type]
            app = self.get_function_call(right_type, '__contains__',
                                         args, arg_types, node, ctx)
            if isinstance(node.ops[0], ast.NotIn):
                app = self.viper.Not(app, self.to_position(node, ctx),
                                     self.no_info(ctx))
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

    def translate_pythonvar_ref(self, var: PythonVar, node: ast.AST,
                                ctx: Context) -> Expr:
        """
        Creates a variable reference for the given PythonVar.
        To be called during the processing phase by the Analyzer.
        """
        return self.viper.LocalVar(var.sil_name,
                                   self.translate_type(var.type, ctx),
                                   self.to_position(node, ctx),
                                   self.no_info(ctx))