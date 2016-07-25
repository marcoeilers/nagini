"""Obligation translator in methods."""


import ast

from typing import List

from py2viper_translation.lib.context import Context
from py2viper_translation.lib.typedefs import (
    Method,
    Stmt,
    StmtsAndExpr,
)
from py2viper_translation.lib.util import (
    UnsupportedException,
)
from py2viper_translation.translators.obligation.common import (
    CommonObligationTranslator,
)
from py2viper_translation.translators.obligation.utils import (
    find_method_by_sil_name,
)


class MethodObligationTranslator(CommonObligationTranslator):
    """Class for translating obligations in methods."""

    def translate_must_terminate(
            self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """Translate ``MustTerminate`` in loop invariant."""
        raise UnsupportedException(node, 'Method is a stub.')

    def create_method_node(
            self, ctx, name, original_args, returns, pres, posts,
            local_vars, body, position, info,
            method=None) -> Method:
        """Construct method AST node with additional obligation stuff."""
        # TODO: This method is a stub.

        if method is None:
            method = find_method_by_sil_name(ctx, name)
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
