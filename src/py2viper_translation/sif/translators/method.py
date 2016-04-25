from py2viper_translation.lib.constants import PRIMITIVES
from py2viper_translation.sif.lib.context import SIFContext
from py2viper_translation.sif.lib.program_nodes import (
    SIFPythonMethod,
    SIFPythonVar,
)
from py2viper_translation.translators.abstract import (
    DomainFuncApp,
    Expr,
    Stmt,
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
        ctx.use_prime = True
        pres += super()._translate_pres(method, ctx)
        ctx.use_prime = False
        return pres

    def _translate_posts(self, method: SIFPythonMethod,
                         err_var: 'viper.ast.LocalVar',
                         ctx: SIFContext):
        posts = super()._translate_posts(method, err_var, ctx)
        ctx.use_prime = True
        posts += super()._translate_posts(method, err_var, ctx)
        ctx.use_prime = False
        return posts

    def _create_typeof_pres(self, args: List[SIFPythonVar],
                            is_constructor: bool,
                            ctx: SIFContext) -> List[DomainFuncApp]:
        pres = []
        for arg in args.values():
            if not (arg.type.name in PRIMITIVES or
                        (is_constructor and arg == next(iter(args)))):
                pres.append(self.get_parameter_typeof(arg, ctx))
                pres.append(self.get_parameter_typeof(arg.var_prime, ctx))

        return pres

    def _create_method_epilog(self, method: SIFPythonMethod,
                              ctx: SIFContext) -> List[Stmt]:
        # newTimeLevel := timeLevel
        tl_stmt = self.viper.LocalVarAssign(method.new_tl_var.ref,
                                            method.tl_var.ref,
                                            self.no_position(ctx),
                                            self.no_info(ctx))
        return super()._create_method_epilog(method, ctx) + [tl_stmt]

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
