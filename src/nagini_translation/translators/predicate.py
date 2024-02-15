"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import ast
import copy

from nagini_translation.lib.constants import BOOL_TYPE
from nagini_translation.lib.errors import rules
from nagini_translation.lib.program_nodes import PythonMethod
from nagini_translation.lib.util import InvalidProgramException
from nagini_translation.translators.abstract import Context
from nagini_translation.translators.common import CommonTranslator
from toposort import toposort_flatten
from typing import List, Tuple


class PredicateTranslator(CommonTranslator):

    def translate_predicate(self, pred: PythonMethod,
                            ctx: Context) -> 'ast.silver.Predicate':
        """
        Translates pred to a Silver predicate.
        """
        if not pred.type or pred.type.name != BOOL_TYPE:
            raise InvalidProgramException(pred.node, 'invalid.predicate')
        assert ctx.current_function is None
        ctx.current_function = pred
        args = []
        arg_types = self.viper.TrueLit(self.no_position(ctx), self.no_info(ctx))
        for name, arg in pred.args.items():
            args.append(arg.decl)
            arg_type = self.type_check(arg.ref(), arg.type,
                                       self.no_position(ctx), ctx)
            arg_types = self.viper.And(arg_types, arg_type,
                                       self.no_position(ctx), self.no_info(ctx))
        if len(pred.node.body) != 1:
            raise InvalidProgramException(pred.node,
                                          'invalid.predicate')

        if pred.contract_only:
            body = None
        else:
            content = pred.node.body[0]
            if isinstance(content, ast.Return):
                content = content.value
            stmt, body = self.translate_expr(
                content,
                ctx, impure=True,
                target_type=self.viper.Bool)
            if stmt:
                raise InvalidProgramException(pred.node,
                                              'invalid.predicate')
            body = self.viper.And(arg_types, body, self.no_position(ctx),
                                  self.no_info(ctx))
        ctx.current_function = None
        return self.viper.Predicate(pred.sil_name, args, body,
                                    self.to_position(pred.node, ctx),
                                    self.no_info(ctx))

    def translate_predicate_family(self, root: PythonMethod,
                                   preds: List[PythonMethod],
                                   ctx: Context) -> Tuple[List['ast.silver.Predicate'], List['ast.silver.Method']]:
        """
        Translates the methods in preds, whose root (which they all override)
        is root, to a family-predicate in Silver.
        """
        no_info = self.no_info(ctx)
        dependencies = {}
        for pred in preds:
            value = {pred.overrides} if pred.overrides else set()
            dependencies[pred] = value
            if pred.contract_only != root.contract_only:
                raise InvalidProgramException(pred.node, 'partially.abstract.predicate.family')
        sorted = toposort_flatten(dependencies, False)

        name = root.sil_name
        args = []
        self_var_ref = root.args[next(iter(root.args))].ref()
        true_lit = self.viper.TrueLit(self.no_position(ctx), self.no_info(ctx))
        arg_types = true_lit
        self.bind_type_vars(root, ctx)
        for arg in root.args.values():
            args.append(arg.decl)
            arg_type = self.type_check(arg.ref(), arg.type,
                                       self.no_position(ctx), ctx)
            arg_types = self.viper.And(arg_types, arg_type,
                                       self.no_position(ctx), self.no_info(ctx))
        unknown_type_condition = true_lit
        self_framing_check_methods = []

        body = None
        assert not ctx.var_aliases
        for instance in sorted:
            if root.contract_only:
                # do not generate any body
                continue
            ctx.var_aliases = {}
            assert not ctx.current_function
            if instance.type.name != BOOL_TYPE:
                raise InvalidProgramException(instance.node,
                                              'invalid.predicate')
            ctx.current_function = instance
            ctx.module = instance.module
            self.bind_type_vars(instance, ctx)
            # Replace variables in instance by variables in root, since we use the
            # parameter names from root.
            for root_name, current_name in zip(root.args.keys(),
                                               instance.args.keys()):
                root_var = root.args[root_name]
                # For the receiver parameter, we need it to have the same sil_name as
                # that of the root, but the type of the current instance when translating
                # it, otherwise some fields/functions/predicates may not be found.
                if root_name == next(iter(root.args.keys())):
                    root_var = copy.copy(root_var)
                    root_var.type = instance.cls
                ctx.set_alias(current_name, root_var)
            actual_body_start = 0
            while (actual_body_start < len(instance.node.body) and
                       isinstance(instance.node.body[actual_body_start], ast.Expr) and
                    isinstance(instance.node.body[actual_body_start].value, ast.Str)):
                actual_body_start += 1
            if len(instance.node.body[actual_body_start:]) != 1:
                raise InvalidProgramException(instance.node,
                                              'invalid.predicate')
            content = instance.node.body[actual_body_start]
            if isinstance(content, ast.Return):
                content = content.value

            stmt, current = self.translate_expr(
                    content,
                    ctx, impure=True,
                    target_type=self.viper.Bool)
            if stmt:
                raise InvalidProgramException(instance.node,
                                              'invalid.predicate')
            instance_pos = self.to_position(instance.node, ctx)
            has_type = self.type_factory.type_check(self_var_ref, instance.cls, instance_pos, ctx)
            implication = self.viper.Implies(has_type, current, instance_pos, no_info)
            self_var_type_expr = self.type_factory.typeof(self_var_ref, ctx)
            instance_type = self.type_factory.translate_type_literal(instance.cls, instance_pos, ctx,
                                                                     alias=self_var_type_expr)
            type_not_instance = self.viper.NeCmp(self_var_type_expr, instance_type, instance_pos, no_info)
            unknown_type_condition = self.viper.And(unknown_type_condition, type_not_instance, instance_pos, no_info)
            ctx.current_function = None
            if body:
                body = self.viper.And(body, implication,
                    self.to_position(root.node, ctx), no_info)
            else:
                body = implication
            self_frame_method_name = root.module.get_fresh_name(root.name + '_' + instance.name + 'frame_check')
            pos_with_rule = self.to_position(instance.node, ctx, rules=rules.PRED_FAM_MEMBER_NOT_FRAMED)
            current_with_rule = self.viper.And(true_lit, current, pos_with_rule, no_info)
            self_frame_method = self.viper.Method(self_frame_method_name, args, [],
                                                  [arg_types, has_type, current_with_rule],
                                                  [], [], None, self.to_position(root.node, ctx), no_info)
            self_framing_check_methods.append(self_frame_method)
            # Dirty hack to artificially create a dependency from this predicate to its well-formedness check;
            # the call is never used, but the creation of the call while translating the predicate will be tracked.
            self.viper.MethodCall(self_frame_method_name, [], [], self.to_position(root.node, ctx), no_info)
        root_pos = self.to_position(root.node, ctx)
        all_preds = []
        if not root.contract_only and not (root.name == 'invariant' and root.cls.name == 'Lock'):
            root_pos_with_rule = self.to_position(root.node, ctx, rules=rules.PRED_FAM_FOLD_UNKNOWN_RECEIVER)
            rest_pred_name = root.module.get_fresh_name(root.name + '_abstract_rest')
            rest_pred = self.viper.Predicate(rest_pred_name, args, None, root_pos, no_info)
            all_preds.append(rest_pred)
            rest_pred_acc = self.viper.PredicateAccess([arg.localVar() for arg in args],
                                                       rest_pred_name, root_pos_with_rule, no_info)
            rest_pred_acc_pred = self.viper.PredicateAccessPredicate(rest_pred_acc,
                                                                     self.viper.FullPerm(root_pos_with_rule, no_info),
                                                                     root_pos_with_rule, no_info)
            body = self.viper.And(body, self.viper.Implies(unknown_type_condition, rest_pred_acc_pred,
                                                           root_pos_with_rule, no_info),
                                  root_pos_with_rule, no_info)
        ctx.var_aliases = {}
        if not root.contract_only:
            body = self.viper.And(arg_types, body, root_pos, no_info)
        family_pred = self.viper.Predicate(name, args, body, root_pos, no_info)
        all_preds.append(family_pred)
        return all_preds, self_framing_check_methods
