from nagini_translation.lib.program_nodes import GenericType, MethodType
from nagini_translation.lib.typedefs import (
    Expr,
    Stmt,
)
from nagini_translation.lib.util import (
    get_body_start_index,
    InvalidProgramException,
)
from nagini_translation.sif.lib.context import SIFContext
from nagini_translation.sif.lib.program_nodes import (
    SIFPythonMethod,
)
from nagini_translation.sif.translators.func_triple_domain_factory import (
    FuncTripleDomainFactory as FTDF,
)
from nagini_translation.translators.method import MethodTranslator
from typing import List


class SIFMethodTranslator(MethodTranslator):
    """
    SIF version of the MethodTranslator.
    """
    def _create_tl_post(self, method: SIFPythonMethod, ctx: SIFContext) -> Expr:
        """
        Creates a check whether a method/function is timelevel preserving.
        """
        pos = self.no_position(ctx)
        info = self.no_info(ctx)
        tl_expr = method.tl_var.ref()
        if method.pure:
            type_ = self.config.func_triple_factory.get_type(method.type, ctx)
            res = self.viper.Result(type_, pos, info)
            new_tl_expr = self.config.func_triple_factory.get_call(FTDF.GET_TL,
                [res], method.type, pos, info, ctx)
        else:
            new_tl_expr = method.new_tl_var.ref()

        not_tl = self.viper.Not(tl_expr, pos, info)
        not_new_tl = self.viper.Not(new_tl_expr, pos, info)

        return self.viper.Implies(not_tl, not_new_tl, pos, info)

    def _translate_pres(self, method: SIFPythonMethod,
                        ctx: SIFContext):
        ctx.in_pres = True
        pres = []
        for pre, aliases in method.precondition:
            with ctx.additional_aliases(aliases):
                ctx.current_tl_var_expr = None
                stmt, expr = self.translate_expr(pre, ctx, impure=True,
                                                 target_type=self.viper.Bool)
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
        ctx.in_pres = False
        return pres

    def _translate_posts(self, method: SIFPythonMethod,
                         err_var: 'viper.ast.LocalVar',
                         ctx: SIFContext):
        ctx.in_posts = True
        ctx.obligation_context.is_translating_posts = True
        posts = []
        no_error = self.viper.EqCmp(err_var,
                                    self.viper.NullLit(self.no_position(ctx),
                                                       self.no_info(ctx)),
                                    self.no_position(ctx), self.no_info(ctx))
        for post, aliases in method.postcondition:
            with ctx.additional_aliases(aliases):
                ctx.current_tl_var_expr = None
                stmt, expr = self.translate_expr(post, ctx, impure=True,
                                                 target_type=self.viper.Bool)
            if stmt:
                raise InvalidProgramException(post, 'purity.violated')
            if method.declared_exceptions:
                expr = self.viper.Implies(no_error, expr,
                                          self.to_position(post, ctx),
                                          self.no_info(ctx))
            posts.append(expr)

        ctx.obligation_context.is_translating_posts = False
        # !tl ==> !new_tl
        if method.preserves_tl:
            posts.append(self._create_tl_post(method, ctx))
        ctx.in_posts = False
        return posts

    def _create_init_pres(self, method: SIFPythonMethod,
                          ctx: SIFContext) -> List[Expr]:
        """
        Generates preconditions specific to the '__init__' method.
        """
        self_var = method.args[next(iter(method.args))]
        self_ref = self_var.ref()
        self_ref_prime = self_var.var_prime.ref()
        fields = method.cls.all_fields
        sil_fields = method.cls.all_sil_fields
        sil_fields_prime = [f.field_prime.sil_field for f in fields]
        # Generate permissions for all fields.
        accs = self.get_all_field_accs(sil_fields, self_ref,
                                       self.to_position(method.node, ctx),
                                       ctx)
        # Generate permissions for all field_primes.
        accs_prime = self.get_all_field_accs(sil_fields_prime, self_ref,
                                             self.to_position(method.node, ctx),
                                             ctx)
        # Requires self != null && self_p != null.
        null = self.viper.NullLit(self.no_position(ctx), self.no_info(ctx))
        not_null = self.viper.NeCmp(self_ref, null, self.no_position(ctx),
                                    self.no_info(ctx))
        not_null_prime = self.viper.NeCmp(self_ref_prime, null,
                                          self.no_position(ctx),
                                          self.no_info(ctx))
        # Requires self == self'.
        equal = self.viper.EqCmp(self_ref, self_ref_prime,
                                 self.no_position(ctx), self.no_info(ctx))

        return [not_null, not_null_prime, equal] + accs + accs_prime

    def _create_local_vars_for_params(self, method: SIFPythonMethod,
                                      ctx: SIFContext) -> List[Stmt]:
        """Creates LocalVarAssigns for the TL parameter."""
        # TODO(shitz): Should at some point also introduce local vars for params
        # but this needs some more work with ctx.var_aliases.
        # __new_tl := __tl
        tl_stmt = self.viper.LocalVarAssign(method.new_tl_var.ref(),
                                            method.tl_var.ref(),
                                            self.no_position(ctx),
                                            self.no_info(ctx))

        return [tl_stmt]

    def translate_function(self, func: SIFPythonMethod,
                           ctx: SIFContext) -> 'silver.ast.Function':
        """
        Translate a pure Python function to a Viper function. The Viper function
        returns a tuple (res, res', timeLevel). Bools and ints get boxed.
        """
        # TODO: We should really have a save/restore_context method and call it
        # automatically at the beginning and end of each translate_* method.
        old_function = ctx.current_function
        ctx.current_function = func
        # Reset ctx to remove any artifacts from previously translated units.
        ctx.reset()
        # Create a FuncTriple type.
        type_ = self.config.func_triple_factory.get_type(func.type, ctx)

        args = self._translate_params(func, ctx)
        if func.declared_exceptions:
            raise InvalidProgramException(func.node,
                                          'function.throws.exception')
        # create preconditions
        pres = self._translate_pres(func, ctx)
        # create postconditions
        ctx.in_posts = True
        posts = []
        for post, aliases in func.postcondition:
            with ctx.additional_aliases(aliases):
                stmt, expr = self.translate_expr(post, ctx,
                                                 target_type=self.viper.Bool)
            if stmt:
                raise InvalidProgramException(post, 'purity.violated')
            posts.append(expr)
        # Add check that timelevel is preserved.
        if func.preserves_tl:
            posts.append(self._create_tl_post(func, ctx))
        ctx.in_posts = False
        # create typeof preconditions
        pres = self._create_typeof_pres(func, False, ctx) + pres
        # Add result type post-condition.
        result_type = self.config.func_triple_factory.get_type(func.type, ctx)
        result = self.viper.Result(result_type, self.no_position(ctx),
                                   self.no_info(ctx))
        res_fst = self.config.func_triple_factory.get_call(FTDF.GET, [result],
                                                           func.type,
                                                           self.no_position(ctx),
                                                           self.no_info(ctx),
                                                           ctx)
        res_snd = self.config.func_triple_factory.get_call(FTDF.GET_PRIME,
                                                           [result],
                                                           func.type,
                                                           self.no_position(
                                                               ctx),
                                                           self.no_info(ctx),
                                                           ctx)
        return_type_posts = []
        return_type_posts.append(self.type_check(res_fst, func.type,
                                                 self.no_position(ctx),
                                                 ctx))
        return_type_posts.append(self.type_check(res_snd, func.type,
                                                 self.no_position(ctx),
                                                 ctx))
        posts = return_type_posts + posts
        statements = func.node.body
        body_index = get_body_start_index(statements)
        # translate body
        body = self.translate_exprs(statements[body_index:], func, ctx)
        ctx.current_function = old_function
        return self.viper.Function(func.sil_name, args, type_, pres,
                                   posts, body, self.no_position(ctx),
                                   self.no_info(ctx))

    def translate_method(self, method: SIFPythonMethod,
                         ctx: SIFContext) -> 'silver.ast.Method':
        # Reset ctx to remove any artifacts from previously translated units.
        ctx.reset()
        return super().translate_method(method, ctx)

    def _create_result_type_post(self, method: SIFPythonMethod, error_var_ref,
                                 ctx: SIFContext):
        if not method.type:
            return []
        res = self._create_single_result_post(method, error_var_ref,
                                              ctx.result_var.ref(method.node,
                                                                 ctx), ctx)
        res_p = self._create_single_result_post(method, error_var_ref,
            ctx.result_var.var_prime.ref(method.node, ctx), ctx)
        return res + res_p
