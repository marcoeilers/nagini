"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import ast

from nagini_translation.lib.constants import (
    CALLABLE_TYPE,
    INT_TYPE,
    PRIMITIVES,
    PSEQ_TYPE,
)
from nagini_translation.lib.program_nodes import (
    PythonClass,
    PythonIOOperation,
    PythonMethod,
    PythonType,
    SilverType,
)
from nagini_translation.lib.jvmaccess import JVM
from nagini_translation.lib.resolver import get_type as do_get_type
from nagini_translation.lib.typedefs import (
    Expr,
)
from nagini_translation.lib.typeinfo import TypeInfo
from nagini_translation.lib.viper_ast import ViperAST
from nagini_translation.translators.abstract import (
    Context,
    TranslatorConfig,
)
from nagini_translation.translators.common import CommonTranslator
from typing import Optional


class TypeTranslator(CommonTranslator):

    def __init__(self, config: TranslatorConfig, jvm: JVM, source_file: str,
                 type_info: TypeInfo, viper_ast: ViperAST) -> None:
        super().__init__(config, jvm, source_file, type_info, viper_ast)

    @property
    def builtins(self):
        return {'builtins.int': self.viper.Int,
                'builtins.bool': self.viper.Bool,
                'builtins.PSeq': self.viper.SeqType(self.viper.Ref),
                'builtins.PSet': self.viper.SetType(self.viper.Ref),
                'builtins.PMultiset': self.viper.MultisetType(self.viper.Ref),
                }

    def translate_type(self, cls: PythonClass,
                       ctx: Context) -> 'silver.ast.Type':
        """
        Translates the given type to the corresponding Viper type (Int, Ref, ..)
        """
        if isinstance(cls, SilverType):
            return cls.type
        elif cls.name == CALLABLE_TYPE:
            ctx.are_function_constants_used = True
            return self.viper.function_domain_type()
        elif cls.name in PRIMITIVES:
            cls = cls.try_box()
            return self.builtins['builtins.' + cls.name]
        elif cls.name == 'type':
            return self.type_factory.type_type()
        else:
            return self.viper.Ref

    def get_type(self, node: ast.AST, ctx: Context) -> Optional[PythonType]:
        """
        Returns the type of the expression represented by node as a PythonType,
        or None if the type is void.
        """
        container = ctx.actual_function if ctx.actual_function else ctx.module
        containers = [ctx]
        if ctx.current_class:
            containers.append(ctx.current_class)
        if isinstance(container, (PythonMethod, PythonIOOperation)):
            containers.append(container)
            containers.extend(container.module.get_included_modules())
        else:
            # Assume module
            containers.extend(container.get_included_modules())
        return do_get_type(node, containers, container)

    def type_check(self, lhs: Expr, type: PythonType,
                   position: 'silver.ast.Position',
                   ctx: Context, inhale_exhale: bool=True) -> Expr:
        """
        Returns a type check expression. This may return a simple isinstance
        for simple types, or include information about type arguments for
        generic types, or things like the lengths for tuples.
        """
        inhale_exhale = False
        if type is None:
            none_type = ctx.module.global_module.classes['NoneType']
            return self.type_factory.type_check(lhs, none_type, position, ctx)
        elif type.name == 'type':
            return self.viper.TrueLit(position, self.no_info(ctx))
        else:
            result = self.type_factory.type_check(lhs, type, position, ctx)
            strict_inv = self._strict_int_pseq_invariant(lhs, type, position, ctx)
            if strict_inv is not None:
                result = self.viper.And(result, strict_inv, position,
                                        self.no_info(ctx))
            return result

    def _strict_int_pseq_invariant(self, pseq_ref: Expr, pseq_type: PythonType,
                                   pos: 'silver.ast.Position',
                                   ctx: Context) -> Optional[Expr]:
        # Mirror of _strict_int_list_invariant for PSeq[int]: in strict-int
        # mode, every element of a PSeq[int] must have exactly type int. Since
        # PSeq is a value type with no permission to attach the invariant to,
        # we conjoin it with the type check that establishes
        # `typeof(s) == PSeq(int())`. Returns None when not applicable.
        if not ctx.strict_int:
            return None
        if pseq_type is None or pseq_type.name != PSEQ_TYPE:
            return None
        if not getattr(pseq_type, 'type_args', None):
            return None
        if pseq_type.type_args[0].name != INT_TYPE:
            return None
        info = self.no_info(ctx)
        seq_class = ctx.module.global_module.classes[PSEQ_TYPE]
        sil_seq = self.get_function_call(seq_class, '__sil_seq__',
                                         [pseq_ref], [None], None, ctx, pos)
        i_decl = self.viper.LocalVarDecl('i', self.viper.Int, pos, info)
        i_ref = self.viper.LocalVar('i', self.viper.Int, pos, info)
        seq_at_i = self.viper.SeqIndex(sil_seq, i_ref, pos, info)
        zero = self.viper.IntLit(0, pos, info)
        length = self.viper.SeqLength(sil_seq, pos, info)
        bounds = self.viper.And(
            self.viper.LeCmp(zero, i_ref, pos, info),
            self.viper.LtCmp(i_ref, length, pos, info),
            pos, info)
        int_cls = ctx.module.global_module.classes[INT_TYPE]
        int_lit = self.type_factory.translate_type_literal(int_cls, pos, ctx)
        typeof_at_i = self.type_factory.typeof(seq_at_i, ctx)
        eq = self.viper.EqCmp(typeof_at_i, int_lit, pos, info)
        body = self.viper.Implies(bounds, eq, pos, info)
        trigger = self.viper.Trigger([seq_at_i], pos, info)
        return self.viper.Forall([i_decl], [trigger], body, pos, info)
