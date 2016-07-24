"""Public interface to obligation translator."""


import ast

from typing import List, Tuple

from py2viper_translation.lib.context import Context
from py2viper_translation.lib.program_nodes import (
    PythonMethod,
)
from py2viper_translation.lib.typedefs import (
    Field,
    Predicate,
    Stmt,
    StmtsAndExpr,
)
from py2viper_translation.lib.util import (
    UnsupportedException,
)
from py2viper_translation.translators.common import CommonTranslator


class ObligationTranslator(CommonTranslator):
    """Translator for obligations."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # TODO: This method is a stub.

    def enter_loop_translation(self, node, ctx) -> None:
        """Update context with info needed to translate loop."""
        # TODO: This method is a stub.

    def leave_loop_translation(self, ctx) -> None:
        """Remove loop translation info from context."""
        # TODO: This method is a stub.

    def translate_obligation_contractfunc_call(
            self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """Translate a call to obligation contract function."""
        raise UnsupportedException(node, 'Method is a stub.')

    def get_obligation_preamble(
            self,
            ctx: Context) -> Tuple[List[Predicate], List[Field]]:
        """Construct obligation preamble."""
        # TODO: This method is a stub.
        return [], []

    def _find_method_by_sil_name(self, ctx, sil_name) -> PythonMethod:
        for method in ctx.program.methods.values():
            if method.sil_name == sil_name:
                return method
        for cls in ctx.program.classes.values():
            for method in cls.methods.values():
                if method.sil_name == sil_name:
                    return method
        return None

    def create_method_node(
            self, ctx, name, original_args, returns, pres, posts,
            local_vars, body, position, info,
            method=None) -> 'viper_ast.Method':
        """Construct method AST node with additional obligation stuff."""
        # TODO: This method is a stub.

        if method is None:
            method = self._find_method_by_sil_name(ctx, name)
        if method is None:
            # Assume that this is a method that is never called from
            # Python and, as a result, does not need obligation stuff.
            return self.viper.Method(
                name, original_args, returns, pres, posts, local_vars, body,
                position, info)

        # Update arguments.
        args = original_args

        # Update body.
        if isinstance(body, self.jvm.viper.silver.ast.Seqn):
            # Axiomatized method, do nothing with body.
            body_block = body
        else:
            # Convert body to Scala.
            body_block = self.translate_block(
                body, position, info)

        return self.viper.Method(
            name, args, returns, pres, posts, local_vars, body_block,
            position, info)

    def create_method_call_node(
            self, ctx, methodname, original_args, targets, position,
            info, target_method=None, target_node=None) -> List[Stmt]:
        """Construct a method call AST node with obligation stuff."""
        # TODO: This method is a stub.

        statements = []

        # Update arguments.
        args = original_args

        # Call method.
        call = self.viper.MethodCall(methodname, args, targets, position, info)
        statements.append(call)

        return statements

    def create_while_node(
            self, ctx, cond, invariants, local_vars, body, node) -> List[Stmt]:
        """Construct a while loop AST node with obligation stuff."""
        # TODO: This method is a stub.

        position = self.to_position(node, ctx)
        info = self.no_info(ctx)

        statements = []

        body_block = self.translate_block(body,
                                          self.to_position(node, ctx),
                                          self.no_info(ctx))

        loop = self.viper.While(
            cond, invariants, local_vars, body_block, position, info)
        statements.append(loop)

        return statements
