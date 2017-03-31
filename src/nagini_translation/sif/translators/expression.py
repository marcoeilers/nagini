import ast

from nagini_translation.lib.constants import (
    BOOL_TYPE,
    LIST_TYPE,
    PRIMITIVE_BOOL_TYPE,
)
from nagini_translation.lib.program_nodes import PythonType
from nagini_translation.lib.util import UnsupportedException
from nagini_translation.lib.typedefs import (
    Expr,
    StmtsAndExpr,
)
from nagini_translation.sif.lib.context import SIFContext
from nagini_translation.sif.lib.expr_cache import ExprCacheMixin
from nagini_translation.sif.lib.program_nodes import SIFPythonField
from nagini_translation.translators.expression import ExpressionTranslator
from typing import cast


class SIFExpressionTranslator(ExpressionTranslator, ExprCacheMixin):
    """
    SIF version of the ExpressionTranslator.
    """
    def __init__(self, *args, **kwargs) -> None:
        ExpressionTranslator.__init__(self, *args, **kwargs)
        ExprCacheMixin.__init__(self)

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
        expr = self._try_cache(node)
        if expr:
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

        self._cache_results(node, [res_var.var_prime.ref()])

        return stmts, res_var.ref(node, ctx)

    def translate_Subscript(
            self, node: ast.Subscript, ctx: SIFContext) -> StmtsAndExpr:
        if not isinstance(node.slice, ast.Index):
            raise UnsupportedException(node, "Slices not supported yet.")
        expr = self._try_cache(node)
        if expr:
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
        res_expr, res_expr_p, tl_expr = \
            self.config.func_triple_factory.extract_results(
                func_app, target_type, position, info, ctx)
        ctx.current_tl_var_expr = tl_expr

        self._cache_results(node, [res_expr_p, tl_expr])

        return (target_stmts + target_stmts_p + index_stmts + index_stmts_p,
                res_expr)

    def _translate_contains(
            self, left: Expr, right: Expr, left_type: PythonType,
            right_type: PythonType, node: ast.AST,
            ctx: SIFContext) -> StmtsAndExpr:
        expr = self._try_cache(node)
        if expr:
            return [], expr
        # Translate the left and right expressions in the prime context.
        with ctx.prime_ctx():
            left_stmts_p, left_p = self.translate_expr(node.left, ctx)
            right_stmts_p, right_p = self.translate_expr(
                node.comparators[0], ctx)

        bool_type = ctx.module.global_module.classes[PRIMITIVE_BOOL_TYPE]
        args = [right, right_p, left, left_p, ctx.current_tl_var_expr]
        arg_types = [right_type, right_type, left_type, left_type, bool_type]
        func_app = self.get_function_call(
            right_type, '__contains__', args, arg_types, node, ctx)
        position = self.to_position(node, ctx)
        info = self.no_info(ctx)
        res_expr, res_expr_p, tl_expr = \
            self.config.func_triple_factory.extract_results(
                func_app, bool_type, position, info, ctx)
        if isinstance(node.ops[0], ast.NotIn):
            res_expr = self.viper.Not(res_expr, position, info)
            res_expr_p = self.viper.Not(res_expr_p, position, info)
        # Update the current timeLevel var expression.
        ctx.current_tl_var_expr = tl_expr

        self._cache_results(node, [res_expr_p, tl_expr])

        return left_stmts_p + right_stmts_p, res_expr
