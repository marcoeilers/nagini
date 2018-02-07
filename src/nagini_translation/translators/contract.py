"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import ast
import copy

from nagini_contracts.contracts import CONTRACT_WRAPPER_FUNCS
from nagini_translation.lib.constants import (
    BOOL_TYPE,
    BUILTIN_PREDICATES,
    GET_ARG_FUNC,
    GET_METHOD_FUNC,
    GET_OLD_FUNC,
    GLOBAL_VAR_FIELD,
    INT_TYPE,
    JOINABLE_FUNC,
    METHOD_ID_DOMAIN,
    PRIMITIVES,
    RANGE_TYPE,
    SEQ_TYPE,
    THREAD_DOMAIN,
    THREAD_POST_PRED,
    THREAD_START_PRED,
)
from nagini_translation.lib.program_nodes import (
    PythonField,
    PythonGlobalVar,
    PythonMethod,
    PythonModule,
    PythonType,
    PythonVar,
    UnionType,
    toposort_classes,
    chain_cond_exp,
)
from nagini_translation.lib.typedefs import (
    Expr,
    Position,
    StmtsAndExpr,
)
from nagini_translation.lib.util import (
    construct_lambda_prefix,
    find_loop_for_previous,
    get_func_name,
    InvalidProgramException,
    OldExpressionNormalizer,
    pprint,
    UnsupportedException,
)
from nagini_translation.translators.abstract import Context
from nagini_translation.translators.common import CommonTranslator
from typing import List


class ContractTranslator(CommonTranslator):

    def translate_contract(self, node: ast.AST, ctx: Context) -> Expr:
        """
        Generic visitor function for translating contracts (i.e. calls to
        contract functions)
        """
        method = 'translate_contract_' + node.__class__.__name__
        visitor = getattr(self, method, self.translate_generic)
        return visitor(node, ctx)

    def translate_contract_Call(self, node: ast.Call, ctx: Context) -> Expr:
        if get_func_name(node) in CONTRACT_WRAPPER_FUNCS:
            stmt, res = self.translate_expr(node.args[0], ctx, self.viper.Bool, True)
            if stmt:
                raise InvalidProgramException(node, 'purity.violated')
            return res
        else:
            raise UnsupportedException(node)

    def translate_contract_Expr(self, node: ast.Expr, ctx: Context) -> Expr:
        if isinstance(node.value, ast.Call):
            return self.translate_contract(node.value, ctx)
        else:
            raise UnsupportedException(node)

    def translate_result(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to the Result() contract function to a result
        expression.
        """
        assert len(node.args) == 0
        type = ctx.actual_function.type
        if not ctx.actual_function.pure:
            if ctx.result_var is None:
                raise InvalidProgramException('invalid.result')
            return [], ctx.result_var.ref(node, ctx)
        else:
            return ([], self.viper.Result(self.translate_type(type, ctx),
                                          self.to_position(node, ctx),
                                          self.no_info(ctx)))

    def translate_raised_exception(
            self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to the RaisedException() contract function to a
        expression.
        """
        assert len(node.args) == 0
        assert not ctx.actual_function.pure
        return [], ctx.error_var.ref(node, ctx)

    def _get_perm(self, node: ast.Call, ctx: Context) -> Expr:
        """
        Returns the permission for a Acc() contract function.
        """
        # Only one argument means implicit full permission
        if ctx.current_function.pure:
            return self.viper.WildcardPerm(self.to_position(node, ctx), self.no_info(ctx))
        if len(node.args) == 1:
            perm = self.viper.FullPerm(self.to_position(node, ctx),
                                       self.no_info(ctx))
        elif len(node.args) == 2:
            perm = self.translate_perm(node.args[1], ctx)
        else:
            # More than two arguments are invalid
            raise InvalidProgramException(node, 'invalid.contract.call')

        return perm

    def translate_builtin_predicate(self, node: ast.Call, perm: Expr,
                                    args: List[Expr], ctx: Context) -> Expr:
        name = node.func.id
        seq_ref = self.viper.SeqType(self.viper.Ref)
        set_ref = self.viper.SetType(self.viper.Ref)
        if name == 'list_pred':
            # field list_acc : Seq[Ref]
            field = self.viper.Field('list_acc', seq_ref, self.no_position(ctx),
                                     self.no_info(ctx))
        elif name == 'set_pred':
            # field set_acc : Set[Ref]
            field = self.viper.Field('set_acc', set_ref, self.no_position(ctx),
                                     self.no_info(ctx))
        elif name == 'dict_pred':
            # field dict_acc : Set[Ref]
            field = self.viper.Field('dict_acc', set_ref, self.no_position(ctx),
                                     self.no_info(ctx))
        elif name == 'MayStart':
            return self.translate_may_start(node, args, perm, ctx)
        elif name == 'ThreadPost':
            return self.translate_thread_post(node, args, perm, ctx)
        else:
            raise UnsupportedException(node)
        field_acc = self.viper.FieldAccess(args[0], field,
                                           self.to_position(node, ctx),
                                           self.no_info(ctx))
        pos = self.to_position(node, ctx)
        info = self.no_info(ctx)
        if ctx.perm_factor:
            perm = self.viper.PermMul(perm, ctx.perm_factor, pos, info)
        pred = self.viper.FieldAccessPredicate(field_acc, perm, pos, info)
        return pred

    def translate_may_start(self, node: ast.Call, args: List[Expr], perm: Expr,
                            ctx: Context) -> Expr:
        pos = self.to_position(node, ctx)
        info = self.no_info(ctx)
        pred_access = self.viper.PredicateAccess(args, THREAD_START_PRED, pos, info)
        access_pred = self.viper.PredicateAccessPredicate(pred_access, perm, pos, info)
        return access_pred

    def translate_thread_post(self, node: ast.Call, args: List[Expr], perm: Expr,
                            ctx: Context) -> Expr:
        pos = self.to_position(node, ctx)
        info = self.no_info(ctx)
        pred_access = self.viper.PredicateAccess(args, THREAD_POST_PRED, pos, info)
        access_pred = self.viper.PredicateAccessPredicate(pred_access, perm, pos, info)
        func = self.viper.FuncApp(JOINABLE_FUNC, args, pos, info, self.viper.Bool)
        conjunction = self.viper.And(access_pred, func, pos, info)
        return conjunction

    def translate_unwrapped_builtin_predicate(self, node: ast.Call, ctx: Context) -> Expr:
        args = []
        stmt, arg = self.translate_expr(node.args[0], ctx)
        if stmt:
            raise InvalidProgramException(node, 'purity.violated')
        perm = self.viper.FullPerm(self.no_position(ctx), self.no_info(ctx))
        return self.translate_builtin_predicate(node, perm, [arg], ctx)

    def translate_acc_predicate(self, node: ast.Call, perm: Expr,
                                ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to the Acc() contract function with a predicate call
        inside to a predicate access.
        """
        assert isinstance(node.args[0], ast.Call)
        call = node.args[0]
        # The predicate inside is a function call in python.
        args = []
        arg_stmts = []
        for arg in call.args:
            arg_stmt, arg_expr = self.translate_expr(arg, ctx)
            arg_stmts = arg_stmts + arg_stmt
            args.append(arg_expr)
        # Get the predicate inside the Acc()
        if isinstance(call.func, ast.Name):
            if call.func.id in BUILTIN_PREDICATES:
                return arg_stmts, self.translate_builtin_predicate(call, perm,
                                                                   args, ctx)
            else:
                pred = self.get_target(call.func, ctx)
        elif isinstance(call.func, ast.Attribute):
            receiver = self.get_target(call.func.value, ctx)
            if isinstance(receiver, PythonModule):
                pred = receiver.predicates[call.func.attr]
            else:
                rec_stmt, receiver = self.translate_expr(call.func.value, ctx)
                assert not rec_stmt
                receiver_class = self.get_type(call.func.value, ctx)
                name = call.func.attr
                pred = receiver_class.get_predicate(name)
                args = [receiver] + args
        else:
            raise UnsupportedException(node)
        if not (isinstance(pred, PythonMethod) and pred.predicate):
            raise InvalidProgramException(node, 'invalid.acc')
        pred_name = pred.sil_name
        # If the predicate is part of a family, find the correct version.
        if pred.cls:
            family_root = pred.cls
            while (family_root.superclass and
                   family_root.superclass.get_predicate(name)):
                family_root = family_root.superclass
            pred_name = family_root.get_predicate(name).sil_name
        return arg_stmts, self.create_predicate_access(pred_name, args, perm,
                                                       node, ctx)

    def translate_acc_field(self, node: ast.Call, perm: Expr,
                            ctx: Context) -> StmtsAndExpr:
        assert isinstance(node.args[0], ast.Attribute)
        field = self.get_target(node.args[0], ctx)
        if not isinstance(field, PythonField):
            raise InvalidProgramException(node, 'invalid.acc')
        stmt, field_acc = self.translate_expr(node.args[0], ctx)
        if stmt:
            raise InvalidProgramException(node, 'purity.violated')
        field_type = self.get_type(node.args[0], ctx)
        pred = self._translate_acc_field(field_acc, field_type, perm,
                                         self.to_position(node, ctx), ctx)
        return [], pred

    def translate_acc_global(self, node: ast.Call, perm: Expr,
                            ctx: Context) -> StmtsAndExpr:
        """
        Translates an access permission to a global variable.
        """
        var = self.get_target(node.args[0], ctx)
        if not isinstance(var, PythonGlobalVar):
            raise InvalidProgramException(node, 'invalid.acc')
        if var.is_final:
            raise InvalidProgramException(node, 'permission.to.final.var')
        pos = self.to_position(node, ctx)
        info = self.no_info(ctx)
        var_func = self.viper.FuncApp(var.sil_name, [], pos, info, self.viper.Ref, [])
        var_type = self.translate_type(var.type, ctx)
        field = self.viper.Field(GLOBAL_VAR_FIELD, var_type, pos, info)
        field_acc = self.viper.FieldAccess(var_func, field, pos, info)
        pred = self.viper.FieldAccessPredicate(field_acc, perm, pos, info)

        # Add type information
        if var.type.name not in PRIMITIVES:
            type_info = self.type_check(field_acc, var.type,
                                        self.no_position(ctx), ctx)
            pred = self.viper.And(pred, type_info, pos, info)
        return [], pred

    def _translate_acc_field(self, field_acc: Expr, field_type: PythonType,
                             perm: Expr, pos: Position, ctx: Context) -> StmtsAndExpr:
        info = self.no_info(ctx)
        if ctx.perm_factor:
            perm = self.viper.PermMul(perm, ctx.perm_factor, pos, info)
        pred = self.viper.FieldAccessPredicate(field_acc, perm,
                                               pos, info)
        # Add type information
        if field_type.name not in PRIMITIVES:
            type_info = self.type_check(field_acc, field_type,
                                        self.no_position(ctx), ctx)
            pred = self.viper.And(pred, type_info, pos, info)
        return pred

    def translate_may_set(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to MaySet().
        """
        pos = self.to_position(node, ctx)
        info = self.no_info(ctx)
        stmt, rec = self.translate_expr(node.args[0], ctx)
        rec_type = self.get_type(node.args[0], ctx)
        if stmt:
            raise InvalidProgramException(node.args[0], 'purity.violated')
        if not isinstance(node.args[1], ast.Str):
            raise InvalidProgramException(node.args[1], 'invalid.may.set')
        field = rec_type.get_field(node.args[1].s)
        if not field:
            raise InvalidProgramException(node.args[1], 'invalid.may.set')
        may_set_pred = self.get_may_set_predicate(rec, field, ctx, pos)
        sil_field = self.viper.Field(field.sil_name, self.translate_type(field.type, ctx),
                                     pos, info)
        field_acc = self.viper.FieldAccess(rec, sil_field, pos, info)
        full_perm = self.viper.FullPerm(pos, info)
        normal_acc = self._translate_acc_field(field_acc, field.type, full_perm, pos, ctx)
        normal_perm = self.viper.CurrentPerm(field_acc, pos, info)
        have_normal_perm = self.viper.PermGtCmp(normal_perm, self.viper.NoPerm(pos, info),
                                                pos, info)
        result_ex = self.viper.CondExp(have_normal_perm, normal_acc, may_set_pred, pos,
                                       info)
        unknown = self.get_unknown_bool(ctx)
        result_in = self.viper.CondExp(unknown, normal_acc, may_set_pred, pos, info)
        return [], self.viper.InhaleExhaleExp(result_in, result_ex, pos, info)

    def translate_may_create(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to MayCreate().
        """
        pos = self.to_position(node, ctx)
        stmt, rec = self.translate_expr(node.args[0], ctx)
        rec_type = self.get_type(node.args[0], ctx)
        if stmt:
            raise InvalidProgramException(node.args[0], 'purity.violated')
        if not isinstance(node.args[1], ast.Str):
            raise InvalidProgramException(node.args[1], 'invalid.may.create')
        field = rec_type.get_field(node.args[1].s)
        if not field:
            raise InvalidProgramException(node.args[1], 'invalid.may.create')
        return [], self.get_may_set_predicate(rec, field, ctx, pos)

    def translate_assert(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to Assert().
        """
        assert len(node.args) == 1
        stmt, expr = self.translate_expr(node.args[0], ctx, self.viper.Bool, True)
        assertion = self.viper.Assert(expr, self.to_position(node, ctx),
                                      self.no_info(ctx))
        return stmt + [assertion], None

    def translate_assume(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to Assume().
        """
        assert len(node.args) == 1
        stmt, expr = self.translate_expr(node.args[0], ctx, self.viper.Bool, True)
        assertion = self.viper.Inhale(expr, self.to_position(node, ctx),
                                      self.no_info(ctx))
        return stmt + [assertion], None

    def translate_implies(self, node: ast.Call, ctx: Context,
                          impure=False) -> StmtsAndExpr:
        """
        Translates a call to the Implies() contract function.
        """
        if len(node.args) != 2:
            raise InvalidProgramException(node, 'invalid.contract.call')
        cond_stmt, cond = self.translate_expr(node.args[0], ctx,
                                              target_type=self.viper.Bool)
        then_stmt, then = self.translate_expr(node.args[1], ctx,
                                              target_type=self.viper.Bool, impure=impure)
        implication = self.viper.Implies(cond, then,
                                         self.to_position(node, ctx),
                                         self.no_info(ctx))
        return (cond_stmt + then_stmt, implication)

    def translate_old(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to the Old() contract function.
        """
        if len(node.args) != 1:
            raise InvalidProgramException(node, 'invalid.contract.call')

        if ctx.old_expr_aliases:
            normalizer = OldExpressionNormalizer()
            normalizer.arg_names = [a for a in ctx.actual_function._args]

            normalized = normalizer.visit(copy.deepcopy(node.args[0]))
            key = pprint(normalized)
            if key in ctx.old_expr_aliases:
                return [], ctx.old_expr_aliases[key]

        stmt, exp = self.translate_expr(node.args[0], ctx)
        res = self.viper.Old(exp, self.to_position(node, ctx),
                             self.no_info(ctx))
        return stmt, res

    def translate_fold(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to the Fold() contract function.
        """
        if len(node.args) != 1:
            raise InvalidProgramException(node, 'invalid.contract.call')
        pred_stmt, pred = self.translate_expr(node.args[0], ctx,
                                              self.viper.Bool, True)
        if self._is_family_fold(node):
            # Predicate called on receiver, so it belongs to a family
            if ctx.ignore_family_folds:
                return [], None
        if pred_stmt:
            raise InvalidProgramException(node, 'purity.violated')
        fold = self.viper.Fold(pred, self.to_position(node, ctx),
                               self.no_info(ctx))
        return [fold], None

    def _is_family_fold(self, fold: ast.AST) -> bool:
        if isinstance(fold.args[0], ast.Call) and \
                isinstance(fold.args[0].func, ast.Attribute):
            return True
        if (isinstance(fold.args[0], ast.Call) and
                isinstance(fold.args[0].func, ast.Name) and
                fold.args[0].func.id == 'Acc' and
                isinstance(fold.args[0].args[0], ast.Attribute)):
            return True
        return False

    def translate_previous(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        arg = node.args[0]
        if not isinstance(arg, ast.Name):
            raise InvalidProgramException(node, 'invalid.previous')
        loop = find_loop_for_previous(node, arg.id)
        if not loop:
            raise InvalidProgramException(node, 'invalid.previous')
        iterator = ctx.loop_iterators[loop].ref()
        list_field = self.viper.Field('__previous', self.viper.Ref,
                                      self.no_position(ctx), self.no_info(ctx))
        field_acc = self.viper.FieldAccess(iterator, list_field,
                                           self.to_position(node, ctx),
                                           self.no_info(ctx))
        return [], field_acc

    def translate_unfold(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to the Unfold() contract function.
        """
        if len(node.args) != 1:
            raise InvalidProgramException(node, 'invalid.contract.call')
        pred_stmt, pred = self.translate_expr(node.args[0], ctx,
                                              self.viper.Bool, True)
        if self._is_family_fold(node):
            # Predicate called on receiver, so it belongs to a family
            if ctx.ignore_family_folds:
                return [], None
        if pred_stmt:
            raise InvalidProgramException(node, 'purity.violated')
        unfold = self.viper.Unfold(pred, self.to_position(node, ctx),
                                   self.no_info(ctx))
        return [unfold], None

    def translate_unfolding(self, node: ast.Call, ctx: Context,
                            impure=False) -> StmtsAndExpr:
        """
        Translates a call to the Unfolding() contract function.
        """
        if len(node.args) != 2:
            raise InvalidProgramException(node, 'invalid.contract.call')
        pred_stmt, pred = self.translate_expr(node.args[0], ctx,
                                              self.viper.Bool, True)
        if pred_stmt:
            raise InvalidProgramException(node, 'purity.violated')
        expr_stmt, expr = self.translate_expr(node.args[1], ctx, impure)
        expr = self.unwrap(expr)
        unfold = self.viper.Unfolding(pred, expr, self.to_position(node, ctx),
                                      self.no_info(ctx))
        return expr_stmt, unfold

    def translate_low(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to the Low() contract function.
        """
        return [], self.viper.TrueLit(self.to_position(node, ctx),
                                      self.no_info(ctx))

    def _translate_triggers(self, body: ast.AST, node: ast.Call,
                            ctx: Context) -> List['silver.ast.Trigger']:
        """
        Assuming the given body is a tuple whose second element is a list
        literal containing any number of list literals containing expressions,
        translates those to a list of triggers.
        """
        if (not isinstance(body, ast.Tuple) or
                    len(body.elts) != 2):
            raise InvalidProgramException(node, 'invalid.trigger')
        trigger_node = body.elts[1]
        triggers = []
        if not isinstance(trigger_node, ast.List):
            raise InvalidProgramException(node, 'invalid.trigger')
        outer = trigger_node

        if outer.elts:
            for el in outer.elts:
                trigger = []
                if not isinstance(el, ast.List):
                    raise InvalidProgramException(el, 'invalid.trigger')
                for inner in el.elts:
                    part_stmt, part = self.translate_expr(inner, ctx)
                    if part_stmt:
                        raise InvalidProgramException(inner,
                                                      'purity.violated')
                    part = self.unwrap(part)
                    trigger.append(part)
                trigger = self.viper.Trigger(trigger, self.no_position(ctx),
                                             self.no_info(ctx))
                triggers.append(trigger)
        return triggers

    def _create_quantifier_contains_expr(self, var: PythonVar,
                                         domain_node: ast.AST,
                                         ctx: Context) -> StmtsAndExpr:
        """
        Creates the left hand side of the implication in a quantifier
        expression, which says that var is an element of the given domain.
        """
        domain_old = False
        if (isinstance(domain_node, ast.Call) and
                    get_func_name(domain_node) == 'Old'):
            domain_old = True
            domain_node = domain_node.args[0]

        ref_var = self.to_ref(var.ref(), ctx)
        pos = self.to_position(domain_node, ctx)
        info = self.no_info(ctx)

        if isinstance(domain_node, ast.Call) and get_func_name(domain_node) == 'range':
            if not len(domain_node.args) == 2:
                msg = 'range() is currently only supported with two args.'
                raise UnsupportedException(domain_node, msg)
            arg1_stmt, arg1 = self.translate_expr(domain_node.args[0], ctx,
                                                  target_type=self.viper.Int)
            arg2_stmt, arg2 = self.translate_expr(domain_node.args[1], ctx,
                                                  target_type=self.viper.Int)
            int_var = self.to_int(ref_var, ctx)
            condition = self.viper.And(self.viper.GeCmp(int_var, arg1, pos, info),
                                       self.viper.LtCmp(int_var, arg2, pos, info),
                                       pos, info)
            return arg1_stmt + arg2_stmt, condition, False
        dom_stmt, domain = self.translate_expr(domain_node, ctx)
        dom_type = self.get_type(domain_node, ctx)
        seq_ref = self.viper.SeqType(self.viper.Ref)
        formal_args = [self.viper.LocalVarDecl('self', self.viper.Ref, pos, info)]
        domain_set = self.viper.FuncApp(dom_type.name + '___sil_seq__',
                                        [domain], pos, info, seq_ref, formal_args)

        result = self.viper.SeqContains(ref_var, domain_set, pos, info)
        if domain_old:
            result = self.viper.Old(result, pos, info)
        return dom_stmt, result, True

    def translate_to_sequence(self, node: ast.Call,
                              ctx: Context) -> StmtsAndExpr:
        coll_type = self.get_type(node.args[0], ctx)
        stmt, arg = self.translate_expr(node.args[0], ctx)
        # Use the same sequence conversion as for iterating over the
        # iterable (which gives no information about order for unordered types).
        seq_call = self.get_function_call(coll_type, '__sil_seq__', [arg],
                                          [None], node, ctx)
        seq_class = ctx.module.global_module.classes[SEQ_TYPE]
        if coll_type.name == RANGE_TYPE:
            type_arg = ctx.module.global_module.classes[INT_TYPE]
        else:
            type_arg = coll_type.type_args[0]
        position = self.to_position(node, ctx)
        type_lit = self.type_factory.translate_type_literal(type_arg, position,
                                                            ctx)
        result = self.get_function_call(seq_class, '__create__',
                                        [seq_call, type_lit], [None, None],
                                        node, ctx)
        return stmt, result

    def translate_sequence(self, node: ast.Call,
                           ctx: Context) -> StmtsAndExpr:
        seq_type = self.get_type(node, ctx)
        viper_type = self.translate_type(seq_type.type_args[0], ctx)
        val_stmts = []
        if node.args:
            vals = []
            for arg in node.args:
                arg_stmt, arg_val = self.translate_expr(arg, ctx,
                    target_type=viper_type)
                val_stmts += arg_stmt
                vals.append(arg_val)
            result = self.viper.ExplicitSeq(vals, self.to_position(node,
                                                                   ctx),
                                            self.no_info(ctx))
        else:
            result = self.viper.EmptySeq(viper_type,
                                         self.to_position(node, ctx),
                                         self.no_info(ctx))
        type_arg = seq_type.type_args[0]
        position = self.to_position(node, ctx)
        type_lit = self.type_factory.translate_type_literal(type_arg, position,
                                                            ctx)
        result = self.get_function_call(seq_type.cls, '__create__',
                                        [result, type_lit], [None, None], node,
                                        ctx)
        return val_stmts, result

    def translate_pset(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        set_type = self.get_type(node, ctx)
        viper_type = self.translate_type(set_type.type_args[0], ctx)
        val_stmts = []
        if node.args:
            vals = []
            for arg in node.args:
                arg_stmt, arg_val = self.translate_expr(arg, ctx,
                    target_type=viper_type)
                val_stmts += arg_stmt
                vals.append(arg_val)
            result = self.viper.ExplicitSet(vals, self.to_position(node, ctx),
                                            self.no_info(ctx))
        else:
            result = self.viper.EmptySet(viper_type,
                                         self.to_position(node, ctx),
                                         self.no_info(ctx))
        type_arg = set_type.type_args[0]
        position = self.to_position(node, ctx)
        type_lit = self.type_factory.translate_type_literal(type_arg, position,
                                                            ctx)
        result = self.get_function_call(set_type.cls, '__create__',
                                        [result, type_lit], [None, None], node,
                                        ctx)
        return val_stmts, result

    def translate_get_arg(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        thread_stmt, thread = self.translate_expr(node.args[0], ctx)
        index_stmt, index = self.translate_expr(node.args[1], ctx,
                                                target_type=self.viper.Int)
        pos = self.to_position(node, ctx)
        info = self.no_info(ctx)
        method_id_type = self.viper.DomainType(METHOD_ID_DOMAIN, {}, [])
        func = self.viper.DomainFuncApp(GET_ARG_FUNC, [thread, index], self.viper.Ref,
                                        pos, info, THREAD_DOMAIN)
        return thread_stmt + index_stmt, func

    def translate_get_old(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        stmt, thread = self.translate_expr(node.args[0], ctx)
        pos = self.to_position(node, ctx)
        info = self.no_info(ctx)
        old_string = pprint(node.args[1])
        index = self._get_string_value(old_string)
        index = self.viper.IntLit(index, pos, info)
        func = self.viper.DomainFuncApp(GET_OLD_FUNC, [thread, index], self.viper.Ref,
                                        pos, info, THREAD_DOMAIN)
        return stmt, func

    def translate_may_join(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        stmt, thread = self.translate_expr(node.args[0], ctx)
        pos = self.to_position(node, ctx)
        info = self.no_info(ctx)
        func = self.viper.FuncApp(JOINABLE_FUNC, [thread], pos, info, self.viper.Bool)
        return stmt, func

    def translate_forall(self, node: ast.Call, ctx: Context,
                         impure=False) -> StmtsAndExpr:
        domain_node = node.args[0]

        lambda_ = node.args[1]
        variables = []
        lambda_prefix = construct_lambda_prefix(lambda_.lineno,
                                                getattr(lambda_, 'col_offset',
                                                        None))
        lambda_prefix += '$'
        arg = lambda_.args.args[0]
        var = ctx.actual_function.get_variable(lambda_prefix + arg.arg)
        variables.append(var.decl)

        ctx.set_alias(arg.arg, var, None)
        if isinstance(lambda_.body, ast.Tuple):
            if not len(lambda_.body.elts) == 2:
                raise InvalidProgramException(node, 'invalid.forall')
            body_stmt, rhs = self.translate_expr(lambda_.body.elts[0], ctx,
                                                 self.viper.Bool, impure)

            triggers = self._translate_triggers(lambda_.body, node, ctx)
        else:
            body_type = self.get_type(lambda_.body, ctx)
            if not body_type or body_type.name != BOOL_TYPE:
                raise InvalidProgramException(node, 'invalid.forall')
            body_stmt, rhs = self.translate_expr(lambda_.body, ctx,
                                                 self.viper.Bool, impure)
            triggers = []

        ctx.remove_alias(arg.arg)
        if body_stmt:
            raise InvalidProgramException(node, 'purity.violated')

        dom_stmt, lhs, is_trigger = self._create_quantifier_contains_expr(var,
                                                                          domain_node,
                                                                          ctx)
        lhs = self.unwrap(lhs)

        implication = self.viper.Implies(lhs, rhs, self.to_position(node, ctx),
                                         self.no_info(ctx))
        if is_trigger and triggers:
            # Add lhs of the implication, which the user cannot write directly
            # in this exact form.
            # If we always do this, we apparently deactivate the automatically
            # generated triggers and things are actually worse.
            try:
                # Depending on the collection expression, this doesn't always
                # work (malformed trigger); in that case, we just don't do it.
                lhs_trigger = self.viper.Trigger([lhs], self.no_position(ctx),
                                                 self.no_info(ctx))
                triggers = [lhs_trigger] + triggers
            except Exception:
                pass
        var_type_check = self.type_check(var.ref(), var.type,
                                         self.no_position(ctx), ctx, False)
        implication = self.viper.Implies(var_type_check, implication,
                                         self.to_position(node, ctx),
                                         self.no_info(ctx))
        forall = self.viper.Forall(variables, triggers, implication,
                                   self.to_position(node, ctx),
                                   self.no_info(ctx))
        return dom_stmt, forall

    def translate_contractfunc_call(self, node: ast.Call, ctx: Context,
                                    impure=False) -> StmtsAndExpr:
        """
        Translates calls to contract functions like Result() and Acc()
        """
        func_name = get_func_name(node)
        if func_name in ('Result', 'TypedResult'):
            return self.translate_result(node, ctx)
        elif func_name == 'RaisedException':
            return self.translate_raised_exception(node, ctx)
        elif func_name in ('Acc', 'Rd'):
            if not impure:
                raise InvalidProgramException(node, 'invalid.contract.position')
            if func_name == 'Rd':
                perm = self.viper.WildcardPerm(self.to_position(node, ctx),
                                               self.no_info(ctx))
            else:
                perm = self._get_perm(node, ctx)
            if isinstance(node.args[0], ast.Call):
                return self.translate_acc_predicate(node, perm, ctx)
            else:
                if isinstance(node.args[0], ast.Attribute):
                    type = self.get_type(node.args[0].value, ctx)
                    if isinstance(type, UnionType):
                        guarded_field_access = []
                        stmt, receiver = self.translate_expr(node.args[0].value, ctx)
                        for recv_type in toposort_classes(type.get_types() - {None}):
                            target = self.get_target(node.args[0].value, ctx)
                            field_guard = self.var_type_check(target.sil_name,
                                                              recv_type,
                                                              self.to_position(node, ctx),
                                                              ctx)
                            field = recv_type.get_field(node.args[0].attr).actual_field
                            field_access = self.viper.FieldAccess(receiver, field.sil_field,
                                                                  self.to_position(node, ctx),
                                                                  self.no_info(ctx))
                            field_acc = self._translate_acc_field(field_access,
                                                                  field.type, perm,
                                                                  self.to_position(node, ctx),
                                                                  ctx)
                            guarded_field_access.append((field_guard, field_acc))
                        if len(guarded_field_access) == 1:
                            _, field_acc = guarded_field_access[0]
                            return stmt, field_acc
                        else:
                            return (stmt, chain_cond_exp(guarded_field_access, self.viper,
                                                         self.to_position(node, ctx),
                                                         self.no_info(ctx), ctx))
                target = self.get_target(node.args[0], ctx)
                if isinstance(target, PythonField):
                    return self.translate_acc_field(node, perm, ctx)
                else:
                    if not isinstance(target, PythonGlobalVar):
                        raise InvalidProgramException(node, 'invalid.acc')
                    return self.translate_acc_global(node, perm, ctx)
        elif func_name in BUILTIN_PREDICATES:
            return self.translate_unwrapped_builtin_predicate(node, ctx)
        elif func_name == 'MaySet':
            return self.translate_may_set(node, ctx)
        elif func_name == 'MayCreate':
            return self.translate_may_create(node, ctx)
        elif func_name == 'Assert':
            return self.translate_assert(node, ctx)
        elif func_name == 'Assume':
            return self.translate_assume(node, ctx)
        elif func_name == 'Implies':
            return self.translate_implies(node, ctx, impure)
        elif func_name == 'Old':
            return self.translate_old(node, ctx)
        elif func_name == 'Fold':
            return self.translate_fold(node, ctx)
        elif func_name == 'Unfold':
            return self.translate_unfold(node, ctx)
        elif func_name == 'Unfolding':
            return self.translate_unfolding(node, ctx, impure)
        elif func_name == 'Low':
            return self.translate_low(node, ctx)
        elif func_name == 'Forall':
            return self.translate_forall(node, ctx, impure)
        elif func_name == 'Previous':
            return self.translate_previous(node, ctx)
        elif func_name == 'Sequence':
            return self.translate_sequence(node, ctx)
        elif func_name == 'PSet':
            return self.translate_pset(node, ctx)
        elif func_name == 'ToSeq':
            return self.translate_to_sequence(node, ctx)
        elif func_name == 'MayJoin':
            return self.translate_may_join(node, ctx)
        elif func_name == 'getArg':
            return self.translate_get_arg(node, ctx)
        elif func_name == 'getOld':
            return self.translate_get_old(node, ctx)
        elif func_name == 'getMethod':
            raise InvalidProgramException(node, 'invalid.get.method.use')
        elif func_name == 'arg':
            raise InvalidProgramException(node, 'invalid.arg.use')
        else:
            raise UnsupportedException(node)
