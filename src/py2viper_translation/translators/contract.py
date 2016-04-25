import ast

from py2viper_contracts.contracts import CONTRACT_WRAPPER_FUNCS
from py2viper_translation.lib.util import (
    get_func_name,
    InvalidProgramException,
    UnsupportedException,
)
from py2viper_translation.translators.abstract import (
    CommonTranslator,
    Context,
    Expr,
    StmtsAndExpr,
)


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
        type = ctx.current_function.type
        if not ctx.current_function.pure:
            return [], ctx.current_function.result.ref
        else:
            return ([], self.viper.Result(self.translate_type(type, ctx),
                                          self.to_position(node, ctx),
                                          self.no_info(ctx)))

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
            pred = ctx.program.get_predicate(call.func.id)
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
        return [], self.create_predicate_access(pred_name, args, perm,
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
        res = self.viper.Old(exp, self.to_position(node, ctx), self.no_info(ctx))
        return stmt, res

    def translate_fold(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to the Fold() contract function.
        """
        if len(node.args) != 1:
            raise InvalidProgramException(node, 'invalid.contract.call')
        pred_stmt, pred = self.translate_expr(node.args[0], ctx)
        if pred_stmt:
            raise InvalidProgramException(node, 'purity.violated')
        fold = self.viper.Fold(pred, self.to_position(node, ctx),
                               self.no_info(ctx))
        return [fold], None

    def translate_unfold(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to the Unfold() contract function.
        """
        if len(node.args) != 1:
            raise InvalidProgramException(node, 'invalid.contract.call')
        pred_stmt, pred = self.translate_expr(node.args[0], ctx)
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

    def translate_contractfunc_call(self, node: ast.Call,
                                    ctx: Context) -> StmtsAndExpr:
        """
        Translates calls to contract functions like Result() and Acc()
        """
        func_name = get_func_name(node)
        if func_name == 'Result':
            return self.translate_result(node, ctx)
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
        else:
            raise UnsupportedException(node)
