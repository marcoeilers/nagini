import ast

from nagini_translation.lib.constants import (
    END_LABEL,
    ERROR_NAME,
    OBJECT_TYPE,
    PRIMITIVES,
)
from nagini_translation.lib.program_nodes import (
    CallSlot,
    GenericType,
    MethodType,
    PythonExceptionHandler,
    PythonField,
    PythonMethod,
    PythonTryBlock,
    PythonVar,
)
from nagini_translation.lib.typedefs import (
    DomainFuncApp,
    Expr,
    Position,
    Stmt,
    VarDecl,
)
from nagini_translation.lib.util import (
    flatten,
    get_body_indices,
    get_surrounding_try_blocks,
    InvalidProgramException
)
from nagini_translation.translators.abstract import Context
from nagini_translation.translators.common import CommonTranslator
from typing import List, Tuple


class MethodTranslator(CommonTranslator):

    def get_parameter_typeof(self, param: PythonVar,
                             ctx: Context) -> 'silver.ast.DomainFuncApp':
        """
        Creates an expression checking if the given parameter has its type,
        to be assumed in preconditions and/or postconditions. If possible,
        the expression is wrapped in an InhaleExhaleExpression s.t. it is
        just assumed, not checked. Generally this seems to be possible with
        types, but not with type arg numbers, because the latter encodes length
        for tuples.
        """
        no_pos = self.no_position(ctx)
        result = self.var_type_check(param.sil_name, param.type, no_pos, ctx)
        return result

    def _translate_pres(self, method: PythonMethod,
                        ctx: Context) -> List[Expr]:
        """
        Translates the preconditions specified for 'method'.
        """
        pres = []
        for pre, aliases in method.precondition:
            with ctx.additional_aliases(aliases):
                stmt, expr = self.translate_expr(pre, ctx, self.viper.Bool, True)
            if stmt:
                raise InvalidProgramException(pre, 'purity.violated')
            pres.append(expr)

        if method.cls and method.method_type is MethodType.normal:
            error_string = '"call receiver is not None"'
            pos = self.to_position(method.node, ctx, error_string)
            not_null = self.viper.NeCmp(next(iter(method.args.values())).ref(),
                                        self.viper.NullLit(
                                            self.no_position(ctx),
                                            self.no_info(ctx)),
                                        pos,
                                        self.no_info(ctx))
            pres = [not_null] + pres

        return pres

    def _translate_posts(self, method: PythonMethod,
                         err_var: 'viper.ast.LocalVar',
                         ctx: Context) -> List[Expr]:
        """
        Translates the postconditions specified for 'method'.
        """
        ctx.obligation_context.is_translating_posts = True
        posts = []
        no_error = self.viper.EqCmp(err_var,
                                    self.viper.NullLit(self.no_position(ctx),
                                                       self.no_info(ctx)),
                                    self.no_position(ctx), self.no_info(ctx))
        for post, aliases in method.postcondition:
            with ctx.additional_aliases(aliases):
                stmt, expr = self.translate_expr(post, ctx, self.viper.Bool, True)
            if stmt:
                raise InvalidProgramException(post, 'purity.violated')
            if method.declared_exceptions:
                expr = self.viper.Implies(no_error, expr,
                                          self.to_position(post, ctx),
                                          self.no_info(ctx))
            posts.append(expr)

        ctx.obligation_context.is_translating_posts = False
        return posts

    def _translate_exceptional_posts(self, method: PythonMethod,
                                     err_var: 'viper.ast.LocalVar',
                                     ctx: Context) -> List[Expr]:
        """
        Translates the exceptional postconditions specified for 'method'.
        """
        ctx.obligation_context.is_translating_posts = True
        posts = []
        error = self.viper.NeCmp(err_var,
                                 self.viper.NullLit(self.no_position(ctx),
                                                    self.no_info(ctx)),
                                 self.no_position(ctx), self.no_info(ctx))
        error_type_conds = []
        error_string = '"method only raises exceptions of type{0} {1}"'.format(
            's' if len(method.declared_exceptions) > 1 else '',
            ', '.join([e.name for e in method.declared_exceptions]))
        error_type_pos = self.to_position(method.node, ctx, error_string)
        for exception in method.declared_exceptions:
            has_type = self.var_type_check(ERROR_NAME,
                                           exception,
                                           error_type_pos,
                                           ctx, inhale_exhale=False)
            error_type_conds.append(has_type)
            condition = self.viper.And(error, has_type, self.no_position(ctx),
                                       self.no_info(ctx))
            assert ctx.current_contract_exception is None
            ctx.current_contract_exception = exception
            for post, aliases in method.declared_exceptions[exception]:
                with ctx.additional_aliases(aliases):
                    stmt, expr = self.translate_expr(post, ctx, self.viper.Bool, True)
                if stmt:
                    raise InvalidProgramException(post, 'purity.violated')
                expr = self.viper.Implies(condition, expr,
                                          self.to_position(post, ctx),
                                          self.no_info(ctx))
                posts.append(expr)
            ctx.current_contract_exception = None

        error_type_cond = None
        for type in error_type_conds:
            if error_type_cond is None:
                error_type_cond = type
            else:
                error_type_cond = self.viper.Or(error_type_cond, type,
                                                error_type_pos,
                                                self.no_info(ctx))
        if error_type_cond is not None:
            posts.append(self.viper.Implies(error, error_type_cond,
                                            error_type_pos,
                                            self.no_info(ctx)))

        ctx.obligation_context.is_translating_posts = False
        return posts

    def _create_typeof_pres(self, func: PythonMethod, is_constructor: bool,
                            ctx: Context) -> List[DomainFuncApp]:
        """
        Creates 'typeof' preconditions for function arguments.
        """
        if isinstance(func, CallSlot):
            args = func.get_args()
            args.extend(func.uq_variables.values())
        else:
            args = func.get_args()
        pres = []
        for i, arg in enumerate(args):
            if not (arg.type.name in PRIMITIVES):
                if i == 0:
                    if is_constructor:
                        continue
                    if func.method_type == MethodType.class_method:
                        cls_arg = arg.ref()
                        type_check = self.type_factory.subtype_check(
                            cls_arg, func.cls, self.no_position(ctx), ctx)
                        pres.append(type_check)
                        continue
                type_check = self.get_parameter_typeof(arg, ctx)
                pres.append(type_check)
        if func.var_arg:
            type_check = self.get_parameter_typeof(func.var_arg, ctx)
            pres.append(type_check)
        pos = self.no_position(ctx)
        info = self.no_info(ctx)
        if func.kw_arg:
            type_check = self.get_parameter_typeof(func.kw_arg, ctx)
            set_ref = self.viper.SetType(self.viper.Ref)
            dict_acc_field = self.viper.Field('dict_acc', set_ref,
                                              pos, info)
            field_acc = self.viper.FieldAccess(func.kw_arg.ref(),
                                               dict_acc_field,
                                               pos, info)
            full_perm = self.viper.FullPerm(self.no_position(ctx),
                                            self.no_info(ctx))
            acc_pred = self.viper.FieldAccessPredicate(field_acc, full_perm,
                                                       pos, info)
            pres.append(type_check)
            pres.append(acc_pred)
        if func.cls:
            # Add upper bound information for type variables.
            for name, var in func.cls.type_vars.items():
                var_expr = self.type_factory.translate_type_literal(var, pos,
                                                                    ctx)
                check = self.type_factory.subtype_check(var_expr, var.bound,
                                                        pos, ctx)
                pres.append(check)
        if func.name != 'Eval':
            # Make an exception for Eval because it uses type variables in ways we don't
            # generally support.
            for name, var in func.type_vars.items():
                check = self.type_factory.subtype_check(var.type_expr, var.bound,
                                                        pos, ctx)
                pres.append(check)
        return pres

    def _translate_params(self, func: PythonMethod,
                          ctx: Context) -> List[VarDecl]:
        args = []
        for arg in func.get_args():
            args.append(arg.decl)
        if func.var_arg:
            args.append(func.var_arg.decl)
        if func.kw_arg:
            args.append(func.kw_arg.decl)
        return args

    def translate_function(self, func: PythonMethod,
                           ctx: Context) -> 'silver.ast.Function':
        """
        Translates a pure Python function (may or not belong to a class) to a
        Viper function
        """
        old_function = ctx.current_function
        ctx.current_function = func
        pos = self.to_position(func.node, ctx)
        if not func.type:
            raise InvalidProgramException(func.node, 'function.type.none')
        type = self.translate_type(func.type, ctx)
        args = self._translate_params(func, ctx)
        if func.declared_exceptions:
            raise InvalidProgramException(func.node,
                                          'function.throws.exception')
        # Create preconditions
        pres = self._translate_pres(func, ctx)
        # Create postconditions
        posts = []
        for post, aliases in func.postcondition:
            with ctx.additional_aliases(aliases):
                stmt, expr = self.translate_expr(post, ctx, self.viper.Bool)
            if stmt:
                raise InvalidProgramException(post, 'purity.violated')
            posts.append(expr)
        # Create typeof preconditions
        pres = self._create_typeof_pres(func, False, ctx) + pres
        if func.type.name not in PRIMITIVES:
            res_type = self.translate_type(func.type, ctx)
            result = self.viper.Result(res_type, pos, self.no_info(ctx))
            check = self.type_check(result, func.type, pos, ctx)
            posts = [check] + posts

        statements = func.node.body
        start, end = get_body_indices(statements)
        # Translate body
        actual_body = statements[start:end]
        if (func.contract_only or
                (len(actual_body) == 1 and isinstance(actual_body[0], ast.Expr) and
                 isinstance(actual_body[0].value, ast.Ellipsis))):
            body = None
        else:
            body = self.translate_exprs(actual_body, func, ctx)
        ctx.current_function = old_function
        name = func.sil_name
        return self.viper.Function(name, args, type, pres, posts, body,
                                   pos, self.no_info(ctx))

    def extract_contract(self, method: PythonMethod, errorvarname: str,
                         is_constructor: bool,
                         ctx: Context) -> Tuple[List[Expr], List[Expr]]:
        """
        Extracts the pre and postcondition from a given method
        """
        error_var_ref = self.viper.LocalVar(errorvarname, self.viper.Ref,
                                            self.no_position(ctx),
                                            self.no_info(ctx))
        # Create preconditions
        pres = self._translate_pres(method, ctx)
        # Create postconditions
        posts = self._translate_posts(method, error_var_ref, ctx)
        # Create exceptional postconditions
        posts += self._translate_exceptional_posts(method, error_var_ref, ctx)
        # Create typeof preconditions
        type_pres = self._create_typeof_pres(method, is_constructor, ctx)
        pres = type_pres + pres

        result_post = self._create_result_type_post(method, error_var_ref, ctx)
        posts = result_post + posts
        return pres, posts

    def _create_result_type_post(self, method: PythonMethod, error_var_ref,
                                 ctx: Context) -> List[Expr]:
        if method.type and method.type.name not in PRIMITIVES:
            result = self._create_single_result_post(method, error_var_ref,
                ctx.result_var.ref(method.node, ctx), ctx)
            return result
        else:
            return []

    def _create_single_result_post(self, method: PythonMethod, error_var_ref,
                                   result_var, ctx: Context) -> List[Expr]:
        no_pos = self.no_position(ctx)
        method_pos = self.to_position(method.node, ctx,
                                      '"return type is correct"')
        no_info = self.no_info(ctx)

        check = self.type_check(result_var,
                                method.type, method_pos, ctx)
        if method.declared_exceptions:
            no_error = self.viper.EqCmp(error_var_ref,
                                        self.viper.NullLit(no_pos, no_info),
                                        method_pos, no_info)
            check = self.viper.Implies(no_error, check, method_pos, no_info)
        result = [check]
        return result

    def get_all_field_accs(self, fields: List['silver.ast.Field'],
            self_var: 'silver.ast.LocalVar', position: 'silver.ast.Position',
            ctx: Context) -> List['silver.ast.FieldAccessPredicate']:
        """
        Creates access predicates for all fields in fields.
        """
        accs = []
        for field in fields:
            acc = self.viper.FieldAccess(self_var, field,
                                         position, self.no_info(ctx))
            perm = self.viper.FullPerm(position, self.no_info(ctx))
            pred = self.viper.FieldAccessPredicate(acc, perm, position,
                                                   self.no_info(ctx))
            accs.append(pred)
        return accs

    def _create_method_epilog(self, method: PythonMethod,
                              ctx: Context) -> List[Stmt]:
        """
        Hook to generate the method epilog.
        """
        end_name = ctx.get_label_name(END_LABEL)
        return [self.viper.Label(end_name, self.no_position(ctx),
                                 self.no_info(ctx))]

    def _create_init_pres(self, method: PythonMethod,
                          ctx: Context) -> List[Expr]:
        """
        Generates preconditions specific to the '__init__' method.
        """
        self_var = method.args[next(iter(method.args))].ref()
        fields = method.cls.all_fields
        accs = [self.get_may_set_predicate(self_var, f, ctx) for f in fields]
        null = self.viper.NullLit(self.no_position(ctx), self.no_info(ctx))
        not_null = self.viper.NeCmp(self_var, null, self.no_position(ctx),
                                    self.no_info(ctx))

        return [not_null] + accs

    def _create_local_vars_for_params(self, method: PythonMethod,
                                      ctx: Context) -> List[Stmt]:
        """Creates LocalVarAssigns for each parameter."""
        assign_stmts = []
        for name, arg in method.args.items():
            arg_var = ctx.current_function.create_variable(name, arg.type,
                                                           self.translator)
            arg_assign = self.viper.LocalVarAssign(arg_var.ref(), arg.ref(),
                                                   self.no_position(ctx),
                                                   self.no_info(ctx))
            assign_stmts.append(arg_assign)
            ctx.set_alias(name, arg_var, arg)

        return assign_stmts

    def bind_type_vars(self, method: PythonMethod, ctx: Context) -> None:
        """
        Binds the names of type variables of the given method and its class
        and superclasses to expressions denoting the values of said types.
        """
        ctx.bound_type_vars = {}
        # Class type variables first.
        if method.cls and method.method_type is MethodType.normal:
            cls = method.cls
            while cls:
                for name, var in cls.type_vars.items():
                    self_arg = next(iter(method.args.values())).ref()
                    literal = self.type_factory.get_ref_type_arg(self_arg,
                                                                 var.target_type,
                                                                 var.index, ctx)
                    ctx.bound_type_vars[(var.target_type.name, name)] = literal
                cls = cls.superclass
                if isinstance(cls, GenericType):
                    cls = cls.cls
        # Now method type variables.
        for name, var in method.type_vars.items():
            if callable(var.type_expr):
                # var.type_expr is currently the function that will create the
                # type expression when given the parameter that defines the
                # type variable (identified by var.target_node).
                for i, python_var in enumerate(method.args.values()):
                    if python_var.node is var.target_node:
                        ref = python_var.ref()
                typeof = self.type_factory.typeof(ref, ctx)
                literal = var.type_expr(self.type_factory, typeof, ctx)
                var.type_expr = literal
            else:
                literal = var.type_expr
            ctx.bound_type_vars[(var.name,)] = literal
        if method.name == 'Eval':
            # Eval uses type parameters in ways we don't usually support;
            # while translating it, we're treating the type parameter V as type
            # object.
            object_type = ctx.module.global_module.classes[OBJECT_TYPE]
            literal = self.type_factory.translate_type_literal(object_type,
                                                               self.no_position(ctx), ctx)
            ctx.bound_type_vars[('V',)] = literal

    def translate_method(self, method: PythonMethod,
                         ctx: Context) -> 'silver.ast.Method':
        """
        Translates an impure Python function (may or not belong to a class) to
        a Viper method
        """
        old_function = ctx.current_function
        ctx.current_function = method
        args = self._translate_params(method, ctx)
        self.bind_type_vars(method, ctx)

        results = [res.decl for res in method.get_results()]
        error_var = PythonVar(ERROR_NAME, None,
                              ctx.module.global_module.classes['Exception'])
        error_var.process(ERROR_NAME, self.translator)
        error_var_decl = error_var.decl
        error_var_ref = error_var.ref()
        method.error_var = error_var
        pres, posts = self.extract_contract(method, ERROR_NAME, False, ctx)
        if method.cls and method.name == '__init__':
            init_pres = self._create_init_pres(method, ctx)
            pres = init_pres + pres
        if method.declared_exceptions:
            results.append(error_var_decl)

        # Translate body
        body = []
        no_pos = self.no_position(ctx)
        no_info = self.no_info(ctx)
        if method.cls and method.method_type == MethodType.normal:
            type_check = self.type_factory.type_check(
                next(iter(method.args.values())).ref(), method.cls, no_pos, ctx,
                concrete=True)
            inhale_type = self.viper.Inhale(type_check, self.no_position(ctx),
                                            self.no_info(ctx))
            body.append(inhale_type)
        if method.type:
            # Assign null as the default return value to the return variable.
            assign_none = self.viper.LocalVarAssign(method.result.ref(),
                                                    self.viper.NullLit(no_pos,
                                                                       no_info),
                                                    no_pos, no_info)
            body.append(assign_none)
        if method.contract_only:
            false = self.viper.FalseLit(self.no_position(ctx),
                                        self.no_info(ctx))
            assume_false = self.viper.Inhale(false, self.no_position(ctx),
                                             self.no_info(ctx))
            body.append(assume_false)
            locals = []
        else:
            statements = method.node.body
            body_start, body_end = get_body_indices(statements)
            if method.declared_exceptions:
                body.append(self.viper.LocalVarAssign(error_var_ref,
                    self.viper.NullLit(self.no_position(ctx),
                                       self.no_info(ctx)),
                    self.no_position(ctx), self.no_info(ctx)))
            # Create local variables for parameters
            body.extend(self._create_local_vars_for_params(method, ctx))
            body += flatten(
                [self.translate_stmt(stmt, ctx) for stmt in
                 method.node.body[body_start:body_end]])
            for arg in method.get_args():
                ctx.remove_alias(arg.name)
            end_label = ctx.get_label_name(END_LABEL)
            body.append(self.viper.Goto(end_label, self.no_position(ctx),
                                        self.no_info(ctx)))
            assert not ctx.var_aliases
            for block in method.try_blocks:
                for handler in block.handlers:
                    body += self.translate_handler(handler, ctx)
                if block.else_block:
                    body += self.translate_handler(block.else_block, ctx)
                if block.finally_block or block.with_item:
                    body += self.translate_finally(block, ctx)
            body += self.add_handlers_for_inlines(ctx)
            locals = [local.decl for local in method.get_locals()
                      if not local.name.startswith('lambda')]
            body += self._create_method_epilog(method, ctx)
        name = method.sil_name
        nodes = self.create_method_node(
            ctx, name, args, results, pres, posts, locals, body,
            self.to_position(method.node, ctx), self.no_info(ctx),
            method=method)
        ctx.current_function = old_function
        return nodes

    def _assign_exit_vars(self, block: PythonTryBlock, type_var: PythonVar,
                          value_var: PythonVar, traceback_var: PythonVar,
                          pos: Position, ctx: Context) -> Stmt:
        """
        Assigns the exception and its type to the given variables if there is
        an uncaught exception, otherwise assigns None to everything.
        """
        info = self.no_info(ctx)
        null = self.viper.NullLit(pos, info)
        one = self.viper.IntLit(1, pos, info)
        code_var = block.get_finally_var(self.translator)
        error_cond = self.viper.GtCmp(code_var.ref(), one, pos, info)
        error_case = []
        no_error_case = []
        # FIXME: Cannot currently assign None to type variable, because types
        # aren't objects.
        for var in [value_var, traceback_var]:
            assign = self.viper.LocalVarAssign(var.ref(), null, pos, info)
            no_error_case.append(assign)

        value_assign = self.viper.LocalVarAssign(value_var.ref(),
                                                 block.error_var.ref(), pos,
                                                 info)
        error_case.append(value_assign)
        error_type = self.type_factory.typeof(block.error_var.ref(), ctx)
        type_assign = self.viper.LocalVarAssign(type_var.ref(), error_type,
                                                pos, info)
        error_case.append(type_assign)

        tb_class = ctx.module.global_module.classes['traceback']
        tb_type = self.type_check(traceback_var.ref(), tb_class, pos, ctx)
        inhale_types = self.viper.Inhale(tb_type, pos, info)
        error_case.append(inhale_types)
        then_block = self.translate_block(error_case, pos, info)
        else_block = self.translate_block(no_error_case, pos, info)
        return self.viper.If(error_cond, then_block, else_block, pos, info)

    def translate_finally(self, block: PythonTryBlock,
                          ctx: Context) -> List[Stmt]:
        """
        Creates a code block representing the finally-block belonging to block,
        to be put at the end of a Viper method.
        """
        pos = self.to_position(block.node, ctx)
        info = self.no_info(ctx)
        label_name = ctx.get_label_name(block.finally_name)
        label = self.viper.Label(label_name,
                                 self.to_position(block.node, ctx),
                                 self.no_info(ctx))
        body = [label]
        if block.finally_block:
            for stmt in block.finally_block:
                body += self.translate_stmt(stmt, ctx)
        else:
            # With-block
            ctx_type = self.get_type(block.with_item.context_expr, ctx)
            ctx_var = block.with_var
            exit_type = ctx_type.get_method('__exit__').type
            exit_res = ctx.current_function.create_variable('exit_res',
                                                            exit_type,
                                                            self.translator)

            type_class = ctx.module.global_module.classes['type']
            exception_class = ctx.module.global_module.classes['Exception']
            tb_class = ctx.module.global_module.classes['traceback']
            # The __exit__ method takes three arguments: type, value and
            # traceback.
            type_var = ctx.actual_function.create_variable('t', type_class,
                                                           self.translator)
            value_var = ctx.actual_function.create_variable('e',
                                                            exception_class,
                                                            self.translator)
            traceback_var = ctx.actual_function.create_variable('tb',
                                                                tb_class,
                                                                self.translator)
            body.append(self._assign_exit_vars(block, type_var, value_var,
                                               traceback_var, pos, ctx))
            exit_call = self.get_method_call(ctx_type, '__exit__',
                                             [ctx_var.ref(), type_var.ref(),
                                              value_var.ref(),
                                              traceback_var.ref()],
                                             [ctx_type, None, None, None],
                                             [exit_res.ref()],
                                             block.with_item.context_expr, ctx)
            body.extend(exit_call)
        finally_var = block.get_finally_var(self.translator)
        if finally_var.sil_name in ctx.var_aliases:
            finally_var = ctx.var_aliases[finally_var.sil_name]
        tries = get_surrounding_try_blocks(ctx.actual_function.try_blocks,
                                           block.node)
        post_label = ctx.get_label_name(block.post_name)
        goto_post = self.viper.Goto(post_label, pos, info)
        end_label = ctx.get_label_name(END_LABEL)
        goto_end = self.viper.Goto(end_label, pos, info)
        empty_stmt = self.translate_block([], pos, info)

        except_block = []
        return_block = []
        for current in tries:
            if not return_block and current.finally_block:
                # Propagate return value
                var_next = current.get_finally_var(self.translator)
                if var_next.sil_name in ctx.var_aliases:
                    var_next = ctx.var_aliases[var_next.sil_name]
                next_assign = self.viper.LocalVarAssign(var_next.ref(),
                                                        finally_var.ref(),
                                                        pos, info)
                # Goto finally block
                next_label = ctx.get_label_name(current.finally_name)
                goto_next = self.viper.Goto(next_label, pos, info)
                return_block = [next_assign, goto_next]
            for handler in current.handlers:
                # If handler applies,
                # goto handler
                err_var = block.get_error_var(self.translator)
                if err_var.sil_name in ctx.var_aliases:
                    err_var = ctx.var_aliases[err_var.sil_name]
                condition = self.var_type_check(err_var.sil_name,
                                                handler.exception,
                                                self.to_position(handler.node,
                                                                 ctx),
                                                ctx, inhale_exhale=False)
                label_name = ctx.get_label_name(handler.name)
                goto = self.viper.Goto(label_name, pos, info)
                if_handler = self.viper.If(condition, goto, empty_stmt, pos,
                                           info)
                except_block.append(if_handler)
            if current.finally_block:
                # Propagate return value
                # Goto finally block
                except_block += return_block
                break
        if not return_block:
            return_block = [goto_end]
        if ctx.actual_function.declared_exceptions:
            # Assign error to error output var
            error_var = ctx.error_var.ref()
            block_error_var = block.get_error_var(self.translator)
            if block_error_var.sil_name in ctx.var_aliases:
                block_error_var = ctx.var_aliases[block_error_var.sil_name]
            assign = self.viper.LocalVarAssign(
                error_var, block_error_var.ref(), pos, info)
            except_block.append(assign)
            except_block.append(goto_end)
        else:
            error_string = '"method raises no exceptions"'
            error_pos = self.to_position(block.node, ctx, error_string)
            false = self.viper.FalseLit(error_pos, info)
            assert_false = self.viper.Exhale(false, error_pos, info)
            except_block.append(assert_false)
            except_block.append(goto_end)
        except_block = self.translate_block(except_block, pos, info)
        return_block = self.translate_block(return_block, pos, info)

        number_zero = self.viper.IntLit(0, pos, info)
        greater_zero = self.viper.GtCmp(finally_var.ref(), number_zero, pos,
                                        info)
        number_one = self.viper.IntLit(1, pos, info)
        greater_one = self.viper.GtCmp(finally_var.ref(), number_one, pos, info)
        if_return = self.viper.If(greater_zero, return_block, goto_post, pos,
                                  info)
        if_except = self.viper.If(greater_one, except_block, if_return, pos,
                                  info)
        body += [if_except]
        return body

    def translate_handler(self, handler: PythonExceptionHandler,
                          ctx: Context) -> List[Stmt]:
        """
        Creates a code block representing an exception handler, to be put at
        the end of a Viper method
        """
        label_name = ctx.get_label_name(handler.name)
        label = self.viper.Label(label_name,
                                 self.to_position(handler.node, ctx),
                                 self.no_info(ctx))
        old_var_aliases = ctx.var_aliases
        ctx.var_aliases = handler.try_block.handler_aliases
        no_position = self.no_position(ctx)
        no_info = self.no_info(ctx)
        body = []
        if handler.exception_name:
            err_var = handler.try_block.get_error_var(self.translator)
            if err_var.sil_name in ctx.var_aliases:
                err_var = ctx.var_aliases[err_var.sil_name]
            ctx.var_aliases[handler.exception_name] = err_var
            err_var.type = handler.exception

            body.append(self.set_var_defined(err_var, no_position, no_info))
        for stmt in handler.body:
            body += self.translate_stmt(stmt, ctx)
        body_block = self.translate_block(body,
                                          self.to_position(handler.node, ctx),
                                          no_info)
        if handler.try_block.finally_block:
            next = handler.try_block.finally_name
            finally_var = handler.try_block.get_finally_var(self.translator)
            if finally_var.sil_name in ctx.var_aliases:
                finally_var = ctx.var_aliases[finally_var.sil_name]
            lhs = finally_var.ref()
            rhs = self.viper.IntLit(0, no_position, no_info)
            var_set = self.viper.LocalVarAssign(lhs, rhs, no_position, no_info)
            next_var_set = [var_set]
        else:
            next = 'post_' + handler.try_block.name
            next_var_set = []
        label_name = ctx.get_label_name(next)
        goto_end = self.viper.Goto(label_name,
                                   self.to_position(handler.node, ctx),
                                   no_info)
        ctx.var_aliases = old_var_aliases
        return [label, body_block] + next_var_set + [goto_end]
