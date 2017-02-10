import ast

from py2viper_translation.lib.constants import (
    BOOL_TYPE,
    LIST_TYPE,
)
from py2viper_translation.sif.lib.context import SIFContext
from py2viper_translation.sif.lib.expr_cache import ExprCache
from py2viper_translation.sif.lib.program_nodes import SIFPythonField
from py2viper_translation.translators.abstract import StmtsAndExpr
from py2viper_translation.translators.expression import ExpressionTranslator
from typing import cast


class SIFExpressionTranslator(ExpressionTranslator):
    """
    SIF version of the ExpressionTranslator.
    """
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._translated_exprs = {}  # Map[ast.Node, ExprCache]

    def translate_Attribute(self, node: ast.Attribute,
                            ctx: SIFContext) -> StmtsAndExpr:
        stmt, receiver = self.translate_expr(node.value, ctx)
        field = cast(SIFPythonField, self._lookup_field(node, ctx))
        if ctx.use_prime:
            field = field.field_prime
        return (stmt, self.viper.FieldAccess(receiver, field.sil_field,
                                             self.to_position(node, ctx),
                                             self.no_info(ctx)))

    def translate_List(self, node: ast.List, ctx: SIFContext) -> StmtsAndExpr:
        if node in self._translated_exprs:
            assert len(self._translated_exprs[node]) == 1
            expr = self._translated_exprs[node].next()
            del self._translated_exprs[node]
            return [], expr
        list_class = ctx.module.global_module.classes[LIST_TYPE]
        res_var = ctx.current_function.create_variable(
            LIST_TYPE, list_class, self.translator)

        bool_type = ctx.module.global_module.classes[BOOL_TYPE]
        constr_call = self.get_method_call(
            list_class, '__init__', [ctx.current_tl_var_expr], [bool_type],
            [res_var.ref(), res_var.var_prime.ref(), ctx.current_tl_var_expr],
            node, ctx)

        stmts = constr_call
        # Inhale the type of the newly created list (including type arguments).
        list_type = self.get_type(node, ctx)
        pos = self.to_position(node, ctx)
        stmts.append(self.viper.Inhale(
            self.type_check(res_var.ref(node, ctx), list_type, pos, ctx),
            pos, self.no_info(ctx)))

        # Append elements.
        for el in node.elts:
            el_type = self.get_type(el, ctx)
            el_stmts, el_expr = self.translate_expr(el, ctx)
            with ctx.prime_ctx():
                el_stmts_p, el_expr_p = self.translate_expr(el, ctx)
            assert el_expr
            args = [res_var.ref(), res_var.var_prime.ref(), el_expr, el_expr_p,
                    ctx.current_tl_var_expr]
            arg_types = [None, None, el_type, el_type, bool_type]
            append_call = self.get_method_call(
                list_class, 'append', args, arg_types,
                [ctx.current_tl_var_expr], node, ctx)
            stmts += el_stmts + el_stmts_p + append_call

        # Cache translated expression.
        cache = ExprCache()
        cache.add_result(res_var.var_prime.ref())
        self._translated_exprs[node] = cache

        return stmts, res_var.ref(node, ctx)





