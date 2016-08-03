"""Common code for obligation translators."""


import abc
import ast

from py2viper_translation.lib import expressions as expr
from py2viper_translation.lib.context import Context
from py2viper_translation.lib.jvmaccess import JVM
from py2viper_translation.lib.typedefs import (
    StmtsAndExpr,
)
from py2viper_translation.lib.typeinfo import TypeInfo
from py2viper_translation.lib.util import (
    InvalidProgramException,
)
from py2viper_translation.lib.viper_ast import ViperAST
from py2viper_translation.translators.abstract import TranslatorConfig
from py2viper_translation.translators.common import CommonTranslator
from py2viper_translation.translators.obligation.manager import (
    ObligationManager,
)
from py2viper_translation.translators.obligation.types.must_terminate import (
    MustTerminateObligationInstance,
)
from py2viper_translation.translators.obligation.types.must_invoke import (
    MustInvokeObligationInstance,
)
from py2viper_translation.translators.obligation.obligation_info import (
    BaseObligationInfo,
)


class CommonObligationTranslator(CommonTranslator):
    """Base class for obligation translators."""

    def __init__(self, config: TranslatorConfig, jvm: JVM, source_file: str,
                 type_info: TypeInfo, viper_ast: ViperAST,
                 obligation_manager: ObligationManager) -> None:
        super().__init__(config, jvm, source_file, type_info, viper_ast)
        self._obligation_manager = obligation_manager

    @abc.abstractmethod
    def _get_obligation_info(self, ctx: Context) -> BaseObligationInfo:
        """Get the relevant obligation info."""

    @abc.abstractmethod
    def _create_must_terminate_use(
            self, obligation_instance: MustTerminateObligationInstance,
            ctx: Context) -> expr.InhaleExhale:
        """Create MustTerminate use from the obligation instance."""

    def translate_must_terminate(
            self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """Translate ``MustTerminate`` in a contract."""
        obligation_info = self._get_obligation_info(ctx)
        guarded_obligation_instance = obligation_info.get_instance(node)
        obligation_instance = guarded_obligation_instance.obligation_instance
        assert isinstance(obligation_instance,
                          MustTerminateObligationInstance)

        inhale_exhale = self._create_must_terminate_use(
            obligation_instance, ctx)

        position = self.to_position(node, ctx)
        info = self.no_info(ctx)
        expression = inhale_exhale.translate(self, ctx, position, info)
        return ([], expression)

    @abc.abstractmethod
    def _create_must_invoke_use(
            self, obligation_instance: MustInvokeObligationInstance,
            ctx: Context) -> expr.InhaleExhale:
        """Create MustInvoke use from the obligation instance."""

    def translate_must_invoke(
            self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """Translate ``token`` in a contract."""
        # TODO: Clean up code duplication.
        obligation_info = self._get_obligation_info(ctx)
        guarded_obligation_instance = obligation_info.get_instance(node)
        obligation_instance = guarded_obligation_instance.obligation_instance
        assert isinstance(obligation_instance,
                          MustInvokeObligationInstance)

        if obligation_instance.is_fresh():
            # Fresh obligations are allowed only in postconditions.
            if ctx.obligation_context.is_translating_loop():
                # TODO: Think how to lift this restriction. The problem
                # is that unlike in original paper, we do not perform
                # explicit conversion of fresh obligations into bounded
                # ones. Can we do that by using InhaleExhale pair in
                # loop invariant?
                raise InvalidProgramException(
                    node, 'obligation.fresh.in_loop')
            elif not ctx.obligation_context.is_translating_posts:
                raise InvalidProgramException(
                    node, 'obligation.fresh.in_precondition')

        inhale_exhale = self._create_must_invoke_use(
            obligation_instance, ctx)

        position = self.to_position(node, ctx)
        info = self.no_info(ctx)
        expression = inhale_exhale.translate(self, ctx, position, info)
        return ([], expression)
