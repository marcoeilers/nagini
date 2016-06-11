from py2viper_translation.lib.constants import PRIMITIVES
from py2viper_translation.lib.typedefs import (
    DomainFuncApp,
    Expr,
)
from py2viper_translation.lib.util import (
    get_body_start_index,
    InvalidProgramException,
)
from py2viper_translation.sif.lib.context import SIFContext
from py2viper_translation.sif.lib.program_nodes import (
    SIFPythonMethod,
)
from py2viper_translation.translators.method import MethodTranslator
from typing import List


class SIFMethodTranslator(MethodTranslator):
    """
    SIF version of the MethodTranslator.
    """
    def _translate_pres(self, method: SIFPythonMethod,
                        ctx: SIFContext):
        pres = super()._translate_pres(method, ctx)
        ctx.set_prime_ctx()
        pres += super()._translate_pres(method, ctx)
        ctx.set_normal_ctx()
        return pres

    def _translate_posts(self, method: SIFPythonMethod,
                         err_var: 'viper.ast.LocalVar',
                         ctx: SIFContext):
        posts = super()._translate_posts(method, err_var, ctx)
        ctx.set_prime_ctx()
        posts += super()._translate_posts(method, err_var, ctx)
        ctx.set_normal_ctx()
        return posts

    def _create_typeof_pres(self, func: SIFPythonMethod,
                            is_constructor: bool,
                            ctx: SIFContext) -> List[DomainFuncApp]:
        pres = []
        args = func.args
        for arg in args.values():
            if not (arg.type.name in PRIMITIVES or
                        (is_constructor and arg == next(iter(args)))):
                pres.append(self.get_parameter_typeof(arg, ctx))
                pres.append(self.get_parameter_typeof(arg.var_prime, ctx))

        return pres

    def _create_method_prolog(self, method: SIFPythonMethod,
                              ctx: SIFContext):
        # newTimeLevel := timeLevel
        tl_stmt = self.viper.LocalVarAssign(method.new_tl_var.ref,
                                            method.tl_var.ref,
                                            self.no_position(ctx),
                                            self.no_info(ctx))
        return [tl_stmt]

    def _create_init_pres(self, method: SIFPythonMethod,
                          ctx: SIFContext) -> List[Expr]:
        """
        Generates preconditions specific to the '__init__' method.
        """
        self_var = method.args[next(iter(method.args))]
        self_ref = self_var.ref
        self_ref_prime = self_var.var_prime.ref
        fields = method.cls.get_all_fields()
        sil_fields = method.cls.get_all_sil_fields()
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
        if func.cls:
            self_var = next(iter(func.args.values()))
            not_null = self.viper.NeCmp(self_var.ref,
                self.viper.NullLit(self.no_position(ctx), self.no_info(ctx)),
                self.no_position(ctx), self.no_info(ctx))
            not_null_p = self.viper.NeCmp(self_var.var_prime.ref,
                self.viper.NullLit(self.no_position(ctx), self.no_info(ctx)),
                self.no_position(ctx), self.no_info(ctx))
            pres = [not_null, not_null_p] + pres
        # create postconditions
        posts = []
        for post in func.postcondition:
            stmt, expr = self.translate_expr(post, ctx)
            ctx.set_prime_ctx()
            stmt_p, expr_p = self.translate_expr(post, ctx)
            ctx.set_normal_ctx()
            if stmt or stmt_p:
                raise InvalidProgramException(post, 'purity.violated')
            posts.append(expr)
            posts.append(expr_p)
        # create typeof preconditions
        pres = self._create_typeof_pres(func, False, ctx) + pres
        # TODO(shitz): Add result type post-condition.
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
