"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Common code for obligation translators."""


import abc
import ast

from nagini_translation.lib import silver_nodes as sil
from nagini_translation.lib.context import Context
from nagini_translation.lib.jvmaccess import JVM
from nagini_translation.lib.typedefs import (
    StmtsAndExpr,
)
from nagini_translation.lib.typeinfo import TypeInfo
from nagini_translation.lib.util import (
    join_expressions,
)
from nagini_translation.lib.viper_ast import ViperAST
from nagini_translation.translators.abstract import TranslatorConfig
from nagini_translation.translators.common import CommonTranslator
from nagini_translation.translators.obligation.manager import (
    ObligationManager,
)
from nagini_translation.translators.obligation.obligation_info import (
    BaseObligationInfo,
)
from nagini_translation.translators.obligation.types.base import (
    ObligationInstance,
)
from nagini_translation.translators.obligation.types.must_invoke import (
    MustInvokeObligationInstance,
)
from nagini_translation.translators.obligation.types.must_release import (
    MustReleaseObligationInstance,
)
from nagini_translation.translators.obligation.types.must_terminate import (
    MustTerminateObligationInstance,
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
    def _create_obligation_instance_use(
            self, obligation_instance: ObligationInstance,
            ctx: Context) -> sil.InhaleExhale:
        """Create obligation use from the obligation instance."""

    def _translate_obligation_use(
            self, node: ast.Call, ctx: Context,
            expected_type: type) -> StmtsAndExpr:
        obligation_info = self._get_obligation_info(ctx)
        guarded_obligation_instance = obligation_info.get_instance(node)
        obligation_instance = guarded_obligation_instance.obligation_instance
        assert isinstance(obligation_instance, expected_type)

        exprs_with_rules = self._create_obligation_instance_use(
            obligation_instance, ctx)

        info = self.no_info(ctx)
        translated_expressions = []
        for expression, rules in exprs_with_rules:
            position = self.to_position(node, ctx, rules=rules)
            translated_expression = expression.translate(
                self, ctx, position, info)
            translated_expressions.append(translated_expression)
        and_operator = (
            lambda left, right:
            self.viper.And(left, right, position, info))
        return ([], join_expressions(and_operator, translated_expressions))

    def translate_must_invoke(
            self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """Translate ``token`` in a contract."""
        return self._translate_obligation_use(
            node, ctx, MustInvokeObligationInstance)

    def translate_may_invoke(
            self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """Translate ``ctoken`` in a contract."""
        obligation = self._obligation_manager.must_invoke_obligation
        use = obligation.create_ctoken_use(node)
        position = self.to_position(node, ctx)
        return ([], use.translate(self, ctx, position, self.no_info(ctx)))

    def translate_must_release(
            self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """Translate ``MustRelease`` in a contract."""
        return self._translate_obligation_use(
            node, ctx, MustReleaseObligationInstance)

    def translate_must_terminate(
            self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """Translate ``MustTerminate`` in a contract."""
        return self._translate_obligation_use(
            node, ctx, MustTerminateObligationInstance)
