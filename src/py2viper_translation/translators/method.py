import ast

from py2viper_translation.lib.constants import END_LABEL, ERROR_NAME, PRIMITIVES
from py2viper_translation.lib.program_nodes import (
    PythonExceptionHandler,
    PythonMethod,
    PythonTryBlock,
    PythonType,
    PythonVar
)
from py2viper_translation.lib.typedefs import (
    DomainFuncApp,
    Expr,
    Stmt,
    StmtsAndExpr,
    VarDecl,
)
from py2viper_translation.lib.util import (
    flatten,
    get_body_start_index,
    get_func_name,
    get_surrounding_try_blocks,
    InvalidProgramException
)
from py2viper_translation.translators.abstract import Context
from py2viper_translation.translators.common import CommonTranslator
from typing import List, Tuple


class MethodTranslator(CommonTranslator):

    def _can_assume_type(self, type: PythonType) -> bool:
        """
        Checks if type information for the given type has to be checked or
        can simply be assumed.
        """
        # Cannot assume tuple type information, since tuple length may be a
        # precondition of other functions used in normal pre- and
        # postconditions.
        return type.name not in ['tuple']

    def get_parameter_typeof(self, param: PythonVar,
                             ctx: Context) -> 'silver.ast.DomainFuncApp':
        """
        Creates an expression checking if the given parameter has its type,
        to be assumed in preconditions and/or postconditions. If possible,
        the expression is wrapped in an InhaleExhaleExpression s.t. it is
        just assumed, not checked; with some types this is not possible.
        """
        result = self.var_type_check(param.sil_name, param.type, ctx)
        if self._can_assume_type(param.type):
            true_lit = self.viper.TrueLit(self.no_position(ctx),
                                          self.no_info(ctx))
            result = self.viper.InhaleExhaleExp(result, true_lit,
                                                self.no_position(ctx),
                                                self.no_info(ctx))
        return result

    def _translate_pres(self, method: PythonMethod,
                        ctx: Context) -> List[Expr]:
        """
        Translates the preconditions specified for 'method'.
        """
        pres = []
        for pre in method.precondition:
            stmt, expr = self.translate_expr(pre, ctx)
            if stmt:
                raise InvalidProgramException(pre, 'purity.violated')
            pres.append(expr)

        return pres

    def _translate_posts(self, method: PythonMethod,
                         err_var: 'viper.ast.LocalVar',
                         ctx: Context) -> List[Expr]:
        """
        Translates the postconditions specified for 'method'.
        """
        posts = []
        no_error = self.viper.EqCmp(err_var,
                                   self.viper.NullLit(self.no_position(ctx),
                                                      self.no_info(ctx)),
                                   self.no_position(ctx), self.no_info(ctx))
        for post in method.postcondition:
            stmt, expr = self.translate_expr(post, ctx)
            if stmt:
                raise InvalidProgramException(post, 'purity.violated')
            if method.declared_exceptions:
                expr = self.viper.Implies(no_error, expr,
                                          self.to_position(post, ctx),
                                          self.no_info(ctx))
            posts.append(expr)

        return posts

    def _translate_exceptional_posts(self, method: PythonMethod,
                                     err_var: 'viper.ast.LocalVar',
                                     ctx: Context) -> List[Expr]:
        """
        Translates the exceptional postconditions specified for 'method'.
        """
        posts = []
        error = self.viper.NeCmp(err_var,
                                 self.viper.NullLit(self.no_position(ctx),
                                                    self.no_info(ctx)),
                                 self.no_position(ctx), self.no_info(ctx))
        error_type_conds = []
        error_type_pos = self.to_position(method.node, ctx)
        for exception in method.declared_exceptions:
            oldpos = ctx.position
            if ctx.position is None:
                ctx.position = error_type_pos
            has_type = self.var_type_check(ERROR_NAME,
                                           ctx.program.classes[exception],
                                           ctx)
            error_type_conds.append(has_type)
            ctx.position = oldpos
            condition = self.viper.And(error, has_type, self.no_position(ctx),
                                       self.no_info(ctx))
            for post in method.declared_exceptions[exception]:
                stmt, expr = self.translate_expr(post, ctx)
                if stmt:
                    raise InvalidProgramException(post, 'purity.violated')
                expr = self.viper.Implies(condition, expr,
                                          self.to_position(post, ctx),
                                          self.no_info(ctx))
                posts.append(expr)

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

        return posts

    def _create_typeof_pres(self, func: PythonMethod, is_constructor: bool,
                            ctx: Context) -> List[DomainFuncApp]:
        """
        Creates 'typeof' preconditions for function arguments.
        """
        args = func.args
        pres = []
        for arg in args.values():
            if not (arg.type.name in PRIMITIVES or
                    (is_constructor and arg == next(iter(args)))):
                type_check = self.get_parameter_typeof(arg, ctx)
                pres.append(type_check)
        if func.var_arg:
            type_check = self.get_parameter_typeof(func.var_arg, ctx)
            pres.append(type_check)
        if func.kw_arg:
            type_check = self.get_parameter_typeof(func.kw_arg, ctx)
            pres.append(type_check)
        return pres

    def _translate_params(self, func: PythonMethod,
                          ctx: Context) -> List[VarDecl]:
        args = []
        for name, arg in func.args.items():
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
        type = self.translate_type(func.type, ctx)
        args = self._translate_params(func)
        if func.declared_exceptions:
            raise InvalidProgramException(func.node,
                                          'function.throws.exception')
        # create preconditions
        pres = self._translate_pres(func, ctx)
        if func.cls:
            not_null = self.viper.NeCmp(next(iter(func.args.values())).ref,
                self.viper.NullLit(self.no_position(ctx), self.no_info(ctx)),
                self.no_position(ctx), self.no_info(ctx))
            pres = [not_null] + pres
        # create postconditions
        posts = []
        for post in func.postcondition:
            stmt, expr = self.translate_expr(post, ctx)
            if stmt:
                raise InvalidProgramException(post, 'purity.violated')
            posts.append(expr)
        # create typeof preconditions
        pres = self._create_typeof_pres(func, False, ctx) + pres
        if func.type.name not in PRIMITIVES:
            res_type = self.translate_type(func.type, ctx)
            result = self.viper.Result(res_type, self.no_position(ctx),
                                       self.no_info(ctx))
            check = self.type_check(result, func.type, ctx)
            if self._can_assume_type(func.type):
                true = self.viper.TrueLit(self.no_position(ctx), self.no_info(ctx))
                check = self.viper.InhaleExhaleExp(check, true,
                                                   self.no_position(ctx),
                                                   self.no_info(ctx))
            posts = [check] + posts

        statements = func.node.body
        body_index = get_body_start_index(statements)
        # translate body
        body = self.translate_exprs(statements[body_index:], func, ctx)
        ctx.current_function = old_function
        name = func.sil_name
        return self.viper.Function(name, args, type, pres, posts, body,
                                   self.no_position(ctx), self.no_info(ctx))

    def extract_contract(self, method: PythonMethod, errorvarname: str,
                         is_constructor: bool,
                         ctx: Context) -> Tuple[List[Expr], List[Expr]]:
        """
        Extracts the pre and postcondition from a given method
        """
        error_var_ref = self.viper.LocalVar(errorvarname, self.viper.Ref,
                                            self.no_position(ctx),
                                            self.no_info(ctx))
        # create preconditions
        pres = self._translate_pres(method, ctx)
        # create postconditions
        posts = self._translate_posts(method, error_var_ref, ctx)
        # create exceptional postconditions
        posts += self._translate_exceptional_posts(method, error_var_ref, ctx)
        # create typeof preconditions
        type_pres = self._create_typeof_pres(method, is_constructor, ctx)
        pres = type_pres + pres
        posts = type_pres + posts
        if method.type and method.type.name not in PRIMITIVES:
            check = self.type_check(ctx.result_var.ref, method.type, ctx)
            if self._can_assume_type(method.type):
                true = self.viper.TrueLit(self.no_position(ctx), self.no_info(ctx))
                check = self.viper.InhaleExhaleExp(check, true,
                                                   self.no_position(ctx),
                                                   self.no_info(ctx))
            posts = [check] + posts
        return pres, posts

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
        end_name = ctx.get_label_name(END_LABEL)
        return [self.viper.Label(end_name, self.no_position(ctx),
                                 self.no_info(ctx))]

    def _create_init_pres(self, method: PythonMethod, ctx: Context) -> List[Expr]:
        """
        Generates preconditions specific to the '__init__' method.
        """
        self_var = method.args[next(iter(method.args))].ref
        fields = method.cls.get_all_sil_fields()
        accs = self.get_all_field_accs(fields, self_var,
                                       self.to_position(method.node, ctx),
                                       ctx)
        null = self.viper.NullLit(self.no_position(ctx), self.no_info(ctx))
        not_null = self.viper.NeCmp(self_var, null, self.no_position(ctx),
                                    self.no_info(ctx))

        return [not_null] + accs

    def translate_method(self, method: PythonMethod,
                         ctx: Context) -> 'silver.ast.Method':
        """
        Translates an impure Python function (may or not belong to a class) to
        a Viper method
        """
        old_function = ctx.current_function
        ctx.current_function = method
        results = [res.decl for res in method.get_results()]
        error_var = PythonVar(ERROR_NAME, None,
                              ctx.program.classes['Exception'])
        error_var.process(ERROR_NAME, self.translator)
        error_var_decl = error_var.decl
        error_var_ref = error_var.ref
        method.error_var = error_var
        pres, posts = self.extract_contract(method, ERROR_NAME, False, ctx)
        if method.cls and method.name == '__init__':
            init_pres = self._create_init_pres(method, ctx)
            pres = init_pres + pres
        if method.declared_exceptions:
            results.append(error_var_decl)
        if method.cls:
            not_null = self.viper.NeCmp(next(iter(method.args.values())).ref,
                self.viper.NullLit(self.no_position(ctx), self.no_info(ctx)),
                self.no_position(ctx), self.no_info(ctx))
            pres = [not_null] + pres

        args = self._translate_params(method, ctx)

        statements = method.node.body
        body_index = get_body_start_index(statements)
        body = []
        # translate body
        if method.cls:
            type_check = self.type_factory.concrete_type_check(
                next(iter(method.args.values())).ref, method.cls, ctx)
            inhale_type = self.viper.Inhale(type_check, self.no_position(ctx),
                                            self.no_info(ctx))
            body.append(inhale_type)
        if method.contract_only:
            false = self.viper.FalseLit(self.no_position(ctx),
                                        self.no_info(ctx))
            assume_false = self.viper.Inhale(false, self.no_position(ctx),
                                             self.no_info(ctx))
            body.append(assume_false)
            locals = []
        else:
            if method.declared_exceptions:
                body.append(self.viper.LocalVarAssign(error_var_ref,
                    self.viper.NullLit(self.no_position(ctx),
                                       self.no_info(ctx)),
                    self.no_position(ctx), self.no_info(ctx)))
            body += flatten(
                [self.translate_stmt(stmt, ctx) for stmt in
                 method.node.body[body_index:]])
            end_label = ctx.get_label_name(END_LABEL)
            body.append(self.viper.Goto(end_label, self.no_position(ctx),
                                        self.no_info(ctx)))
            assert not ctx.var_aliases
            for block in method.try_blocks:
                for handler in block.handlers:
                    body += self.translate_handler(handler, ctx)
                if block.else_block:
                    body += self.translate_handler(block.else_block, ctx)
                if block.finally_block:
                    body += self.translate_finally(block, ctx)
            body += self.add_handlers_for_inlines(ctx)
            locals = [local.decl for local in method.get_locals()]
            body += self._create_method_epilog(method, ctx)
        body_block = self.translate_block(body,
                                          self.to_position(method.node, ctx),
                                          self.no_info(ctx))
        ctx.current_function = old_function
        name = method.sil_name
        return self.viper.Method(name, args, results, pres, posts,
                                 locals, body_block,
                                 self.to_position(method.node, ctx),
                                 self.no_info(ctx))

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
        for stmt in block.finally_block:
            body += self.translate_stmt(stmt, ctx)
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
        # assert tries
        except_block = []
        return_block = []
        for current in tries:
            if not return_block and current.finally_block:
                # propagate return value
                var_next = current.get_finally_var(self.translator)
                if var_next.sil_name in ctx.var_aliases:
                    var_next = ctx.var_aliases[var_next.sil_name]
                next_assign = self.viper.LocalVarAssign(var_next.ref,
                                                        finally_var.ref,
                                                        pos, info)
                # goto finally block
                next_label = ctx.get_label_name(current.finally_name)
                goto_next = self.viper.Goto(next_label, pos, info)
                return_block = [next_assign, goto_next]
            for handler in current.handlers:
                # if handler applies
                # goto handler
                err_var = block.get_error_var(self.translator)
                if err_var.sil_name in ctx.var_aliases:
                    err_var = ctx.var_aliases[err_var.sil_name]
                condition = self.var_type_check(err_var.sil_name,
                                                handler.exception, ctx)
                label_name = ctx.get_label_name(handler.name)
                goto = self.viper.Goto(label_name, pos, info)
                if_handler = self.viper.If(condition, goto, empty_stmt, pos,
                                           info)
                except_block.append(if_handler)
            if current.finally_block:
                # propagate return value
                # goto finally block
                except_block += return_block
                break
        if not return_block:
            return_block = [goto_end]
        if ctx.actual_function.declared_exceptions:
            # assign error to error output var
            error_var = ctx.error_var.ref
            block_error_var = block.get_error_var(self.translator)
            if block_error_var.sil_name in ctx.var_aliases:
                block_error_var = ctx.var_aliases[block_error_var.sil_name]
            assign = self.viper.LocalVarAssign(
                error_var, block_error_var.ref, pos, info)
            except_block.append(assign)
            except_block.append(goto_end)
        else:
            false = self.viper.FalseLit(pos, info)
            assert_false = self.viper.Exhale(false, pos, info)
            except_block.append(assert_false)
        except_block = self.translate_block(except_block, pos, info)
        return_block = self.translate_block(return_block, pos, info)

        number_zero = self.viper.IntLit(0, pos, info)
        greater_zero = self.viper.GtCmp(finally_var.ref, number_zero, pos, info)
        number_one = self.viper.IntLit(1, pos, info)
        greater_one = self.viper.GtCmp(finally_var.ref, number_one, pos, info)
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
        if handler.exception_name:
            if not ctx.var_aliases:
                ctx.var_aliases = {}
            err_var = handler.try_block.get_error_var(self.translator)
            if err_var.sil_name in ctx.var_aliases:
                err_var = ctx.var_aliases[err_var.sil_name]
            ctx.var_aliases[handler.exception_name] = err_var
        body = []
        for stmt in handler.body:
            body += self.translate_stmt(stmt, ctx)
        body_block = self.translate_block(body,
                                          self.to_position(handler.node, ctx),
                                          self.no_info(ctx))
        if handler.try_block.finally_block:
            next = handler.try_block.finally_name
            finally_var = handler.try_block.get_finally_var(self.translator)
            if finally_var.sil_name in ctx.var_aliases:
                finally_var = ctx.var_aliases[finally_var.sil_name]
            lhs = finally_var.ref
            rhs = self.viper.IntLit(0, self.no_position(ctx), self.no_info(ctx))
            var_set = self.viper.LocalVarAssign(lhs, rhs, self.no_position(ctx),
                                                self.no_info(ctx))
            next_var_set = [var_set]
        else:
            next = 'post_' + handler.try_block.name
            next_var_set = []
        label_name = ctx.get_label_name(next)
        goto_end = self.viper.Goto(label_name,
                                   self.to_position(handler.node, ctx),
                                   self.no_info(ctx))
        ctx.var_aliases = old_var_aliases
        return [label, body_block] + next_var_set + [goto_end]
