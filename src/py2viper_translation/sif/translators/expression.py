import ast

from py2viper_translation.lib.constants import (
    BOOL_TYPE,
    LIST_TYPE,
)
from py2viper_translation.lib.util import UnsupportedException
from py2viper_translation.sif.lib.context import SIFContext
from py2viper_translation.sif.lib.expr_cache import ExprCache
from py2viper_translation.sif.lib.program_nodes import SIFPythonField
from py2viper_translation.sif.translators.func_triple_domain_factory import (
    FuncTripleDomainFactory as FTDF,
)
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
            if not len(self._translated_exprs[node]):
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

    def translate_Subscript(
            self, node: ast.Subscript, ctx: SIFContext) -> StmtsAndExpr:
        if not isinstance(node.slice, ast.Index):
            raise UnsupportedException(node, "Slices not supported yet.")
        if node in self._translated_exprs:
            expr = self._translated_exprs[node].next()
            if not len(self._translated_exprs[node]):
                del self._translated_exprs[node]
            return [], expr

        # Translate the target expression of the subscript.
        target_type = self.get_type(node.value, ctx)
        if target_type.name != LIST_TYPE:
            raise UnsupportedException("Subscript only supported for lists.")
        target_stmts, target_expr = self.translate_expr(node.value, ctx)
        with ctx.prime_ctx():
            target_stmts_p, target_expr_p = self.translate_expr(node.value, ctx)

        # Translate the index expression of the subscript.
        index_type = self.get_type(node.slice.value, ctx)
        index_stmts, index_expr = self.translate_expr(node.slice.value, ctx)
        with ctx.prime_ctx():
            index_stmts_p, index_expr_p = self.translate_expr(
                node.slice.value, ctx)

        # Call __getitem__ and get results out of FuncTriple.
        position = self.to_position(node, ctx)
        info = self.no_info(ctx)
        args = [target_expr, target_expr_p, index_expr, index_expr_p,
                ctx.current_tl_var_expr]
        arg_types = [target_type, target_type, index_type, index_type,
                     ctx.module.global_module.classes[BOOL_TYPE]]
        func_app = self.get_function_call(
            target_type, '__getitem__', args, arg_types, node, ctx)
        res_expr = self.config.func_triple_factory.get_call(
            FTDF.GET, [func_app], target_type, position, info, ctx)
        res_expr_p = self.config.func_triple_factory.get_call(
            FTDF.GET_PRIME, [func_app], target_type, position, info, ctx)
        # Update the current timeLevel var expression.
        tl_expr = self.config.func_triple_factory.get_call(
            FTDF.GET_TL, [func_app], target_type, position, info, ctx)
        ctx.current_tl_var_expr = tl_expr

        # Cache translated expression.
        cache = ExprCache()
        cache.add_result(res_expr_p)
        cache.add_result(tl_expr)
        self._translated_exprs[node] = cache

        return (target_stmts + target_stmts_p + index_stmts + index_stmts_p,
                res_expr)








