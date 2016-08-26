import ast

from py2viper_contracts.contracts import CONTRACT_WRAPPER_FUNCS
from py2viper_translation.lib.constants import BUILTIN_PREDICATES, PRIMITIVES
from py2viper_translation.lib.program_nodes import PythonVar
from py2viper_translation.lib.typedefs import (
    Expr,
    Stmt,
    StmtsAndExpr,
)
from py2viper_translation.lib.util import (
    construct_lambda_prefix,
    find_loop_for_previous,
    get_func_name,
    InvalidProgramException,
    UnsupportedException,
)
from py2viper_translation.translators.abstract import Context
from py2viper_translation.translators.common import CommonTranslator
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
            stmt, res = self.translate_expr(node.args[0], ctx)
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
        # only one argument means implicit full permission
        if len(node.args) == 1:
            perm = self.viper.FullPerm(self.to_position(node, ctx),
                                       self.no_info(ctx))
        elif len(node.args) == 2:
            perm = self.translate_perm(node.args[1], ctx)
        else:
            # more than two arguments are invalid
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
        else:
            raise UnsupportedException(node)
        field_acc = self.viper.FieldAccess(args[0], field,
                                           self.to_position(node, ctx),
                                           self.no_info(ctx))
        pred = self.viper.FieldAccessPredicate(field_acc, perm,
                                               self.to_position(node, ctx),
                                               self.no_info(ctx))
        return pred

    def translate_acc_predicate(self, node: ast.Call, perm: Expr,
                                ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to the Acc() contract function with a predicate call
        inside to a predicate access.
        """
        assert isinstance(node.args[0], ast.Call)
        call = node.args[0]
        # the predicate inside is a function call in python.
        args = []
        arg_stmts = []
        for arg in call.args:
            arg_stmt, arg_expr = self.translate_expr(arg, ctx)
            arg_stmts = arg_stmts + arg_stmt
            args.append(arg_expr)
        # get the predicate inside the Acc()
        if isinstance(call.func, ast.Name):
            if call.func.id in BUILTIN_PREDICATES:
                return arg_stmts, self.translate_builtin_predicate(call, perm,
                                                                   args, ctx)
            else:
                pred = ctx.program.predicates[call.func.id]
        elif isinstance(call.func, ast.Attribute):
            rec_stmt, receiver = self.translate_expr(call.func.value, ctx)
            assert not rec_stmt
            receiver_class = self.get_type(call.func.value, ctx)
            name = call.func.attr
            pred = receiver_class.get_predicate(name)
            args = [receiver] + args
        else:
            raise UnsupportedException(node)
        pred_name = pred.sil_name
        # if the predicate is part of a family, find the correct version.
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
        stmt, fieldacc = self.translate_expr(node.args[0], ctx)
        if stmt:
            raise InvalidProgramException(node, 'purity.violated')
        pred = self.viper.FieldAccessPredicate(fieldacc, perm,
                                               self.to_position(node, ctx),
                                               self.no_info(ctx))
        return [], pred

    def translate_assert(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to Assert().
        """
        assert len(node.args) == 1
        stmt, expr = self.translate_expr(node.args[0], ctx)
        assertion = self.viper.Assert(expr, self.to_position(node, ctx),
                                      self.no_info(ctx))
        return stmt + [assertion], None

    def translate_implies(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to the Implies() contract function.
        """
        if len(node.args) != 2:
            raise InvalidProgramException(node, 'invalid.contract.call')
        cond_stmt, cond = self.translate_expr(node.args[0], ctx)
        then_stmt, then = self.translate_expr(node.args[1], ctx)
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
        pred_stmt, pred = self.translate_expr(node.args[0], ctx)
        if self._is_family_fold(node):
            # predicate called on receiver, so it belongs to a family
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

    def translate_seq_constructor(self, node: ast.Call,
                                  ctx: Context) -> StmtsAndExpr:
        seq_type = self.get_type(node, ctx)
        viper_type = self.translate_type(seq_type.type_args[0], ctx)
        if node.args:
            vals = []
            val_stmts = []
            for arg in node.args:
                arg_stmt, arg_val = self.translate_expr(arg, ctx)
                val_stmts += arg_stmt
                vals.append(arg_val)
            result = self.viper.ExplicitSeq(vals, self.to_position(node, ctx),
                                            self.no_info(ctx))
            return val_stmts, result
        else:
            result = self.viper.EmptySeq(viper_type,
                                         self.to_position(node, ctx),
                                         self.no_info(ctx))
            return [], result

    def translate_unfold(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to the Unfold() contract function.
        """
        if len(node.args) != 1:
            raise InvalidProgramException(node, 'invalid.contract.call')
        pred_stmt, pred = self.translate_expr(node.args[0], ctx)
        if self._is_family_fold(node):
            # predicate called on receiver, so it belongs to a family
            if ctx.ignore_family_folds:
                return [], None
        if pred_stmt:
            raise InvalidProgramException(node, 'purity.violated')
        unfold = self.viper.Unfold(pred, self.to_position(node, ctx),
                                   self.no_info(ctx))
        return [unfold], None

    def translate_unfolding(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to the Unfolding() contract function.
        """
        if len(node.args) != 2:
            raise InvalidProgramException(node, 'invalid.contract.call')
        pred_stmt, pred = self.translate_expr(node.args[0], ctx)
        if pred_stmt:
            raise InvalidProgramException(node, 'purity.violated')
        expr_stmt, expr = self.translate_expr(node.args[1], ctx)
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
        dom_stmt, domain = self.translate_expr(domain_node, ctx)
        dom_type = self.get_type(domain_node, ctx)
        seq_ref = self.viper.SeqType(self.viper.Ref)
        formal_args = [self.viper.LocalVarDecl('self', self.viper.Ref,
                                               self.no_position(ctx),
                                               self.no_info(ctx))]
        domain_set = self.viper.FuncApp(dom_type.name + '___sil_seq__',
                                        [domain], self.no_position(ctx),
                                        self.no_info(ctx), seq_ref, formal_args)
        if var.type.name in PRIMITIVES:
            ref_var = self.box_primitive(var.ref(), var.type, None, ctx)
        else:
            ref_var = var.ref()
        result = self.viper.SeqContains(ref_var, domain_set,
                                        self.to_position(domain_node, ctx),
                                        self.no_info(ctx))
        if domain_old:
            result = self.viper.Old(result, self.to_position(domain_node, ctx),
                                    self.no_info(ctx))
        return dom_stmt, result

    def translate_forall(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
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
        body_stmt, rhs = self.translate_expr(lambda_.body.elts[0], ctx)

        triggers = self._translate_triggers(lambda_.body, node, ctx)

        ctx.remove_alias(arg.arg)
        if body_stmt:
            raise InvalidProgramException(node, 'purity.violated')

        dom_stmt, lhs = self._create_quantifier_contains_expr(var, domain_node,
                                                              ctx)

        implication = self.viper.Implies(lhs, rhs, self.to_position(node, ctx),
                                         self.no_info(ctx))
        forall = self.viper.Forall(variables, triggers, implication,
                                   self.to_position(node, ctx),
                                   self.no_info(ctx))
        return dom_stmt, forall

    def translate_contractfunc_call(self, node: ast.Call,
                                    ctx: Context) -> StmtsAndExpr:
        """
        Translates calls to contract functions like Result() and Acc()
        """
        func_name = get_func_name(node)
        if func_name == 'Result':
            return self.translate_result(node, ctx)
        elif func_name == 'RaisedException':
            return self.translate_raised_exception(node, ctx)
        elif func_name == 'Acc':
            perm = self._get_perm(node, ctx)
            if isinstance(node.args[0], ast.Call):
                return self.translate_acc_predicate(node, perm, ctx)
            else:
                return self.translate_acc_field(node, perm, ctx)
        elif func_name == 'Assert':
            return self.translate_assert(node, ctx)
        elif func_name == 'Implies':
            return self.translate_implies(node, ctx)
        elif func_name == 'Old':
            return self.translate_old(node, ctx)
        elif func_name == 'Fold':
            return self.translate_fold(node, ctx)
        elif func_name == 'Unfold':
            return self.translate_unfold(node, ctx)
        elif func_name == 'Unfolding':
            return self.translate_unfolding(node, ctx)
        elif func_name == 'Low':
            return self.translate_low(node, ctx)
        elif func_name == 'Forall':
            return self.translate_forall(node, ctx)
        elif func_name == 'Previous':
            return self.translate_previous(node, ctx)
        elif func_name == 'Seq':
            return self.translate_seq_constructor(node, ctx)
        else:
            raise UnsupportedException(node)
