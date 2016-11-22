import ast

from py2viper_translation.lib.constants import (
    DICT_TYPE,
    END_LABEL,
    LIST_TYPE,
    OBJECT_TYPE,
    PRIMITIVES,
    SET_TYPE,
    TUPLE_TYPE,
)
from py2viper_translation.lib.program_nodes import PythonType, PythonVar
from py2viper_translation.lib.typedefs import (
    Expr,
    Stmt,
    StmtsAndExpr,
)
from py2viper_translation.lib.util import (
    AssignCollector,
    contains_stmt,
    flatten,
    get_body_start_index,
    get_func_name,
    get_surrounding_try_blocks,
    InvalidProgramException,
    is_get_ghost_output,
    is_invariant,
    UnsupportedException,
)
from py2viper_translation.translators.abstract import Context
from py2viper_translation.translators.common import CommonTranslator
from typing import List, Optional, Tuple


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
        left_stmt, left = self.translate_expr(node.target, ctx)
        if left_stmt:
            raise InvalidProgramException(node, 'purity.violated')
        stmt, right = self.translate_expr(node.value, ctx)
        left_type = self.get_type(node.target, ctx)
        right_type = self.get_type(node.value, ctx)
        position = self.to_position(node, ctx)
        info = self.no_info(ctx)
        op_stmt, result = self.translate_operator(left, right, left_type,
                                                  right_type, node, ctx)
        stmt += op_stmt
        if isinstance(node.target, ast.Name):
            assign = self.viper.LocalVarAssign(left, result, position, info)
        elif isinstance(node.target, ast.Attribute):
            assign = self.viper.FieldAssign(left, result, position, info)
        return stmt + [assign]

    def translate_stmt_Pass(self, node: ast.Pass, ctx: Context) -> List[Stmt]:
        return []

    def _create_for_loop_invariant(self, iter_var: PythonVar,
                                   target_var: PythonVar,
                                   err_var: PythonVar,
                                   iterable: Expr,
                                   iterable_type: PythonType,
                                   node: ast.AST,
                                   ctx: Context) -> List[Stmt]:
        """
        Creates the default invariant for for loops using iterators. It's a
        static block of code that's always the same except for possible boxing
        and unboxing, and looks like this:

        invariant acc(a.list_acc, 1 / 20)
        invariant acc(iter.list_acc, 1 / 20)
        invariant iter.list_acc == list___sil_seq__(a)
        invariant acc(iter.__iter_index, write)
        invariant acc(iter.__previous, 1 / 20)
        invariant acc(iter.__previous.list_acc, write)
        invariant iter.__iter_index - 1 == list___len__(iter.__previous)
        invariant (iter_err == null) ==> (iter.__iter_index >= 0) &&
                  (iter.__iter_index <= |iter.list_acc|)
        invariant (iter_err == null) ==> (c ==
                                          iter.list_acc[iter.__iter_index - 1])
        invariant (iter_err == null) ==> (c in iter.list_acc)
        invariant (iter_err == null) ==>(iter.__previous.list_acc ==
                                         iter.list_acc[..iter.__iter_index - 1])
        invariant (iter_err != null) ==> (iter.__previous.list_acc ==
                                          iter.list_acc)
        """
        pos = self.to_position(node, ctx)
        info = self.no_info(ctx)
        seq_ref = self.viper.SeqType(self.viper.Ref)
        set_ref = self.viper.SetType(self.viper.Ref)

        param = self.viper.LocalVarDecl('self', self.viper.Ref, pos, info)

        seq_func_name = iterable_type.name + '___sil_seq__'
        iter_seq = self.viper.FuncApp(seq_func_name, [iterable], pos, info,
                                      seq_ref, [param])
        full_perm = self.viper.FullPerm(pos, info)
        wildcard = self.viper.WildcardPerm(pos, info)

        invariant = []
        one = self.viper.IntLit(1, pos, info)
        zero = self.viper.IntLit(0, pos, info)
        twenty = self.viper.IntLit(20, pos, info)
        frac_perm_120 = self.viper.FractionalPerm(one, twenty, pos, info)
        if iterable_type.name in {DICT_TYPE, LIST_TYPE, SET_TYPE}:
            field_name = iterable_type.name + '_acc'
            field_type = seq_ref if iterable_type.name == LIST_TYPE else set_ref
            acc_field = self.viper.Field(field_name, field_type, pos, info)
            field_acc = self.viper.FieldAccess(iterable, acc_field, pos, info)
            field_pred = self.viper.FieldAccessPredicate(field_acc,
                                                         frac_perm_120, pos,
                                                         info)
            invariant.append(field_pred)
        else:
            raise UnsupportedException(node)

        list_acc_field = self.viper.Field('list_acc', seq_ref, pos, info)
        iter_acc = self.viper.FieldAccess(iter_var.ref(), list_acc_field, pos,
                                          info)
        iter_acc_pred = self.viper.FieldAccessPredicate(iter_acc, frac_perm_120,
                                                        pos, info)
        invariant.append(iter_acc_pred)

        iter_list_equal = self.viper.EqCmp(iter_acc, iter_seq, pos, info)
        invariant.append(iter_list_equal)

        index_field = self.viper.Field('__iter_index', self.viper.Int, pos,
                                       info)
        iter_index_acc = self.viper.FieldAccess(iter_var.ref(), index_field,
                                                pos, info)
        iter_index_acc_pred = self.viper.FieldAccessPredicate(iter_index_acc,
                                                              full_perm, pos,
                                                              info)
        invariant.append(iter_index_acc_pred)

        previous_field = self.viper.Field('__previous', self.viper.Ref, pos,
                                          info)
        iter_previous_acc = self.viper.FieldAccess(iter_var.ref(),
                                                   previous_field,
                                                   pos, info)
        iter_previous_acc_pred = self.viper.FieldAccessPredicate(
            iter_previous_acc, frac_perm_120, pos, info)
        invariant.append(iter_previous_acc_pred)

        previous_list_acc = self.viper.FieldAccess(iter_previous_acc,
                                                   list_acc_field, pos, info)
        previous_list_acc_pred = self.viper.FieldAccessPredicate(
            previous_list_acc, full_perm, pos, info)
        invariant.append(previous_list_acc_pred)

        index_minus_one = self.viper.Sub(iter_index_acc, one, pos, info)
        object_class = ctx.module.global_module.classes[OBJECT_TYPE]
        list_class = ctx.module.global_module.classes[LIST_TYPE]
        previous_len = self.get_function_call(list_class, '__len__',
                                              [iter_previous_acc],
                                              [object_class], None, ctx)
        previous_len_eq = self.viper.EqCmp(index_minus_one, previous_len, pos,
                                           info)
        invariant.append(previous_len_eq)

        no_error = self.viper.EqCmp(err_var.ref(),
                                    self.viper.NullLit(pos, info),
                                    pos, info)
        some_error = self.viper.NeCmp(err_var.ref(),
                                      self.viper.NullLit(pos, info),
                                      pos, info)

        index_nonneg = self.viper.GeCmp(iter_index_acc, zero, pos, info)
        iter_list_len = self.viper.SeqLength(iter_acc, pos, info)
        index_le_len = self.viper.LeCmp(iter_index_acc, iter_list_len, pos,
                                        info)
        index_bounds = self.viper.And(index_nonneg, index_le_len, pos, info)
        invariant.append(self.viper.Implies(no_error, index_bounds, pos, info))

        iter_current_index = self.viper.SeqIndex(iter_acc, index_minus_one, pos,
                                                 info)
        boxed_target = target_var.ref()
        if target_var.type.name in PRIMITIVES:
            boxed_target = self.box_primitive(boxed_target, target_var.type,
                                              None, ctx)
            iter_current_index = self.unbox_primitive(iter_current_index,
                                                      target_var.type, None,
                                                      ctx)

        current_element_index = self.viper.EqCmp(target_var.ref(),
                                                 iter_current_index, pos, info)
        current_element_contained = self.viper.SeqContains(boxed_target,
                                                           iter_acc, pos, info)
        invariant.append(self.viper.Implies(no_error, current_element_index,
                                            pos, info))
        invariant.append(self.viper.Implies(no_error, current_element_contained,
                                            pos, info))

        previous_elements = self.viper.SeqTake(iter_acc, index_minus_one, pos,
                                               info)
        iter_previous_contents = self.viper.EqCmp(previous_list_acc,
                                                  previous_elements, pos, info)
        invariant.append(self.viper.Implies(no_error, iter_previous_contents,
                                            pos, info))

        previous_is_all = self.viper.EqCmp(previous_list_acc, iter_acc, pos,
                                           info)
        invariant.append(self.viper.Implies(some_error, previous_is_all, pos,
                                            info))
        return invariant

    def _get_iterator(self, iterable: Expr, iterable_type: PythonType,
                      node: ast.AST, ctx: Context) -> Tuple[PythonVar,
                                                            List[Stmt]]:
        iter_class = ctx.module.global_module.classes['Iterator']
        iter_var = ctx.actual_function.create_variable('iter', iter_class,
                                                       self.translator)
        assert not node in ctx.loop_iterators
        ctx.loop_iterators[node] = iter_var
        args = [iterable]
        arg_types = [iterable_type]
        iter_assign = self.get_method_call(iterable_type, '__iter__', args,
                                           arg_types, [iter_var.ref()], node,
                                           ctx)
        return iter_var, iter_assign

    def _get_next_call(self, iter_var: PythonVar, target_var: PythonVar,
                       node: ast.For,
                       ctx: Context) -> Tuple[PythonVar, List[Stmt]]:

        if target_var.type.name in PRIMITIVES:
            class_name = '__boxed_' + target_var.type.name
            boxed_target_type = ctx.module.global_module.classes[class_name]
        else:
            boxed_target_type = target_var.type
        boxed_target_var = ctx.actual_function.create_variable('target',
            boxed_target_type, self.translator)
        exc_class = ctx.module.global_module.classes['Exception']
        err_var = ctx.actual_function.create_variable('iter_err', exc_class,
                                                      self.translator)
        iter_class = ctx.module.global_module.classes['Iterator']
        args = [iter_var.ref()]
        arg_types = [iter_class]
        targets = [boxed_target_var.ref(node.target, ctx), err_var.ref()]
        next_call = self.get_method_call(iter_class, '__next__', args,
                                         arg_types, targets, node, ctx)

        if target_var.type.name in PRIMITIVES:
            unboxed_target = self.unbox_primitive(
                boxed_target_var.ref(node.target, ctx), target_var.type, None,
                ctx)
        else:
            unboxed_target = boxed_target_var.ref(node.target, ctx)
        target_assign = self.viper.LocalVarAssign(target_var.ref(node.target,
                                                                 ctx),
                                                  unboxed_target,
                                                  self.to_position(node, ctx),
                                                  self.no_info(ctx))
        return err_var, next_call, target_assign

    def _get_iterator_delete(self, iter_var: PythonVar, node: ast.For,
                             ctx: Context) -> List[Stmt]:
        iter_class = ctx.module.global_module.classes['Iterator']
        args = [iter_var.ref()]
        arg_types = [iter_class]
        iter_del = self.get_method_call(iter_class, '__del__', args, arg_types,
                                        [], node, ctx)
        return iter_del

    def _get_havoced_var_type_info(self, nodes: List[ast.AST],
                                   ctx: Context) -> List[Expr]:
        """
        Creates a list of assertions containing type information for all local
        variables written to within the given partial ASTs which already
        existed before.
        To be used to remember type information about arguments/local variables
        which are assigned to in loops and therefore havoced.
        """
        result = []
        collector = AssignCollector()
        for stmt in nodes:
            collector.visit(stmt)
        for name in collector.assigned_vars:
            if name in ctx.var_aliases:
                var = ctx.var_aliases[name]
            else:
                var = ctx.actual_function.get_variable(name)
            if (name in ctx.actual_function.args or
                    (var.writes and not contains_stmt(nodes, var.writes[0]))):
                if var.type.name not in PRIMITIVES:
                    result.append(self.type_check(var.ref(), var.type,
                                                  self.no_position(ctx), ctx))
        return result

    def translate_stmt_For(self, node: ast.For, ctx: Context) -> List[Stmt]:
        iterable_type = self.get_type(node.iter, ctx)
        iterable_stmt, iterable = self.translate_expr(node.iter, ctx)
        iter_var, iter_assign = self._get_iterator(iterable, iterable_type,
                                                   node, ctx)
        target_var = ctx.actual_function.get_variable(node.target.id)

        err_var, next_call, target_assign = self._get_next_call(iter_var,
                                                                target_var,
                                                                node, ctx)
        self.enter_loop_translation(node, ctx, err_var)

        invariant = self._create_for_loop_invariant(iter_var, target_var,
                                                    err_var, iterable,
                                                    iterable_type, node, ctx)
        bodyindex = get_body_start_index(node.body)
        invariant.extend(self._get_havoced_var_type_info(node.body[bodyindex:],
                                                         ctx))

        for expr, aliases in ctx.actual_function.loop_invariants[node]:
            with ctx.additional_aliases(aliases):
                invariant.append(self.translate_contract(expr, ctx))

        body = flatten(
            [self.translate_stmt(stmt, ctx) for stmt in node.body[bodyindex:]])
        body.extend(next_call)
        body.append(target_assign)
        cond = self.viper.EqCmp(err_var.ref(),
                                self.viper.NullLit(self.no_position(ctx),
                                                   self.no_info(ctx)),
                                self.to_position(node, ctx),
                                self.no_info(ctx))
        loop = self.create_while_node(
            ctx, cond, invariant, [], body, node)
        iter_del = self._get_iterator_delete(iter_var, node, ctx)
        self.leave_loop_translation(ctx)
        del ctx.loop_iterators[node]
        return iter_assign + next_call + [target_assign] + loop + iter_del

    def translate_stmt_Assert(self, node: ast.Assert,
                              ctx: Context) -> List[Stmt]:
        stmt, expr = self.translate_expr(node.test, ctx)
        assertion = self.viper.Assert(expr, self.to_position(node, ctx),
                                      self.no_info(ctx))
        return stmt + [assertion]

    def translate_stmt_With(self, node: ast.With, ctx: Context) -> List[Stmt]:
        try_block = None
        for block in ctx.actual_function.try_blocks:
            if block.node is node:
                try_block = block
                break
        assert try_block
        code_var = try_block.get_finally_var(self.translator)
        if code_var.sil_name in ctx.var_aliases:
            code_var = ctx.var_aliases[code_var.sil_name]
        code_var = code_var.ref()
        zero = self.viper.IntLit(0, self.no_position(ctx), self.no_info(ctx))
        # Get context mgr
        ctx_stmt, ctx_mgr = self.translate_expr(try_block.with_item.context_expr,
                                                ctx)
        ctx_type = self.get_type(try_block.with_item.context_expr, ctx)
        enter_method = ctx_type.get_method('__enter__')
        # Create temp var
        enter_res_type = enter_method.type
        with_ctx = ctx.current_function.create_variable('with_ctx',
                                                         ctx_type,
                                                         self.translator)
        try_block.with_var = with_ctx
        ctx_assign = self.viper.LocalVarAssign(with_ctx.ref(), ctx_mgr,
                                               self.no_position(ctx),
                                               self.no_info(ctx))
        enter_res = ctx.current_function.create_variable('enter_res',
                                                         enter_res_type,
                                                         self.translator)
        # Call enter
        enter_call = self.get_method_call(ctx_type, '__enter__',
                                          [with_ctx.ref()],
                                          [ctx_type],
                                          [enter_res.ref(node, ctx)], node, ctx)
        assign = self.viper.LocalVarAssign(code_var, zero,
                                           self.no_position(ctx),
                                           self.no_info(ctx))
        if try_block.with_item.optional_vars:
            as_expr = try_block.with_item.optional_vars
            as_var = ctx.current_function.get_variable(as_expr.id)
            enter_assign = self.viper.LocalVarAssign(as_var.ref(as_expr, ctx),
                                                     enter_res.ref(),
                                                     self.to_position(as_expr,
                                                                      ctx),
                                                     self.no_info(ctx))
            body = [enter_assign, assign]
        else:
            body = [assign]
        body += flatten([self.translate_stmt(stmt, ctx) for stmt in node.body])
        finally_name = ctx.get_label_name(try_block.finally_name)
        goto = self.viper.Goto(finally_name,
                               self.to_position(node, ctx),
                               self.no_info(ctx))
        body.append(goto)
        label_name = ctx.get_label_name(try_block.post_name)
        end_label = self.viper.Label(label_name,
                                     self.to_position(node, ctx),
                                     self.no_info(ctx))
        return ctx_stmt + [ctx_assign] + enter_call + body + [end_label]

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
        code_var = code_var.ref()
        zero = self.viper.IntLit(0, self.no_position(ctx), self.no_info(ctx))
        assign = self.viper.LocalVarAssign(code_var, zero,
                                           self.no_position(ctx),
                                           self.no_info(ctx))
        body = [assign]
        body += flatten([self.translate_stmt(stmt, ctx) for stmt in node.body])
        try_block.handler_aliases = ctx.var_aliases.copy()
        if try_block.else_block:
            else_label = ctx.get_label_name(try_block.else_block.name)
            goto = self.viper.Goto(else_label,
                                   self.to_position(node, ctx),
                                   self.no_info(ctx))
            body.append(goto)
        elif try_block.finally_block:
            finally_name = ctx.get_label_name(try_block.finally_name)
            goto = self.viper.Goto(finally_name,
                                   self.to_position(node, ctx),
                                   self.no_info(ctx))
            body.append(goto)
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
            assign = self.viper.LocalVarAssign(var.ref(node, ctx), expr,
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
            return lhs_stmt + ind_stmt + call
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
        if is_get_ghost_output(node):
            return self.translate_get_ghost_output(node, ctx)
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
            # Translate rhs
            for index in range(len(target.elts)):
                stmt += self.assign_to(target.elts[index], rhs,
                                       index, rhs_type,
                                       node, ctx)
            return stmt
        lhs_stmt = self.assign_to(target, rhs, None, rhs_type, node, ctx)
        return lhs_stmt

    def translate_stmt_While(self, node: ast.While,
                             ctx: Context) -> List[Stmt]:
        self.enter_loop_translation(node, ctx)
        cond_stmt, cond = self.translate_to_bool(node.test, ctx)
        if cond_stmt:
            raise InvalidProgramException(node, 'purity.violated')
        invariants = []
        locals = []
        for expr, aliases in ctx.actual_function.loop_invariants[node]:
            with ctx.additional_aliases(aliases):
                invariants.append(self.translate_contract(expr, ctx))
        bodyindex = get_body_start_index(node.body)
        invariants.extend(self._get_havoced_var_type_info(node.body[bodyindex:],
                                                          ctx))
        body = flatten(
            [self.translate_stmt(stmt, ctx) for stmt in node.body[bodyindex:]])
        loop = self.create_while_node(
            ctx, cond, invariants, locals, body, node)
        self.leave_loop_translation(ctx)
        return loop

    def _translate_return(self, node: ast.Return, ctx: Context) -> List[Stmt]:
        if not node.value:
            return []
        type_ = ctx.actual_function.type
        rhs_stmt, rhs = self.translate_expr(node.value, ctx)
        assign = self.viper.LocalVarAssign(
            ctx.result_var.ref(node, ctx),
            rhs, self.to_position(node, ctx),
            self.no_info(ctx))

        return rhs_stmt + [assign]

    def translate_stmt_Return(self, node: ast.Return,
                              ctx: Context) -> List[Stmt]:
        return_stmts = self._translate_return(node, ctx)
        tries = get_surrounding_try_blocks(ctx.actual_function.try_blocks,
                                           node)
        for try_block in tries:
            if try_block.finally_block or try_block.with_item:
                lhs = try_block.get_finally_var(self.translator).ref()
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
