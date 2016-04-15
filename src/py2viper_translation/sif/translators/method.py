from py2viper_translation.lib.program_nodes import PythonMethod
from py2viper_translation.sif.lib.context import SIFContext
from py2viper_translation.sif.lib.program_nodes import SIF_VAR_SUFFIX
from py2viper_translation.translators.abstract import Expr, VarDecl
from py2viper_translation.translators.method import MethodTranslator
from typing import List


class SIFMethodTranslator(MethodTranslator):
    """
    SIF version of the MethodTranslator.
    """
    def _get_results(self, method: PythonMethod,
                     ctx: SIFContext) -> List['viper.ast.LocalVarDecl']:
        results = []
        if method.type is not None:
            type_ = self.translate_type(method.type, ctx)
            results.append(self.viper.LocalVarDecl("_res", type_,
                self.to_position(method.node, ctx), self.no_info(ctx)))
            results.append(self.viper.LocalVarDecl("_res" + SIF_VAR_SUFFIX,
                type_, self.to_position(method.node, ctx), self.no_info(ctx)))
        # Add timeLevel to results.
        results.append(self.viper.LocalVarDecl("newTimeLevel", self.viper.Bool,
            self.no_position(ctx), self.no_info(ctx)))

        return results

    def _get_method_args(self, method: PythonMethod,
                         ctx: SIFContext) -> List[VarDecl]:
        args = []
        for arg in method.args.values():
            args.append(arg.decl)
            args.append(arg.var_prime.decl)

        # Append timeLevel arg.
        args.append(self.viper.LocalVarDecl("timeLevel", self.viper.Bool,
                                            self.no_position(ctx),
                                            self.no_info(ctx)))

        return args

    def _handle_init(self, method: PythonMethod, ctx: SIFContext) -> List[Expr]:
        self_var = method.args[next(iter(method.args))]
        self_ref = self_var.ref
        self_ref_prime = self_var.var_prime.ref
        fields = method.cls.get_all_fields()
        sil_fields = method.cls.get_all_sil_fields()
        sil_fields_prime = [f.field_prime.sil_field for f in fields]
        accs = self.get_all_field_accs(sil_fields, self_ref,
                                       self.to_position(method.node, ctx),
                                       ctx)
        accs_prime = self.get_all_field_accs(sil_fields_prime, self_ref,
                                             self.to_position(method.node, ctx),
                                             ctx)
        null = self.viper.NullLit(self.no_position(ctx), self.no_info(ctx))
        not_null = self.viper.NeCmp(self_ref, null, self.no_position(ctx),
                                    self.no_info(ctx))
        not_null_prime = self.viper.NeCmp(self_ref_prime, null,
                                          self.no_position(ctx),
                                          self.no_info(ctx))
        equal = self.viper.EqCmp(self_ref, self_ref_prime,
                                 self.no_position(ctx), self.no_info(ctx))

        return [not_null, not_null_prime, equal] + accs + accs_prime
