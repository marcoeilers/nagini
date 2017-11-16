import ast
import inspect

from nagini_translation.lib.constants import (
    BOOL_TYPE,
    BOXED_PRIMITIVES,
    BYTES_TYPE,
    CHECK_DEFINED_FUNC,
    DICT_TYPE,
    END_LABEL,
    FUNCTION_DOMAIN_NAME,
    INT_TYPE,
    CALLABLE_TYPE,
    LIST_TYPE,
    OPERATOR_FUNCTIONS,
    PRIMITIVE_INT_TYPE,
    SET_TYPE,
    STRING_TYPE,
    TUPLE_TYPE,
)
from nagini_translation.lib.errors import rules
from nagini_translation.lib.program_nodes import (
    GenericType,
    PythonClass,
    PythonField,
    PythonGlobalVar,
    PythonIOExistentialVar,
    PythonMethod,
    PythonModule,
    PythonTryBlock,
    PythonType,
    PythonVar,
)
from nagini_translation.lib.typedefs import (
    Expr,
    Position,
    Stmt,
    StmtsAndExpr,
)
from nagini_translation.lib.util import (
    construct_lambda_prefix,
    get_func_name,
    get_surrounding_try_blocks,
    InvalidProgramException,
    join_three_expressions,
    join_expressions,
    UnsupportedException,
)
from nagini_translation.translators.abstract import Context
from nagini_translation.translators.common import CommonTranslator
from typing import List, Optional, Union


# Maps function names to bools; caches which functions take an additonal argument
# encoding if impure assertions are allowed or not.
TAKES_IMPURE_ARGS = {}


class ExpressionTranslator(CommonTranslator):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # TODO: Update all code to use this flag.
        self._is_expression = False
        self._target_type = None
        self._primitive_operations = {
            ast.Add: self.viper.Add,
            ast.Sub: self.viper.Sub,
            ast.Mult: self.viper.Mul,
            ast.FloorDiv: self.viper.Div,
            ast.Mod: self.viper.Mod,
            ast.Is: self.viper.EqCmp,
            ast.Eq: self.viper.EqCmp,
            ast.NotEq: self.viper.NeCmp,
            ast.IsNot: self.viper.NeCmp,
            ast.Lt: self.viper.LtCmp,
            ast.LtE: self.viper.LeCmp,
            ast.Gt: self.viper.GtCmp,
            ast.GtE: self.viper.GeCmp,
        }

    def translate_expr(self, node: ast.AST, ctx: Context,
                       target_type = None,
                       impure: bool = False) -> StmtsAndExpr:
        """
        Generic visitor function for translating an expression.

        :param target_type:
            The Silver type this expression should be translated to, defaults
            to Ref if no arguments is provided.
        :param impure:
            Indicates if ``node`` may be translated to an impure assertion. If False,
            translating a predicate or field permission will result in an
            InvalidProgramException.
        """

        if not target_type:
            target_type = self.viper.Ref
        old_target = self._target_type
        self._target_type = target_type
        stmt, result = self._translate_only(node, ctx, impure)

        if target_type != result.typ():
            result = self.convert_to_type(result, target_type, ctx, node)

        self._target_type = old_target
        return stmt, result

    def _translate_only(self, node: ast.AST, ctx: Context, impure=False):
        """
        Translates an expression, but does so without changing the expression's type in
        any way.
        """
        method = 'translate_' + node.__class__.__name__
        visitor = getattr(self, method, self.translate_generic)
        if method in TAKES_IMPURE_ARGS:
            impure_arg = TAKES_IMPURE_ARGS[method]
        else:
            sig = inspect.signature(visitor)
            impure_arg = len(sig.parameters) > 2
            TAKES_IMPURE_ARGS[method] = impure_arg
        if impure_arg:
            stmt, result = visitor(node, ctx, impure)
        else:
            stmt, result = visitor(node, ctx)
        return stmt, result

    def translate_Return(self, node: ast.Return, ctx: Context,
                         impure=False) -> StmtsAndExpr:
        return self.translate_expr(node.value, ctx, impure=impure, target_type=self._target_type)

    def translate_ListComp(self, node: ast.ListComp, ctx: Context) -> StmtsAndExpr:
        if len(node.generators) != 1:
            raise UnsupportedException(node, 'Multiple generators in list comprehension.')
        if node.generators[0].ifs:
            raise UnsupportedException(node, 'Filter in list comprehension.')
        list_class = ctx.module.global_module.classes['list']
        name = construct_lambda_prefix(node.lineno, node.col_offset)
        target = node.generators[0].target
        local_name = name + '$' + target.id
        element_var = ctx.actual_function.special_vars[local_name]
        ctx.set_alias(target.id, element_var)
        body_stmt, body = self.translate_expr(node.elt, ctx)
        result_type = self.get_type(node.elt, ctx)
        list_type = GenericType(list_class, [result_type])
        if body_stmt:
            raise InvalidProgramException(node, 'impure.list.comprehension.body')
        ctx.remove_alias(target.id)
        result_var = ctx.actual_function.create_variable('listcomp', list_type,
                                                         self.translator)
        stmt = self._create_list_comp_inhale(result_var, list_type, element_var,
                                             body, node, ctx)
        return stmt, result_var.ref()

    def _create_list_comp_inhale(self, result_var: PythonVar, list_type: PythonType,
                                 element_var: PythonVar, body: Expr, node: ast.ListComp,
                                 ctx: Context) -> List[Stmt]:
        # Create an inhale of the following form:
        # Inhale issubtype(typeof(result), list(result_type)) && acc(result.list_acc) &&
        # len(result) == |iter.__sil_seq__()| &&
        # forall 0 <= i < len(result) :: result.list_acc[i] ==
        #                                (let e == iter.__sil_seq__()[i] in body)
        position = self.to_position(node, ctx)
        info = self.no_info(ctx)
        list_class = ctx.module.global_module.classes['list']
        type_check = self.type_check(result_var.ref(), list_type, position, ctx, False)
        list_acc_field = self.viper.Field('list_acc', self.viper.SeqType(self.viper.Ref),
                                          position, info)
        field_acc = self.viper.FieldAccess(result_var.ref(), list_acc_field, position,
                                           info)
        acc_pred = self.viper.FieldAccessPredicate(field_acc,
                                                   self.viper.FullPerm(position, info),
                                                   position, info)
        type_and_perm = self.viper.And(type_check, acc_pred, position, info)
        result_len = self.get_function_call(list_class, '__len__', [result_var.ref()],
                                            [None], node, ctx)
        iter_stmt, iter = self.translate_expr(node.generators[0].iter, ctx)
        iter_type = self.get_type(node.generators[0].iter, ctx)
        sil_seq = self.get_function_call(iter_type.cls, '__sil_seq__', [iter], [None],
                                         node, ctx)
        seq_len = self.viper.SeqLength(sil_seq, position, info)
        len_equal = self.viper.EqCmp(self.to_int(result_len, ctx), seq_len, position,
                                     info)
        int_class = ctx.module.global_module.classes[PRIMITIVE_INT_TYPE]
        index_var = ctx.actual_function.create_variable('i', int_class, self.translator,
                                                        False)
        index_positive = self.viper.GeCmp(index_var.ref(),
                                          self.viper.IntLit(0, position, info),
                                          position, info)
        index_lt_len = self.viper.LtCmp(index_var.ref(), seq_len, position, info)
        index_in_bounds = self.viper.And(index_positive, index_lt_len, position, info)
        value_i = self.viper.SeqIndex(field_acc, index_var.ref(), position, info)
        sil_seq_i = self.get_function_call(iter_type.cls, '__getitem__',
                                           [iter, index_var.ref()], [None, None],
                                           node, ctx)

        let = self.viper.Let(element_var.decl, sil_seq_i, body, position, info)
        value = self.viper.EqCmp(value_i, let, position, info)
        trigger = self.viper.Trigger([value_i], position, info)
        value_in_bounds = self.viper.Implies(index_in_bounds, value, position, info)
        values = self.viper.Forall([index_var.decl], [trigger], value_in_bounds, position,
                                   info)
        contents = self.viper.And(len_equal, values, position, info)
        all = self.viper.And(type_and_perm, contents, position, info)
        inhale = self.viper.Inhale(all, position, info)
        return iter_stmt + [inhale]


    def translate_Num(self, node: ast.Num, ctx: Context) -> StmtsAndExpr:
        lit = self.viper.IntLit(node.n, self.to_position(node, ctx),
                                self.no_info(ctx))
        int_class = ctx.module.global_module.classes[PRIMITIVE_INT_TYPE]
        boxed_lit = self.get_function_call(int_class, '__box__', [lit],
                                           [None], node, ctx)
        return ([], boxed_lit)

    def translate_Dict(self, node: ast.Dict, ctx: Context) -> StmtsAndExpr:
        args = []
        res_var = ctx.current_function.create_variable('dict',
            ctx.module.global_module.classes[DICT_TYPE], self.translator)
        dict_class = ctx.module.global_module.classes[DICT_TYPE]
        arg_types = []
        constr_call = self.get_method_call(dict_class, '__init__', [],
                                           [], [res_var.ref()], node, ctx)
        stmt = constr_call
        # Inhale the type of the newly created dict (including type arguments)
        dict_type = self.get_type(node, ctx)
        position = self.to_position(node, ctx)
        stmt.append(self.viper.Inhale(self.type_check(res_var.ref(node, ctx),
                                                      dict_type, position, ctx),
                                      position, self.no_info(ctx)))
        for key, val in zip(node.keys, node.values):
            key_stmt, key_val = self.translate_expr(key, ctx)
            key_type = self.get_type(key, ctx)
            val_stmt, val_val = self.translate_expr(val, ctx)
            val_type = self.get_type(val, ctx)
            args = [res_var.ref(), key_val, val_val]
            arg_types = [None, key_type, val_type]
            append_call = self.get_method_call(dict_class, '__setitem__', args,
                                               arg_types, [], node, ctx)
            stmt += key_stmt + val_stmt + append_call
        return stmt, res_var.ref(node, ctx)

    def translate_Set(self, node: ast.Set, ctx: Context) -> StmtsAndExpr:
        set_class = ctx.module.global_module.classes[SET_TYPE]
        res_var = ctx.current_function.create_variable(SET_TYPE,
            set_class, self.translator)
        constr_call = self.get_method_call(set_class, '__init__', [], [],
                                           [res_var.ref()], node, ctx)
        stmt = constr_call
        # Inhale the type of the newly created set (including type arguments)
        set_type = self.get_type(node, ctx)
        position = self.to_position(node, ctx)
        stmt.append(self.viper.Inhale(self.type_check(res_var.ref(node, ctx),
                                                      set_type, position, ctx),
                                      position, self.no_info(ctx)))
        for el in node.elts:
            el_stmt, el_val = self.translate_expr(el, ctx)
            el_type = self.get_type(el, ctx)
            args = [res_var.ref(), el_val]
            arg_types = [None, el_type]
            append_call = self.get_method_call(set_class, 'add', args,
                                               arg_types, [], node, ctx)
            stmt += el_stmt + append_call
        return stmt, res_var.ref(node, ctx)

    def translate_List(self, node: ast.List, ctx: Context) -> StmtsAndExpr:
        list_class = ctx.module.global_module.classes[LIST_TYPE]
        res_var = ctx.current_function.create_variable(LIST_TYPE,
            list_class, self.translator)
        targets = [res_var.ref()]

        constr_call = self.get_method_call(list_class, '__init__', [], [],
                                           [res_var.ref()], node, ctx)
        stmt = constr_call
        # Inhale the type of the newly created list (including type arguments)
        list_type = self.get_type(node, ctx)
        position = self.to_position(node, ctx)
        stmt.append(self.viper.Inhale(self.type_check(res_var.ref(node, ctx),
                                                      list_type, position, ctx),
                                      position, self.no_info(ctx)))
        for element in node.elts:
            el_stmt, el = self.translate_expr(element, ctx)
            el_type = self.get_type(element, ctx)
            args = [res_var.ref(), el]
            arg_types = [None, el_type]
            append_call = self.get_method_call(list_class, 'append', args,
                                               arg_types, [], node, ctx)
            stmt += el_stmt + append_call
        return stmt, res_var.ref(node, ctx)

    def translate_Str(self, node: ast.Str, ctx: Context) -> StmtsAndExpr:
        length = len(node.s)
        length_arg = self.viper.IntLit(length, self.no_position(ctx),
                                       self.no_info(ctx))
        val_arg = self.viper.IntLit(self._get_string_value(node.s),
                                    self.no_position(ctx), self.no_info(ctx))
        args = [length_arg, val_arg]
        arg_types = [None, None]
        str_type = ctx.module.global_module.classes[STRING_TYPE]
        func_name = '__create__'
        call = self.get_function_call(str_type, func_name, args, arg_types,
                                      node, ctx)
        return [], call

    def translate_Bytes(self, node: ast.Bytes, ctx: Context) -> StmtsAndExpr:
        elems = []
        for c in node.s:
            lit = self.viper.IntLit(c, self.to_position(node, ctx),
                                    self.no_info(ctx))
            elems.append(self.to_ref(lit, ctx))
        if elems:
            seq = self.viper.ExplicitSeq(elems, self.to_position(node, ctx),
                                         self.no_info(ctx))
        else:
            seq = self.viper.EmptySeq(self.viper.Ref,
                                      self.to_position(node, ctx),
                                      self.no_info(ctx))
        bytes_class = ctx.module.global_module.classes[BYTES_TYPE]
        args = [seq, self.get_fresh_int_lit(ctx)]
        result = self.get_function_call(bytes_class, '__create__', args,
                                        [None, None], node, ctx)
        return [], result

    def translate_Tuple(self, node: ast.Tuple, ctx: Context) -> StmtsAndExpr:
        position = self.to_position(node, ctx)
        info = self.no_info(ctx)
        stmts = []
        vals = []
        val_types = []
        for el in node.elts:
            el_stmt, el_val = self.translate_expr(el, ctx)
            stmts += el_stmt
            vals.append(el_val)
            val_types.append(self.get_type(el, ctx))
        call = self.create_tuple(vals, val_types, node, ctx)
        return stmts, call

    def create_tuple(self, vals: List[Expr], val_types: List[PythonType],
                     node: ast.AST, ctx: Context) -> Expr:
        """
        Creates a tuple containing the given values.
        """
        tuple_class = ctx.module.global_module.classes[TUPLE_TYPE]
        type_class = ctx.module.global_module.classes['type']
        func_name = '__create' + str(len(vals)) + '__'
        types = [self.get_tuple_type_arg(v, t, node, ctx)
                 for (t, v) in zip(val_types, vals)]
        args = vals + types
        # Also add a running integer s.t. other tuples with same contents are
        # not reference-identical (except for empty tuples).
        if args:
            args.append(self.get_fresh_int_lit(ctx))
        arg_types = [None] * len(args)
        call = self.get_function_call(tuple_class, func_name, args, arg_types,
                                      node, ctx)
        return call

    def translate_Subscript(self, node: ast.Subscript,
                            ctx: Context) -> StmtsAndExpr:
        target_type = self.get_type(node.value, ctx)
        target_stmt, target = self.translate_expr(node.value, ctx,
                                                  target_type=self.viper.Ref)
        if not isinstance(node.slice, ast.Index):
            return self._translate_slice_subscript(node, target, target_type,
                                                   target_stmt, ctx)

        index_stmt, index = self.translate_expr(node.slice.value, ctx,
                                                target_type=self.viper.Ref)
        index_type = self.get_type(node.slice.value, ctx)
        args = [target, index]
        arg_types = [target_type, index_type]
        call = self.get_function_call(target_type, '__getitem__', args,
                                      arg_types, node, ctx)
        result = call
        result_type = self.get_type(node, ctx)
        return target_stmt + index_stmt, result

    def _translate_slice_subscript(self, node: ast.Subscript, target: Expr,
                                   target_type: PythonType,
                                   target_stmt: List[Stmt],
                                   ctx: Context) -> StmtsAndExpr:
        if node.slice.step:
            raise UnsupportedException(node, 'slice step')
        slice_class = ctx.module.global_module.classes['slice']
        null = self.viper.NullLit(self.no_position(ctx), self.no_info(ctx))
        start = stop = null
        start_stmt = stop_stmt = []
        if node.slice.lower:
            start_stmt, start = self.translate_expr(node.slice.lower, ctx)
        if node.slice.upper:
            stop_stmt, stop = self.translate_expr(node.slice.upper, ctx)
        slice = self.get_function_call(slice_class, '__create__',
                                       [start, stop], [None, None],
                                       node.slice, ctx)
        args = [target, slice]
        stmt = target_stmt + start_stmt + stop_stmt
        getitem = target_type.get_func_or_method('__getitem_slice__')
        if not getitem.pure:
            result_var = ctx.actual_function.create_variable(
                'slice_res', target_type, self.translator)
            call = self.get_method_call(target_type, '__getitem_slice__',
                                        args, [None, None],
                                        [result_var.ref()], node, ctx)
            stmt += call
            return stmt, result_var.ref()
        else:
            call = self.get_function_call(target_type, '__getitem_slice__',
                                          args, [None, None], node, ctx)
            return stmt, call

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
            end_label = ctx.get_label_name(END_LABEL)
            goto_end = self.viper.Goto(end_label, position, self.no_info(ctx))
            if ctx.actual_function.declared_exceptions:
                assignerror = self.viper.LocalVarAssign(err_var, var, position,
                                                        self.no_info(ctx))
                uncaught_option = self.translate_block([assignerror, goto_end],
                                                       position,
                                                       self.no_info(ctx))
            else:
                error_string = '"method raises no exceptions"'
                error_pos = self.to_position(call, ctx, error_string)
                exhale_false = self.viper.Exhale(
                    self.viper.FalseLit(error_pos, self.no_info(ctx)),
                    error_pos,
                    self.no_info(ctx))
                uncaught_option = self.translate_block([exhale_false, goto_end],
                                                       position,
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
            if try_.finally_block or try_.with_item:
                # Propagate return value
                var_next = try_.get_finally_var(self.translator)
                if var_next.sil_name in ctx.var_aliases:
                    var_next = ctx.var_aliases[var_next.sil_name]
                number_two = self.viper.IntLit(2, self.no_position(ctx),
                                               self.no_info(ctx))
                next_assign = self.viper.LocalVarAssign(var_next.ref(),
                                                        number_two,
                                                        self.no_position(ctx),
                                                        self.no_info(ctx))
                # Goto finally block
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

    def translate_to_bool(self, node: ast.AST, ctx: Context,
                          expression: bool = False) -> StmtsAndExpr:
        """
        Translates node as a normal expression, then applies Python's auto-
        conversion to a boolean value (using the __bool__ function)
        """
        stmt, res = self.translate_expr(node, ctx, expression)
        type = self.get_type(node, ctx)
        bool_class = ctx.module.global_module.classes[BOOL_TYPE]
        if type is not bool_class:
            args = [res]
            arg_type = self.get_type(node, ctx)
            arg_types = [arg_type]
            res = self.get_function_call(arg_type, '__bool__', args, arg_types,
                                         node, ctx)
        if res.typ() != self.viper.Bool:
            res = self.get_function_call(bool_class, '__unbox__', [res], [None],
                                         node, ctx)
        return stmt, res

    def translate_Expr(self, node: ast.Expr, ctx: Context) -> StmtsAndExpr:
        return self.translate_expr(node.value, ctx)

    def translate_Name(self, node: ast.Name, ctx: Context) -> StmtsAndExpr:
        target = self.get_target(node, ctx)
        if isinstance(target, PythonGlobalVar):
            position = self.to_position(node, ctx)
            if target.cls:
                # This is a static field
                field_func = self.translate_static_field_access(target,
                    ctx.current_class, position, ctx)
                return [], field_func
            var = target
            type = self.translate_type(var.type, ctx)
            func_app = self.viper.FuncApp(var.sil_name, [], position,
                                          self.no_info(ctx), type, [])
            return [], func_app
        elif isinstance(target, PythonMethod):
            func = self.viper.DomainFuncApp(target.func_constant, [],
                                            self.viper.function_domain_type(),
                                            self.to_position(node, ctx), self.no_info(ctx),
                                            FUNCTION_DOMAIN_NAME)
            return [], func
        else:
            if isinstance(target, PythonType):
                return [], self.type_factory.translate_type_literal(target,
                    self.to_position(node, ctx), ctx)
            if node.id in ctx.var_aliases:
                var = ctx.var_aliases[node.id]
            else:
                var = ctx.actual_function.get_variable(node.id)
            if (isinstance(var, PythonIOExistentialVar) and
                    not var.is_defined()):
                raise InvalidProgramException(
                    node, 'io_existential_var.use_of_undefined')

            if (isinstance(ctx.actual_function, PythonMethod) and
                    not (ctx.actual_function.pure or ctx.actual_function.predicate) and
                    not isinstance(node.ctx, ast.Store) and
                    self.is_local_variable(var, ctx) and
                    var.type.name != 'Callable'):
                result = self.wrap_definedness_check(var, node, ctx)
            else:
                result = var.ref(node, ctx)
            return [], result

    def wrap_definedness_check(self, var: PythonVar, node: ast.AST,
                               ctx: Context) -> Expr:
        """
        Create an access to the given variable, wrapped into a function call which checks
        if the variable has been defined.
        """
        pos = self.to_position(node, ctx, rules=rules.LOCAL_VARIABLE_NOT_DEFINED)
        info = self.no_info(ctx)
        id_param_decl = self.viper.LocalVarDecl('id', self.viper.Int, pos, info)
        var_param_decl = self.viper.LocalVarDecl('val', self.viper.Ref, pos, info)
        id = self.viper.IntLit(self._get_string_value(var.sil_name), pos, info)
        return self.viper.FuncApp(CHECK_DEFINED_FUNC, [var.ref(node, ctx), id], pos, info,
                                  self.viper.Ref, [var_param_decl, id_param_decl])

    def _lookup_field(self, node: ast.Attribute, ctx: Context) -> PythonField:
        """
        Returns the PythonField for a given ast.Attribute node.
        """
        recv = self.get_type(node.value, ctx)
        if recv.name == 'type':
            recv = recv.type_args[0]
        field = recv.get_field(node.attr)
        if not field:
            if (isinstance(recv, PythonType) and
                    recv.python_class.get_static_field(node.attr)):
                var = recv.python_class.static_fields[node.attr]
                return var
            raise InvalidProgramException(node, 'field.nonexistent')
        if isinstance(field, PythonField):
            field = field.actual_field
            if field.is_mangled() and (field.cls is not ctx.current_class and
                                       field.cls is not ctx.actual_function.cls):
                raise InvalidProgramException(node, 'private.field.access')

        return field

    def translate_static_field_access(self, field: PythonGlobalVar,
                                      receiver: Union[Expr, PythonType],
                                      position, ctx: Context) -> Expr:
        """
        Translates an access to the given field via the given receiver. The
        receiver can either be the type literal via which the field is
        accessed, an expression of type 'type' (e.g. cls in classmethods) or
        a normal object.
        """
        while field.overrides:
            field = field.overrides
        field_type = self.translate_type(field.type, ctx)

        if isinstance(receiver, PythonType):
            type_arg = self.type_factory.translate_type_literal(receiver,
                                                                position, ctx)
        else:
            if receiver.typ() != self.type_factory.type_type():
                # Normal object, get its type.
                type_arg = self.type_factory.typeof(receiver, ctx)
            else:
                # Type expression, use it directly.
                type_arg = receiver
        info = self.no_info(ctx)
        param = self.viper.LocalVarDecl('receiver',
                                        self.type_factory.type_type(), position,
                                        info)
        return self.viper.FuncApp(field.sil_name, [type_arg], position, info,
                                  field_type, [param])

    def translate_Attribute(self, node: ast.Attribute,
                            ctx: Context) -> StmtsAndExpr:
        position = self.to_position(node, ctx)
        target = self.get_target(node.value, ctx)
        func_name = get_func_name(node.value)
        if isinstance(target, PythonModule):
            target = self.get_target(node, ctx)
            if isinstance(target, PythonGlobalVar):
                # Global var
                info = self.no_info(ctx)
                var_type = self.translate_type(target.type, ctx)
                return [], self.viper.FuncApp(target.sil_name, [], position,
                                              info, var_type, [])
            else:
                raise UnsupportedException(node)
        elif isinstance(target, PythonClass) and func_name != 'Result':
            field = target.get_static_field(node.attr)
            field_func = self.translate_static_field_access(field, target,
                                                            position, ctx)
            return [], field_func
        else:
            stmt, receiver = self.translate_expr(node.value, ctx,
                                                 target_type=self.viper.Ref)
            field = self._lookup_field(node, ctx)
            if isinstance(field, PythonGlobalVar):
                field_func = self.translate_static_field_access(field, receiver,
                                                                position, ctx)
                return [], field_func
            if isinstance(field, PythonMethod):
                # This is a reference to a property, so we translate it to a call of
                # the property getter function.
                target_type = self.translate_type(self.get_type(node.value, ctx), ctx)
                target_param = self.viper.LocalVarDecl('self', target_type, position,
                                                       self.no_info(ctx))
                property_type = self.translate_type(field.type, ctx)
                return stmt, self.viper.FuncApp(field.sil_name, [receiver], position,
                                                self.no_info(ctx), property_type,
                                                [target_param])
            return (stmt, self.viper.FieldAccess(receiver, field.sil_field,
                                                 position, self.no_info(ctx)))

    def translate_UnaryOp(self, node: ast.UnaryOp,
                          ctx: Context) -> StmtsAndExpr:
        if isinstance(node.op, ast.Not):
            stmt, expr = self.translate_expr(node.operand, ctx,
                                             target_type=self.viper.Bool)
            return (stmt, self.viper.Not(expr, self.to_position(node, ctx),
                                         self.no_info(ctx)))
        stmt, expr = self.translate_expr(node.operand, ctx,
                                         target_type=self.viper.Int)
        if isinstance(node.op, ast.USub):
            return (stmt, self.viper.Minus(expr, self.to_position(node, ctx),
                                           self.no_info(ctx)))
        else:
            raise UnsupportedException(node)

    def translate_IfExp(self, node: ast.IfExp, ctx: Context,
                        impure=False) -> StmtsAndExpr:
        position = self.to_position(node, ctx)
        cond_stmt, cond = self.translate_expr(node.test, ctx,
                                              target_type=self.viper.Bool)
        then_stmt, then = self.translate_expr(node.body, ctx,
                                              target_type=self._target_type,
                                              impure=impure)
        else_stmt, else_ = self.translate_expr(node.orelse, ctx,
                                               target_type=self._target_type,
                                               impure=impure)
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
        op_stmt, result = self.translate_operator(left, right, left_type,
                                                  right_type, node, ctx)
        return stmt + op_stmt, result

    def _is_primitive_operation(self, left_type: PythonType,
                                right_type: PythonType) -> bool:
        """
        Determines if a binary operation with the given operand types can be
        translated as a native silver binary operation. True iff both types
        are identical and primitives.
        """
        left_type_boxed = left_type.python_class.try_box()
        right_type_boxed = right_type.python_class.try_box()
        return (right_type_boxed.name in BOXED_PRIMITIVES and
                right_type_boxed.name == left_type_boxed.name)

    def _translate_primitive_operation(self, left: Expr, right: Expr,
                                       op_type: PythonType, op: ast.operator,
                                       pos: Position, ctx: Context) -> Expr:
        """
        Translates the binary operation consisting of the given operator and
        the given operands to a primitive Viper BinOp.
        """
        op = self._primitive_operations[type(op)]
        if op_type.python_class.try_box().name == INT_TYPE:
            wrap = self.to_int
        elif op_type.python_class.try_box().name == CALLABLE_TYPE:
            wrap = lambda node, ctx: node
        else:
            wrap = self.to_bool
        result = op(wrap(left, ctx), wrap(right, ctx), pos, self.no_info(ctx))
        return result

    def translate_operator(self, left: Expr, right: Expr, left_type: PythonType,
                           right_type: PythonType, node: ast.AST,
                           ctx: Context) -> StmtsAndExpr:
        """
        Translates the invocation of the binary operator of 'node' on the
        given two arguments, either to a primitive Silver operation or to a
        function or method call.
        """
        position = self.to_position(node, ctx)
        info = self.no_info(ctx)
        stmt = []
        if self._is_primitive_operation(left_type, right_type):
            result = self._translate_primitive_operation(left, right, left_type,
                                                         node.op, position, ctx)
            return stmt, result
        func_name = OPERATOR_FUNCTIONS[type(node.op)]
        called_method = left_type.get_func_or_method(func_name)
        if called_method.pure:
            result = self.get_function_call(left_type, func_name,
                                            [left, right],
                                            [left_type, right_type],
                                            node, ctx)
        else:
            result_type = called_method.type
            res_var = ctx.actual_function.create_variable('op_res',
                                                          result_type,
                                                          self.translator)
            stmt += self.get_method_call(left_type, func_name,
                                         [left, right],
                                         [left_type, right_type],
                                         [res_var.ref(node, ctx)], node,
                                         ctx)
            result = res_var.ref(node, ctx)
        return stmt, result

    def translate_Compare(self, node: ast.Compare,
                          ctx: Context) -> StmtsAndExpr:
        if self.is_io_existential_defining_equality(node, ctx):
            self.define_io_existential(node, ctx)
            return ([], self.viper.TrueLit(self.to_position(node, ctx),
                                           self.no_info(ctx)))
        if self.is_wait_level_comparison(node, ctx):
            return self.translate_wait_level_comparison(node, ctx)
        if len(node.ops) != 1 or len(node.comparators) != 1:
            raise UnsupportedException(node)
        left_stmt, left = self.translate_expr(node.left, ctx)
        left_type = self.get_type(node.left, ctx)
        right_stmt, right = self.translate_expr(node.comparators[0], ctx)
        right_type = self.get_type(node.comparators[0], ctx)
        stmts = left_stmt + right_stmt
        position = self.to_position(node, ctx)
        info = self.no_info(ctx)

        if self._is_primitive_operation(left_type, right_type):
            result = self._translate_primitive_operation(left, right, left_type,
                                                         node.ops[0], position,
                                                         ctx)
            return stmts, result

        if isinstance(node.ops[0], ast.Is):
            return (stmts, self.viper.EqCmp(left, right, position, info))
        elif isinstance(node.ops[0], ast.IsNot):
            return (stmts, self.viper.NeCmp(left, right, position, info))
        elif isinstance(node.ops[0], (ast.In, ast.NotIn)):
            contains_stmts, contains_expr = self._translate_contains(
                left, right, left_type, right_type, node, ctx)
            stmts.extend(contains_stmts)
            return stmts, contains_expr
        if isinstance(node.ops[0], ast.Eq):
            int_compare = self.viper.EqCmp
            compare_func = '__eq__'
        elif isinstance(node.ops[0], ast.NotEq):
            int_compare = self.viper.NeCmp
            compare_func = '__ne__'
        elif isinstance(node.ops[0], ast.Gt):
            int_compare = self.viper.GtCmp
            compare_func = '__gt__'
        elif isinstance(node.ops[0], ast.GtE):
            int_compare = self.viper.GeCmp
            compare_func = '__ge__'
        elif isinstance(node.ops[0], ast.Lt):
            int_compare = self.viper.LtCmp
            compare_func = '__lt__'
        elif isinstance(node.ops[0], ast.LtE):
            int_compare = self.viper.LeCmp
            compare_func = '__le__'
        else:
            raise UnsupportedException(node.ops[0])
        if left_type.get_function(compare_func):
            comparison = self.get_function_call(left_type, compare_func,
                                                [left, right],
                                                [left_type, right_type],
                                                node, ctx)
        elif compare_func == '__ne__' and left_type.get_function('__eq__'):
            # The default behavior if __ne__ is not explicitly defined
            # is to invert the result of __eq__.
            call = self.get_function_call(left_type, '__eq__',
                                          [left, right],
                                          [left_type, right_type],
                                          node, ctx)
            comparison = self.viper.Not(self.to_bool(call, ctx, node.left),
                                        position, info)
        else:
            raise InvalidProgramException(node, 'undefined.comparison')
        return stmts, comparison

    def _translate_contains(
            self, left: Expr, right: Expr, left_type: PythonType,
            right_type: PythonType, node: ast.AST,
            ctx: Context) -> StmtsAndExpr:
        args = [right, left]
        arg_types = [right_type, left_type]
        app = self.get_function_call(
            right_type, '__contains__', args, arg_types, node, ctx)
        if isinstance(node.ops[0], ast.NotIn):
            app = self.viper.Not(
                app, self.to_position(node, ctx), self.no_info(ctx))
        return [], app

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

    def translate_BoolOp(self, node: ast.BoolOp, ctx: Context,
                         impure=False) -> StmtsAndExpr:
        assert isinstance(node.op, ast.Or) or isinstance(node.op, ast.And)

        position = self.to_position(node, ctx)
        info = self.no_info(ctx)

        statements_parts = []
        expression_parts = []
        bool_parts = []
        types_parts = []
        all_pure = True
        for value in node.values:
            typ = self.get_type(value, ctx)
            old_target = self._target_type
            # Translate expression to its original type, but with boolean
            # subexpressions.
            self._target_type = self.viper.Bool
            statements_part, expression_part = self._translate_only(
                value, ctx, impure)
            self._target_type = old_target
            # Get a version that is converted to a boolean. Unless we have
            # something impure.
            if self._is_pure(expression_part):
                bool_expression = self.to_bool(expression_part, ctx, value)
            else:
                bool_expression = expression_part
                all_pure = False
            if self._is_expression and statements_part:
                raise InvalidProgramException(node, 'not_expression')
            statements_parts.append(statements_part)
            if all_pure:
                expression_parts.append(self.to_ref(expression_part, ctx))
            bool_parts.append(bool_expression)
            types_parts.append(typ)

        all_bool = all(typ and typ.name == 'bool' for typ in types_parts)

        if isinstance(node.op, ast.And):
            operator = (
                lambda left, right:
                self.viper.And(left, right, position, info))
        else:
            operator = (
                lambda left, right:
                self.viper.Or(left, right, position, info))

        joined_bool_parts = [
            join_expressions(operator, bool_parts[:i + 1])
            for i in range(len(bool_parts))
            ]
        # If this is not an assertion (i.e. all parts are pure and there are non-boolean operands)
        if all_pure and not all_bool:
            # Instead of using Viper's And and Or, create an expression like
            # bool(lhs) ? lhs : rhs (or the other way round for Or).
            if isinstance(node.op, ast.And):
                operator = (
                    lambda left, left_bool, right:
                    self.viper.CondExp(left_bool, right, left, position, info)
                )
            else:
                operator = (
                    lambda left, left_bool, right:
                    self.viper.CondExp(left_bool, left, right, position, info)
                )
            joined_expression_parts = [
                join_three_expressions(operator, expression_parts[:i + 1],
                                       bool_parts[:i + 1], expression_parts[i])
                for i in range(len(bool_parts))
                ]

        statements = statements_parts[0]
        for i, part in enumerate(statements_parts[1:]):

            cond = joined_bool_parts[i]
            if isinstance(node.op, ast.Or):
                cond = self.viper.Not(cond, position, info)

            if part:
                then_block = self.translate_block(part, position, info)
                else_block = self.translate_block([], position, info)
                if_stmt = self.viper.If(cond, then_block, else_block,
                                        position, info)
                statements.append(if_stmt)
        if all_pure and not all_bool:
            res_val = joined_expression_parts[-1]
        else:
            res_val = joined_bool_parts[-1]
        return statements, res_val

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
