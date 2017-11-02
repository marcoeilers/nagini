import ast

from nagini_translation.lib.constants import (
    BYTES_TYPE,
    DICT_TYPE,
    END_LABEL,
    INT_TYPE,
    LIST_TYPE,
    MAY_SET_PRED,
    OBJECT_TYPE,
    PRIMITIVES,
    RANGE_TYPE,
    SET_TYPE,
    TUPLE_TYPE,
)
from nagini_translation.lib.program_nodes import (
    GenericType,
    PythonField,
    PythonGlobalVar,
    PythonMethod,
    PythonType,
    PythonVar,
)
from nagini_translation.lib.typedefs import (
    Expr,
    Info,
    Position,
    Stmt,
)
from nagini_translation.lib.util import (
    AssignCollector,
    contains_stmt,
    flatten,
    get_body_indices,
    get_parent_of_type,
    get_surrounding_try_blocks,
    InvalidProgramException,
    is_get_ghost_output,
    UnsupportedException,
)
from nagini_translation.translators.abstract import Context
from nagini_translation.translators.common import CommonTranslator
from typing import List, Optional, Tuple, Union


class StatementTranslator(CommonTranslator):
    def __init__(self, config: 'TranslatorConfig', jvm: 'JVM', source_file: str,
                 type_info: 'TypeInfo', viper_ast: 'ViperAST') -> None:
        super().__init__(config, jvm, source_file, type_info, viper_ast)
        # Keep track of the end and after labels of loops we are currently in.
        self.loops = {}

    def translate_stmt(self, node: ast.AST, ctx: Context) -> List[Stmt]:
        """
        Generic visitor function for translating statements
        """
        method = 'translate_stmt_' + node.__class__.__name__
        visitor = getattr(self, method, self.translate_generic)
        return visitor(node, ctx)

    def _execute_module_statements(self, path, ctx: Context):
        pass

    def translate_stmt_ImportFrom(self, node: ast.ImportFrom, ctx: Context) -> List[Stmt]:
        path = ...

    def translate_stmt_Import(self, node: ast.Import, ctx: Context) -> List[Stmt]:
        pass

    def translate_stmt_FunctionDef(self, node: ast.FunctionDef, ctx: Context) -> List[Stmt]:
        return []

    def translate_stmt_ClassDef(self, node: ast.ClassDef, ctx: Context) -> List[Stmt]:
        pass

    def translate_stmt_Global(self, node: ast.Global, ctx: Context) -> List[Stmt]:
        return []

    def translate_stmt_Delete(self, node: ast.Delete, ctx: Context) -> List[Stmt]:
        result = []
        info = self.no_info(ctx)
        full_perm = self.viper.FullPerm(self.no_position(ctx), info)
        for t in node.targets:
            target = self.get_target(t, ctx)
            if isinstance(target, PythonField):
                pos = self.to_position(t, ctx)
                # assume t is an ast.Attribute
                stmts, receiver = self.translate_expr(t.value, ctx)
                result.extend(stmts)
                rec_type = self.get_type(t.value, ctx)
                python_field = rec_type.get_field(t.attr)
                field = self.viper.Field(python_field.sil_name,
                                         self.translate_type(python_field.type, ctx),
                                         pos, info)
                field_acc = self.viper.FieldAccess(receiver, field, pos, info)
                field_acc_pred = self.viper.FieldAccessPredicate(field_acc, full_perm,
                                                                 pos, info)
                result.append(self.viper.Exhale(field_acc_pred, pos, info))
                may_set = self.get_may_set_predicate(receiver, python_field, ctx, pos)
                result.append(self.viper.Inhale(may_set, pos, info))
            else:
                raise UnsupportedException(node)
        return result


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
        result = self.to_ref(result, ctx)
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
                                   assign_expr: List[Expr],
                                   node: ast.AST,
                                   ctx: Context) -> List[Stmt]:
        """
        Creates the default invariant for for loops using iterators. It's a
        static block of code that's always the same except for possible boxing
        and unboxing, and looks like this:

        .. code-block:: silver
            invariant acc(a.list_acc, 1 / 20)
            invariant acc(iter.list_acc, 1 / 20)
            invariant iter.list_acc == list___sil_seq__(a)
            invariant acc(iter.__iter_index, write)
            invariant acc(iter.__previous, 1 / 20)
            invariant acc(iter.__previous.list_acc, write)
            invariant issubtype(typeof(iter.__previous), list()) && ...
            invariant iter_err == null ==>
                      iter.__iter_index - 1 == list___len__(iter.__previous)
            invariant iter_err != null ==>
                      iter.__iter_index == list___len__(iter.__previous)
            invariant iter.__iter_index >= 0 &&
                      iter.__iter_index <= |iter.list_acc|
            invariant |iter.list_acc| > 0 ==>
                      c == iter.list_acc[iter.__iter_index - 1]
            invariant (if there are multiple loop targets, relations between
                       c and the loop targets, e.g. a == getitem(c, 0) etc.,
                       as given in ``assign_expr``)
            invariant |iter.list_acc| > 0 ==> (c in iter.list_acc)
            invariant iter_err == null ==>
                          iter.__previous.list_acc ==
                          iter.list_acc[..iter.__iter_index - 1]
            invariant |iter.list_acc| > 0 ==>
                      issubtype(typeof(c), list()) && ...
            invariant iter_err != null ==>
                      iter.__previous.list_acc == iter.list_acc
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
        elif iterable_type.name == RANGE_TYPE:
            pass
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
        list_class = ctx.module.global_module.classes[LIST_TYPE]

        previous_type = GenericType(list_class, [target_var.type])
        invariant.append(self.type_check(iter_previous_acc, previous_type, pos,
                                         ctx))

        index_minus_one = self.viper.Sub(iter_index_acc, one, pos, info)
        object_class = ctx.module.global_module.classes[OBJECT_TYPE]

        previous_len = self.get_function_call(list_class, '__len__',
                                              [iter_previous_acc],
                                              [object_class], None, ctx)
        no_error_previous_len_eq = self.viper.EqCmp(index_minus_one,
                                                    previous_len, pos, info)
        error_previous_len_eq = self.viper.EqCmp(iter_index_acc, previous_len,
                                                 pos, info)

        null = self.viper.NullLit(pos, info)

        no_error = self.viper.EqCmp(err_var.ref(), null, pos, info)
        some_error = self.viper.NeCmp(err_var.ref(), null, pos, info)

        invariant.append(self.viper.Implies(no_error, no_error_previous_len_eq,
                                            pos, info))
        invariant.append(self.viper.Implies(some_error, error_previous_len_eq,
                                            pos, info))

        index_nonneg = self.viper.GeCmp(iter_index_acc, zero, pos, info)
        iter_list_len = self.viper.SeqLength(iter_acc, pos, info)

        non_empty_iterator = self.viper.GtCmp(iter_list_len, zero, pos, info)
        empty_iterator = self.viper.EqCmp(iter_list_len, zero, pos, info)

        no_error_implies_non_empty = self.viper.Implies(no_error,
                                                        non_empty_iterator, pos,
                                                        info)
        invariant.append(no_error_implies_non_empty)

        index_le_len = self.viper.LeCmp(iter_index_acc, iter_list_len, pos,
                                        info)
        index_bounds = self.viper.And(index_nonneg, index_le_len, pos, info)
        invariant.append(index_bounds)

        iter_current_index = self.viper.SeqIndex(iter_acc, index_minus_one, pos,
                                                 info)
        boxed_target = target_var.ref()
        if target_var.type.name in PRIMITIVES:
            boxed_target = self.box_primitive(boxed_target, target_var.type,
                                              None, ctx)
            iter_current_index = self.unbox_primitive(iter_current_index,
                                                      target_var.type, None,
                                                      ctx)

        positive_index = self.viper.GtCmp(iter_index_acc, zero, pos, info)
        invariant.append(self.viper.Implies(non_empty_iterator, positive_index,
                                            pos, info))
        current_element_index = self.viper.EqCmp(target_var.ref(),
                                                 iter_current_index, pos, info)
        current_element_contained = self.viper.SeqContains(boxed_target,
                                                           iter_acc, pos, info)
        invariant.append(self.viper.Implies(non_empty_iterator,
                                            current_element_index, pos, info))
        invariant.append(self.viper.Implies(non_empty_iterator,
                                            current_element_contained, pos,
                                            info))

        previous_elements = self.viper.SeqTake(iter_acc, index_minus_one, pos,
                                               info)
        iter_previous_contents = self.viper.EqCmp(previous_list_acc,
                                                  previous_elements, pos, info)
        invariant.append(self.viper.Implies(no_error, iter_previous_contents,
                                            pos, info))

        target_type = self.type_check(target_var.ref(), target_var.type, pos,
                                      ctx)
        invariant.append(self.viper.Implies(non_empty_iterator, target_type,
                                            pos, info))
        # Add information about and permissions for actual loop targets
        for target_info in assign_expr:
            invariant.append(self.viper.Implies(non_empty_iterator, target_info,
                                                pos, info))

        previous_is_all = self.viper.EqCmp(previous_list_acc, iter_acc, pos,
                                           info)
        invariant.append(self.viper.Implies(some_error, previous_is_all, pos,
                                            info))
        invariant.append(self.viper.Implies(empty_iterator, some_error, pos, info))
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
        exc_class = ctx.module.global_module.classes['Exception']
        err_var = ctx.actual_function.create_variable('iter_err', exc_class,
                                                      self.translator)
        iter_class = ctx.module.global_module.classes['Iterator']
        args = [iter_var.ref()]
        arg_types = [iter_class]
        targets = [target_var.ref(node.target, ctx), err_var.ref()]
        next_call = self.get_method_call(iter_class, '__next__', args,
                                         arg_types, targets, node, ctx)
        return err_var, next_call

    def _get_iterator_delete(self, iter_var: PythonVar, node: ast.For,
                             ctx: Context) -> List[Stmt]:
        iter_class = ctx.module.global_module.classes['Iterator']
        args = [iter_var.ref()]
        arg_types = [iter_class]
        iter_del = self.get_method_call(iter_class, '__del__', args, arg_types,
                                        [], node, ctx)
        return iter_del

    def _get_havoced_vars(self, nodes: List[ast.AST],
                          ctx: Context) -> List[PythonVar]:
        """
        Finds all local variables written to within the given partial ASTs which
        already existed before.
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
                result.append(var)
        return result

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
        vars = self._get_havoced_vars(nodes, ctx)
        for var in vars:
            result.append(self.type_check(var.ref(), var.type,
                                          self.no_position(ctx), ctx))
        return result

    def translate_stmt_For(self, node: ast.For, ctx: Context) -> List[Stmt]:
        position = self.to_position(node, ctx)
        info = self.no_info(ctx)
        post_label = ctx.actual_function.get_fresh_name('post_loop')
        end_label = ctx.actual_function.get_fresh_name('loop_end')
        iterable_type = self.get_type(node.iter, ctx)
        iterable_stmt, iterable = self.translate_expr(node.iter, ctx)
        iterable_var = ctx.actual_function.create_variable('iterable', iterable_type,
                                                           self.translator, True)
        iterable_assign = self.viper.LocalVarAssign(iterable_var.ref(), iterable,
                                                    position, info)
        iterable = iterable_var.ref()
        iterable_stmt.append(iterable_assign)
        iter_var, iter_assign = self._get_iterator(iterable, iterable_type,
                                                   node, ctx)
        # Find type of the collection content we're iterating over.
        if iterable_type.name in (LIST_TYPE, DICT_TYPE, SET_TYPE):
            target_type = iterable_type.type_args[0]
        elif iterable_type.name in (RANGE_TYPE, BYTES_TYPE):
            target_type = ctx.module.global_module.classes[INT_TYPE]
        else:
            raise UnsupportedException(node, 'unknown.iterable')

        # Create artificial new variable to store current iteration content.
        target_var = ctx.actual_function.create_variable('loop_target',
                                                         target_type,
                                                         self.translator)

        err_var, next_call = self._get_next_call(iter_var, target_var,
                                                 node, ctx)

        # Assign target_var contents to actual loop target(s).
        assign_stmt, assign_expr = self.assign_to(node.target,
                                                  target_var.ref(),
                                                  None, None, target_type,
                                                  node, ctx)

        self.enter_loop_translation(node, post_label, end_label, ctx, err_var)

        invariant = self._create_for_loop_invariant(iter_var, target_var,
                                                    err_var, iterable,
                                                    iterable_type, assign_expr,
                                                    node, ctx)
        start, end = get_body_indices(node.body)

        # Remember type information about havoced local variables.
        invariant.extend(self._get_havoced_var_type_info(node.body[start:end],
                                                         ctx))

        for expr, aliases in ctx.actual_function.loop_invariants[node]:
            with ctx.additional_aliases(aliases):
                invariant.append(self.translate_contract(expr, ctx))

        body = flatten(
            [self.translate_stmt(stmt, ctx) for stmt in node.body[start:end]])
        # Label for continue to jump to
        body.append(self.viper.Label(end_label, position, info))
        body.extend(next_call)
        body.extend(assign_stmt)
        cond = self.viper.EqCmp(err_var.ref(),
                                self.viper.NullLit(position, info),
                                position, info)
        loop = self.create_while_node(
            ctx, cond, invariant, [], body, node)
        iter_del = self._get_iterator_delete(iter_var, node, ctx)
        self.leave_loop_translation(ctx)
        del ctx.loop_iterators[node]
        result = (iterable_stmt + iter_assign + next_call + assign_stmt +
                  loop + iter_del)
        result += self._set_result_none(ctx)
        if node.orelse:
            translated_block = flatten([self.translate_stmt(stmt, ctx) for stmt
                                        in node.orelse])
            result += translated_block
        # Label for break to jump to
        result.append(self.viper.Label(post_label, position, info))
        result += self._set_result_none(ctx)
        return result

    def translate_stmt_Assert(self, node: ast.Assert,
                              ctx: Context) -> List[Stmt]:
        stmt, expr = self.translate_expr(node.test, ctx, self.viper.Bool)
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
            define_var = self.set_var_defined(as_var, self.no_position(ctx),
                                              self.no_info(ctx))
            body = [enter_assign, define_var, assign]
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
        raised = self.get_target(node.exc, ctx)
        if (not isinstance(node.exc, ast.Call) and
                isinstance(raised, PythonType)):
            # The argument of raise is a class; call constructor with no
            # arguments.
            args = []
            init = raised.get_method('__init__')
            if init:
                _, args, _ = self.translate_args(init, [], [], node.exc, ctx,
                                                 True)
            stmt, exception = self.translate_constructor_call(raised, node.exc,
                                                              args, [], ctx)
        else:
            stmt, exception = self.translate_expr(node.exc, ctx)
        position = self.to_position(node, ctx)
        if node.cause:
            cause_stmt, cause = self.translate_expr(node.cause, ctx)
            stmt += cause_stmt
        assignment = self.viper.LocalVarAssign(var, exception, position,
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
        elif isinstance(node.value, (ast.Str, ast.Ellipsis)):
            # Docstring or ellipsis, just skip.
            return []
        else:
            raise UnsupportedException(node)

    def translate_stmt_If(self, node: ast.If, ctx: Context) -> List[Stmt]:
        cond_stmt, cond = self.translate_expr(node.test, ctx,
                                              target_type=self.viper.Bool)
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
                  rhs_end: Optional[Expr],
                  rhs_type: PythonType,
                  node: ast.AST, ctx: Context) -> Tuple[List[Stmt], List[Expr]]:
        """
        Assigns the given expression ``rhs`` to the target given in ``lhs``.
        If ``rhs_index`` is set, will only assign the element of ``rhs`` at
        this index; if ``rhs_end`` is also set, will assign a list containing
        the given range of elements to ``lhs`` (assuming ``lhs`` is of type
        ast.Starred).

        In addition to assignment statements, returns a list of assertions
        which are known to hold after the asignment, to be used in loop
        invariants.
        """
        position = self.to_position(node, ctx)
        info = self.no_info(ctx)
        if isinstance(lhs, ast.Starred):
            return self._assign_to_starred(lhs, rhs, rhs_index, rhs_end,
                                           rhs_type, node, ctx)
        if rhs_index is not None:
            rhs_lit = self.viper.IntLit(rhs_index, position, info)
            args = [rhs, rhs_lit]
            arg_types = [rhs_type, None]
            rhs = self.get_function_call(rhs_type, '__getitem__', args,
                                         arg_types, node, ctx)
            if rhs_type.name == TUPLE_TYPE and rhs_type.exact_length:
                rhs_type = rhs_type.type_args[rhs_index]
            else:
                rhs_type = rhs_type.type_args[0]
        if isinstance(lhs, ast.Tuple):
            return self._assign_to_tuple(lhs, rhs, rhs_type, node, ctx)

        return self._assign_single_value(lhs, rhs, rhs_type, node, ctx)

    def _assign_single_value(self, lhs: ast.AST, rhs: Expr,
                             rhs_type: PythonType, node: ast.AST,
                             ctx: Context) -> Tuple[List[Stmt], List[Expr]]:
        position = self.to_position(node, ctx)
        info = self.no_info(ctx)

        if isinstance(lhs, ast.Subscript):
            return self._assign_with_subscript(lhs, rhs, node, ctx)

        target = self.get_target(lhs, ctx)
        if isinstance(target, PythonMethod):
            # We're assigning to a property, so we have to call the method representing
            # the property setter.
            assert isinstance(lhs, ast.Attribute)
            assert target.setter
            arg_stmt, arg = self.translate_expr(lhs.value, ctx)
            call = self.create_method_call_node(ctx, target.setter.sil_name, [arg, rhs],
                                                [], position, info, target.setter, lhs)
            getter_type = self.translate_type(target.type, ctx)
            self_arg = self.viper.LocalVarDecl('self', self.viper.Ref, position, info)
            getter = self.viper.FuncApp(target.sil_name, [arg], position, info,
                                        getter_type, [self_arg])
            getter_equal = self.viper.EqCmp(getter, rhs, position, info)
            return arg_stmt + call, [getter_equal]
        lhs_stmt, var = self.translate_expr(lhs, ctx)
        before_assign = []
        after_assign = []
        if isinstance(target, PythonGlobalVar):
            if target.is_final:
                def assignment(lhs, rhs, pos, info):
                    eq = self.viper.EqCmp(lhs, rhs, pos, info)
                    return self.viper.Inhale(eq, position, info)
                after_assign.append(self.set_var_defined(target, position, info))
            else:
                assignment = self.viper.FieldAssign
                after_assign.append(self.set_var_defined(target, position, info))
        elif isinstance(lhs, ast.Name):
            assignment = self.viper.LocalVarAssign
            if self.is_local_variable(target, ctx):
                after_assign.append(self.set_var_defined(target, position, info))
        else:
            assignment = self.viper.FieldAssign
            permission_inhale = self.create_new_field_permission(var, target,
                                                                 position, info, ctx)
            before_assign.append(permission_inhale)
        assign_stmt = assignment(var, rhs, position, info)
        assign_val = self.viper.EqCmp(var, rhs, position, info)
        return lhs_stmt + before_assign + [assign_stmt] + after_assign, [assign_val]

    def create_new_field_permission(self, field_acc: Expr, target: PythonField,
                                    position: Position, info: Info, ctx: Context) -> Stmt:
        """
        Creates a statement that checks if the receiver of the given field access is the
        self-parameter of the current method and there is a permission to create the
        given field. If this is the case, it will exhale the permission to create the
        field, and inhale a write permission to the field instead.
        To be used for field writes in constructors.
        """
        receiver = field_acc.rcv()

        no_perm = self.viper.NoPerm(position, info)
        id_value = self._get_string_value(target.actual_field.sil_name)
        id = self.viper.IntLit(id_value, position, info)
        may_set_pred = self.viper.PredicateAccess([receiver, id], MAY_SET_PRED, position,
                                                  info)
        may_set_perm = self.viper.CurrentPerm(may_set_pred, position, info)
        may_set = self.viper.PermGtCmp(may_set_perm, no_perm, position, info)
        full_perm = self.viper.FullPerm(position, info)
        all_may_set = self.viper.PredicateAccessPredicate(may_set_pred, full_perm,
                                                          position, info)
        field_perm = self.viper.FieldAccessPredicate(field_acc, full_perm, position, info)
        exhale = self.viper.Exhale(all_may_set, position, info)
        inhale = self.viper.Inhale(field_perm, position, info)
        in_ex = self.translate_block([exhale, inhale], position, info)
        empty_block = self.translate_block([], position, info)
        inner_if = self.viper.If(may_set, in_ex, empty_block, position, info)
        return inner_if

    def _assign_with_subscript(self, lhs: ast.Tuple, rhs: Expr, node: ast.AST,
                               ctx: Context) -> Tuple[List[Stmt], List[Expr]]:
        # Special treatment for subscript; instead of an assignment, we
        # need to call a setitem method.
        if not isinstance(node.targets[0].slice, ast.Index):
            raise UnsupportedException(node, 'assignment to slice')
        position = self.to_position(node, ctx)
        target_cls = self.get_type(lhs.value, ctx)
        lhs_stmt, target = self.translate_expr(lhs.value, ctx)
        ind_stmt, index = self.translate_expr(lhs.slice.value, ctx,
                                              target_type=self.viper.Int)
        args = [target, index, rhs]
        arg_types = [None, None, None]
        stmt = self.get_method_call(target_cls, '__setitem__', args,
                                    arg_types, [], node, ctx)
        # The respective assertion states that getitem with the given index
        # now has the assigned value.
        item = self.get_function_call(
            target_cls, '__getitem__', [target, index], [None, None], node, ctx)
        val = self.viper.EqCmp(item, rhs, position, self.no_info(ctx))
        return lhs_stmt + ind_stmt + stmt, [val]

    def _assign_to_tuple(self, lhs: ast.Tuple, rhs: Expr, rhs_type: PythonType,
                         node: ast.AST,
                         ctx: Context) -> Tuple[List[Stmt], List[Expr]]:
        position = self.to_position(node, ctx)
        info = self.no_info(ctx)

        no_after_starred = 0
        next = 0
        stmt_result = []
        val_result = []
        # Need to find out how many other receivers come after a starred
        # expression (if any) to calculate the last index that should be
        # assigned to the starred expression.
        for index, e in enumerate(lhs.elts):
            if isinstance(e, ast.Starred):
                no_after_starred = len(lhs.elts) - index - 1
                next = -no_after_starred
            else:
                next = next + 1
            next_expr = self.viper.IntLit(next, position, info)
            if next <= 0:
                # Calculate next index dynamically as len(rhs) + next
                # because len(rhs) might be unknown statically.
                len_expr = self.get_function_call(rhs_type, '__len__',
                                                  [rhs], [None], node, ctx)
                next_expr = self.viper.Add(len_expr, next_expr, position,
                                           info)

            stmt, val = self.assign_to(e, rhs, index, next_expr,
                                       rhs_type, node, ctx)
            stmt_result += stmt
            val_result += val
        return stmt_result, val_result

    def _assign_to_starred(self, lhs: ast.Starred, rhs: Expr,
                           rhs_index: Optional[int], rhs_end: Optional[Expr],
                           rhs_type: PythonType, node: ast.AST,
                           ctx: Context) -> Tuple[List[Stmt], List[Expr]]:
        assert rhs_index is not None and rhs_end
        position = self.to_position(node, ctx)
        info = self.no_info(ctx)

        rhs_lit = self.viper.IntLit(rhs_index, position, info)
        list_class = ctx.module.global_module.classes[LIST_TYPE]
        stmt, res_var = self.translate_expr(lhs.value, ctx)

        # Create a new list and assign it to starred variable
        constr_call = self.get_method_call(list_class, '__init__', [], [],
                                           [res_var], node, ctx)
        stmt += constr_call
        # Inhale the type of the newly created list (including type arguments)
        list_type = self.get_type(lhs.value, ctx)
        position = self.to_position(node, ctx)
        stmt.append(
            self.viper.Inhale(self.type_check(res_var,
                                              list_type, position, ctx),
                              position, info))
        # Set list contents to segment of rhs from rhs_index until rhs_end
        seq = self.get_function_call(rhs_type, '__sil_seq__',
                                     [rhs], [None], node, ctx)

        seq_until = self.viper.SeqTake(seq, rhs_end, position, info)
        seq_from = self.viper.SeqDrop(seq_until, rhs_lit, position, info)
        list_field = self.viper.Field('list_acc',
                                      self.viper.SeqType(self.viper.Ref),
                                      self.no_position(ctx), info)
        list_field_acc = self.viper.FieldAccess(res_var, list_field,
                                                position, info)
        # Also return new list permission...
        val = []
        full = self.viper.FullPerm(position, info)
        list_perm = self.viper.FieldAccessPredicate(list_field_acc,
                                                    full, position,
                                                    info)
        val.append(list_perm)
        list_type = self.type_check(res_var, list_type, position, ctx)
        val.append(list_type)
        assign_stmt = self.viper.FieldAssign(list_field_acc, seq_from, position,
                                             info)
        after_assign = []
        target = self.get_target(lhs.value, ctx)
        if self.is_local_variable(target, ctx):
            after_assign.append(self.set_var_defined(target, position, info))
        # ... and information about the list contents
        assign_val = self.viper.EqCmp(list_field_acc, seq_from, position, info)
        return stmt + [assign_stmt] + after_assign, val + [assign_val]

    def translate_stmt_Assign(self, node: ast.Assign,
                              ctx: Context) -> List[Stmt]:
        if is_get_ghost_output(node):
            return self.translate_get_ghost_output(node, ctx)
        rhs_type = self.get_type(node.value, ctx)
        rhs_stmt, rhs = self.translate_expr(node.value, ctx)
        assign_stmts = []
        for target in node.targets:
            target_stmt, _ = self.assign_to(target, rhs, None, None, rhs_type,
                                            node, ctx)
            assign_stmts += target_stmt
        return rhs_stmt + assign_stmts

    def translate_stmt_While(self, node: ast.While,
                             ctx: Context) -> List[Stmt]:
        post_label = ctx.actual_function.get_fresh_name('post_loop')
        end_label = ctx.actual_function.get_fresh_name('loop_end')
        self.enter_loop_translation(node, post_label, end_label, ctx)
        cond_stmt, cond = self.translate_expr(node.test, ctx,
                                              target_type=self.viper.Bool)
        if cond_stmt:
            raise InvalidProgramException(node, 'purity.violated')
        invariants = []
        locals = []
        for expr, aliases in ctx.actual_function.loop_invariants[node]:
            with ctx.additional_aliases(aliases):
                invariants.append(self.translate_contract(expr, ctx))
        start, end = get_body_indices(node.body)
        var_types = self._get_havoced_var_type_info(node.body[start:end], ctx)
        invariants = var_types + invariants
        body = flatten(
            [self.translate_stmt(stmt, ctx) for stmt in node.body[start:end]])
        body.append(self.viper.Label(end_label, self.to_position(node, ctx),
                                     self.no_info(ctx)))
        loop = self.create_while_node(
            ctx, cond, invariants, locals, body, node)
        self.leave_loop_translation(ctx)
        loop += self._set_result_none(ctx)
        if node.orelse:
            translated_block = flatten([self.translate_stmt(stmt, ctx) for stmt
                                        in node.orelse])
            loop += translated_block
        loop.append(self.viper.Label(post_label, self.to_position(node, ctx),
                    self.no_info(ctx)))
        loop += self._set_result_none(ctx)
        return loop

    def enter_loop_translation(
            self, node: Union[ast.While, ast.For], post_label: str,
            end_label: str, ctx: Context,
            err_var: PythonVar = None) -> None:
        self.loops[node] = (post_label, end_label)
        super().enter_loop_translation(node, ctx, err_var)

    def leave_loop_translation(self, ctx: Context) -> None:
        super().leave_loop_translation(ctx)

    def _set_result_none(self, ctx: Context) -> List[Stmt]:
        """
        Sets the return variable of the current function to null (the default
        return variable), to be used after loops which may havoc the result
        variable (if there is a return within the loop body).
        """
        result = []
        null = self.viper.NullLit(self.no_position(ctx), self.no_info(ctx))
        if ctx.actual_function.type:
            result_none = self.viper.LocalVarAssign(
                ctx.actual_function.result.ref(),
                null, self.no_position(ctx),
                self.no_info(ctx))
            result.append(result_none)
        # Do the same for the error variable
        if ctx.actual_function.declared_exceptions:
            error_none = self.viper.LocalVarAssign(
                ctx.actual_function.error_var.ref(),
                null, self.no_position(ctx), self.no_info(ctx))
            result.append(error_none)
        return result

    def translate_stmt_Break(self, node: ast.Break, ctx: Context) -> List[Stmt]:
        loop = get_parent_of_type(node, (ast.While, ast.For))
        loop_and_label = self.loops[loop]
        result = self.viper.Goto(loop_and_label[0], self.to_position(node, ctx),
                                 self.no_info(ctx))
        return [result]

    def translate_stmt_Continue(self, node: ast.Continue,
                                ctx: Context) -> List[Stmt]:

        parent = node
        # Find the loop surrounding this node.
        while not isinstance(parent._parent, (ast.While, ast.For)):
            # If we find, on the way, that we're in a try block
            if isinstance(parent._parent, ast.Try):
                # namely, in the finally branch
                if parent in parent._parent.finalbody:
                    # this is illegal in Python any mypy doesn't check it.
                    raise InvalidProgramException(node, 'continue.in.finally')
            else:
                parent = parent._parent

        loop = parent._parent
        loop_and_label = self.loops[loop]
        result = self.viper.Goto(loop_and_label[1], self.to_position(node, ctx),
                                 self.no_info(ctx))
        return [result]

    def _translate_return(self, node: ast.Return, ctx: Context) -> List[Stmt]:
        if not node.value:
            return []
        type_ = ctx.actual_function.type
        rhs_stmt, rhs = self.translate_expr(node.value, ctx)
        if not ctx.result_var:
            raise InvalidProgramException(node, 'invalid.return')
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
