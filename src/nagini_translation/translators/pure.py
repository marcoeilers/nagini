"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import ast

from typing import Dict, List, Union

from nagini_contracts.contracts import CONTRACT_WRAPPER_FUNCS
from nagini_translation.lib.constants import (
    ASSUMING_FUNC, BOOL_TYPE, IS_DEFINED_FUNC, PRIMITIVE_BOOL_TYPE
)
from nagini_translation.lib.program_nodes import PythonMethod, PythonType, PythonVar
from nagini_translation.lib.typedefs import (
    Expr,
)
from nagini_translation.lib.util import (
    flatten,
    get_func_name,
    InvalidProgramException,
    isStr,
    UnsupportedException,
)
from nagini_translation.translators.abstract import Context
from nagini_translation.translators.common import CommonTranslator


class AssignWrapper:
    """
    Represents an assignment of expr to a var named name, to
    be executed under conditions conds.
    """

    def __init__(self, name: str, conds: List, expr: ast.AST, node: ast.AST,
                 user_var: bool = False):
        self.name = name
        self.cond = conds
        self.expr = expr
        self.node = node
        self.names = {}
        self.var = None
        self.user_var = user_var


class ReturnWrapper:
    """
    Represents a return of expr, to be executed under condition conds.
    """
    def __init__(self, cond: List, expr: ast.AST, node: ast.AST):
        self.cond = cond
        self.expr = expr
        self.node = node
        self.names = {}


class UnfoldWrapper:
    """
    Represents an unfolding of predicate pred, to be executed under conditions conds.
    """

    def __init__(self, conds: List, pred: ast.AST, node: ast.AST):
        self.cond = conds
        self.pred = pred
        self.node = node
        self.names = {}
        self.var = None


class AssertWrapper:
    """
    Represents an asserting of assertion a, to be executed under conditions conds.
    """

    def __init__(self, conds: List, a: ast.AST, node: ast.AST):
        self.cond = conds
        self.a = a
        self.node = node
        self.names = {}
        self.var = None



class NotWrapper:
    """
    Represents a negation of the condition cond.
    """
    def __init__(self, cond, node):
        self.cond = cond
        self.node = node

class CondWrapper:
    """
    Represents the condition cond.
    """
    def __init__(self, cond, node):
        self.cond = cond
        self.node = node


class BinOpWrapper:
    """
    Represents a binary operation to be performed on a variable;
    used to encode augmented assignments
    """
    def __init__(self, op: ast.BinOp, rhs: ast.AST):
        self.op = op
        self.rhs = rhs


class MatchPatternExpr:
    """
    Sentinel stored in AssignWrapper.expr for deferred match-pattern condition evaluation.
    Resolved in _translate_wrapper_expr by calling _translate_match_pattern_cond.
    """
    def __init__(self, subj_sil_name: str, pattern: ast.AST, subj_type,
                 match_node: ast.Match, guard=None, guard_aliases=None):
        self.subj_sil_name = subj_sil_name
        self.pattern = pattern
        self.subj_type = subj_type
        self.match_node = match_node
        self.guard = guard
        self.guard_aliases = guard_aliases or {}


class SubjectVarRef:
    """
    Sentinel stored in AssignWrapper.expr that resolves to the match subject variable.
    Used to encode capture-variable assignments in pure match translation.
    """
    def __init__(self, subj_sil_name: str):
        self.subj_sil_name = subj_sil_name


Wrapper = Union[AssignWrapper, ReturnWrapper, UnfoldWrapper, AssertWrapper]


class PureTranslator(CommonTranslator):

    def translate_pure(self, conds: List, node: ast.AST,
                       ctx: Context) -> List[Wrapper]:
        method = 'translate_pure_' + node.__class__.__name__
        visitor = getattr(self, method, self.translate_pure_generic)
        return visitor(conds, node, ctx)

    def translate_pure_generic(self, conds: List,
                               node: ast.AST, ctx: Context) -> List[Wrapper]:
        raise UnsupportedException(node, f'unsupported statement type in pure function: {node.__class__.__name__}')

    def translate_pure_Expr(self, conds: List, node: ast.Expr,
                            ctx: Context) -> List[Wrapper]:
        if isStr(node.value):
            # Ignore docstrings.
            return []
        if isinstance(node.value, ast.Call) and get_func_name(node.value) in CONTRACT_WRAPPER_FUNCS:
            raise InvalidProgramException(node, 'invalid.contract.position')
        if isinstance(node.value, ast.Call) and get_func_name(node.value) == 'Unfold':
            wrapper = UnfoldWrapper(conds, node.value, node)
            return [wrapper]
        if isinstance(node.value, ast.Call) and get_func_name(node.value) == 'Assert':
            wrapper = AssertWrapper(conds, node.value, node)
            return [wrapper]
        raise UnsupportedException(node, 'unsupported expression in pure function; only Unfold, Assert, assignments, and docstrings are supported')

    def translate_pure_If(self, conds: List, node: ast.If,
                          ctx: Context) -> List[Wrapper]:
        """
        Translates an if-block to a list of Return- and AssignWrappers which
        contain the condition(s) introduced by the if-block.
        """
        cond = node.test
        cond_var = ctx.current_function.create_variable('cond',
            ctx.module.global_module.classes[PRIMITIVE_BOOL_TYPE], self.translator)
        cond_let = AssignWrapper(cond_var.sil_name, conds, cond, node)
        then_cond = conds + [CondWrapper(cond_var.sil_name, node.test)]
        else_cond = conds + [NotWrapper(cond_var.sil_name, node.test)]
        then = [self.translate_pure(then_cond, stmt, ctx) for stmt in node.body]
        then = flatten(then)
        else_ = []
        if node.orelse:
            else_ = [self.translate_pure(else_cond, stmt, ctx) for stmt
                     in node.orelse]
            else_ = flatten(else_)
        return [cond_let] + then + else_

    def translate_pure_Return(self, conds: List, node: ast.Return,
                              ctx: Context) -> List[Wrapper]:
        """
        Translates a return statement to a ReturnWrapper
        """
        wrapper = ReturnWrapper(conds, node.value, node)
        return [wrapper]

    def translate_pure_AugAssign(self, conds: List, node: ast.AugAssign,
                                 ctx: Context) -> List[Wrapper]:
        """
        Translates an augmented assign statement to an AssignWrapper
        """
        assert isinstance(node.target, ast.Name)
        val = BinOpWrapper(node.op, node.value)
        wrapper = AssignWrapper(node.target.id, conds, val, node, user_var=True)
        return [wrapper]

    def translate_pure_Assign(self, conds: List, node: ast.Assign,
                              ctx: Context) -> List[Wrapper]:
        """
        Translates an assign statement to an AssignWrapper
        """
        assert len(node.targets) == 1
        if not isinstance(node.targets[0], ast.Name):
            raise UnsupportedException(node, "Multi-target assignments are not supported in pure functions.")
        wrapper = AssignWrapper(node.targets[0].id, conds, node.value, node, user_var=True)
        return [wrapper]

    def translate_pure_AnnAssign(self, conds: List, node: ast.AnnAssign,
                                 ctx: Context) -> List[Wrapper]:
        """
        Translates an annotated assign statement to an AssignWrapper
        """
        if not isinstance(node.target, ast.Name):
            raise UnsupportedException(node, "Only assignments to single variables are supported in pure functions.")
        wrapper = AssignWrapper(node.target.id, conds, node.value, node, user_var=True)
        return [wrapper]

    def translate_pure_Match(self, conds: List, node: ast.Match,
                             ctx: Context) -> List[Wrapper]:
        """
        Translates a match statement to a list of wrappers for the pure translator.
        Each case becomes an AssignWrapper holding a MatchPatternExpr condition,
        followed by capture AssignWrappers and body wrappers.
        """
        subject_type = self.get_type(node.subject, ctx)
        bool_class = ctx.module.global_module.classes[PRIMITIVE_BOOL_TYPE]

        subj_var = ctx.current_function.create_variable(
            'match_subject', subject_type, self.translator)
        subj_wrapper = AssignWrapper(subj_var.sil_name, conds, node.subject, node)

        result = [subj_wrapper]
        prev_conds = list(conds)

        for case in node.cases:
            guard_aliases = {}
            if case.guard is not None:
                for name in self._collect_match_guard_capture_names(case.pattern):
                    guard_aliases[name] = subj_var.sil_name

            case_var = ctx.current_function.create_variable(
                'match_case', bool_class, self.translator)
            case_expr = MatchPatternExpr(
                subj_var.sil_name, case.pattern, subject_type, node,
                guard=case.guard, guard_aliases=guard_aliases)
            case_wrapper = AssignWrapper(case_var.sil_name, prev_conds, case_expr, node)
            result.append(case_wrapper)

            case_conds = prev_conds + [CondWrapper(case_var.sil_name, node)]
            for cap_name, cap_expr in self._collect_pure_match_captures(
                    case.pattern, subj_var.sil_name, node):
                cap_wrapper = AssignWrapper(cap_name, case_conds, cap_expr, node,
                                            user_var=True)
                result.append(cap_wrapper)

            body_wrappers = flatten([self.translate_pure(case_conds, stmt, ctx)
                                     for stmt in case.body])
            result.extend(body_wrappers)

            prev_conds = prev_conds + [NotWrapper(case_var.sil_name, node)]

        return result

    def _collect_pure_match_captures(self, pattern: ast.AST, subj_sil_name: str,
                                     node: ast.Match):
        """Yield (python_name, SubjectVarRef) for each variable bound by pattern."""
        if isinstance(pattern, ast.MatchAs):
            if pattern.name is not None:
                yield pattern.name, SubjectVarRef(subj_sil_name)
            if pattern.pattern is not None:
                yield from self._collect_pure_match_captures(
                    pattern.pattern, subj_sil_name, node)
        if isinstance(pattern, ast.MatchClass):
            if pattern.patterns or pattern.kwd_patterns:
                raise UnsupportedException(
                    pattern, 'class patterns with parameters not yet supported')
            for kwd_pattern in pattern.kwd_patterns:
                yield from self._collect_pure_match_captures(
                    kwd_pattern, subj_sil_name, node)

    def _collect_match_guard_capture_names(self, pattern: ast.AST):
        """Yield names that a guard expression might reference from the pattern."""
        if isinstance(pattern, ast.MatchAs):
            if pattern.name is not None:
                yield pattern.name
            if pattern.pattern is not None:
                yield from self._collect_match_guard_capture_names(pattern.pattern)
        if isinstance(pattern, ast.MatchClass):
            if pattern.patterns or pattern.kwd_patterns:
                raise UnsupportedException(
                    pattern, 'class patterns with parameters not yet supported')
            for kwd_pattern in pattern.kwd_patterns:
                yield from self._collect_match_guard_capture_names(kwd_pattern)

    def _translate_return_wrapper(self, wrapper: Wrapper, previous: Expr,
                                  function: PythonMethod,
                                  ctx: Context) -> Expr:
        info = self.no_info(ctx)
        position = self.to_position(wrapper.node, ctx)
        val = self._translate_wrapper_expr(wrapper, ctx)
        if wrapper.cond:
            cond = self._translate_condition(wrapper.cond,
                                             wrapper.names, ctx)
            if previous:
                return self.viper.CondExp(self.to_bool(cond, ctx), val,
                                          previous, position, info)
            else:
                # No fallback expression yet: this is the last return in program
                # order, and it is guarded by a condition.  Wrap the missing-path
                # in `asserting false in dummy` so the verifier rejects any
                # execution path that does not reach an explicit return.
                # Paths where the condition is provably always true (e.g. due to
                # preconditions or exhaustive branches) pass without a complaint.
                no_pos = self.no_position(ctx)
                no_inf = self.no_info(ctx)
                false_lit = self.viper.FalseLit(no_pos, no_inf)
                dummies = {
                    self.viper.Int:  self.viper.IntLit(0, no_pos, no_inf),
                    self.viper.Bool: self.viper.FalseLit(no_pos, no_inf),
                    self.viper.Ref:  self.viper.NullLit(no_pos, no_inf),
                }
                dummy = dummies.get(val.typ(), self.viper.NullLit(no_pos, no_inf))
                fallback = self.viper.Asserting(false_lit, dummy, position, no_inf)
                return self.viper.CondExp(self.to_bool(cond, ctx), val,
                                          fallback, position, info)
        else:
            if previous:
                raise InvalidProgramException(function.node,
                                              'function.dead.code')
            return val

    def _wrap_with_assuming(self, val: Expr, python_name: str, position,
                            info, ctx: Context) -> Expr:
        """Wrap val in _assuming(val, _isDefined(id)) to produce the definedness fact."""
        id_param_decl = self.viper.LocalVarDecl('id', self.viper.Int, position, info)
        r_param_decl = self.viper.LocalVarDecl('r', self.viper.Ref, position, info)
        fact_param_decl = self.viper.LocalVarDecl('fact', self.viper.Bool, position, info)
        id_lit = self.viper.IntLit(self._get_string_value(python_name), position, info)
        is_defined = self.viper.FuncApp(IS_DEFINED_FUNC, [id_lit], position, info,
                                        self.viper.Bool, [id_param_decl])
        return self.viper.FuncApp(ASSUMING_FUNC, [val, is_defined], position, info,
                                  self.viper.Ref, [r_param_decl, fact_param_decl])

    def _translate_assign_wrapper(self, wrapper: Wrapper, previous: Expr,
                                  function: PythonMethod,
                                  ctx: Context) -> Expr:
        info = self.no_info(ctx)
        position = self.to_position(wrapper.node, ctx)
        val = self._translate_wrapper_expr(wrapper, ctx)
        val = self.to_type(val, wrapper.var.decl.typ(), ctx)
        if wrapper.user_var and wrapper.var.decl.typ() == self.viper.Ref:
            val = self._wrap_with_assuming(val, wrapper.name, position, info, ctx)
        if not previous:
            raise InvalidProgramException(function.node,
                                          'function.return.missing')
        if wrapper.cond:
            cond = self._translate_condition(wrapper.cond,
                                             wrapper.names, ctx)
            if wrapper.name in ctx.var_aliases:
                old_val = ctx.var_aliases[wrapper.name].ref()
            else:
                # Variable newly defined in conditional branch, so
                # there is no old value; the variable is not defined
                # if the condition is false.
                # Our encoding requires some value though, even
                # though that will never be used, so we take some dummy
                # value.
                zero = self.viper.IntLit(0, self.no_position(ctx),
                                         self.no_info(ctx))
                false = self.viper.FalseLit(self.no_position(ctx),
                                            self.no_info(ctx))
                null = self.viper.NullLit(self.no_position(ctx),
                                          self.no_info(ctx))
                dummies = {
                    self.viper.Int: zero,
                    self.viper.Bool: false,
                    self.viper.Ref: null
                }
                old_val = dummies[wrapper.var.decl.typ()]
            new_val = self.viper.CondExp(cond, val, self.to_type(old_val, val.typ(), ctx), position,
                                         info)
            return self.viper.Let(wrapper.var.decl, new_val,
                                  previous, position, info)
        else:
            return self.viper.Let(wrapper.var.decl, val,
                                  previous, position, info)

    def _translate_unfold_wrapper(self, wrapper: Wrapper, previous: Expr,
                                  function: PythonMethod,
                                  ctx: Context) -> Expr:
        info = self.no_info(ctx)
        position = self.to_position(wrapper.node, ctx)
        if not previous:
            raise InvalidProgramException(function.node,
                                          'function.return.missing')

        if len(wrapper.pred.args) != 1:
            raise InvalidProgramException(wrapper.pred, 'invalid.contract.call')
        if not isinstance(wrapper.pred.args[0], ast.Call):
            raise InvalidProgramException(wrapper.pred, 'invalid.contract.call')
        if get_func_name(wrapper.pred.args[0]) in ('Acc', 'Rd'):
            pred_call = wrapper.pred.args[0].args[0]
        else:
            pred_call = wrapper.pred.args[0]
        target_pred = self.get_target(pred_call, ctx)
        if (target_pred and
                (not isinstance(target_pred, PythonMethod) or not target_pred.predicate)):
            raise InvalidProgramException(wrapper.pred, 'invalid.contract.call')
        if target_pred and target_pred.contract_only:
            raise InvalidProgramException(wrapper.pred, 'abstract.predicate.fold')
        pred_stmt, pred = self.translate_expr(wrapper.pred.args[0], ctx,
                                              self.viper.Bool, True)
        if pred_stmt:
            raise InvalidProgramException(wrapper.node, 'purity.violated')

        unfolding = self.viper.Unfolding(pred, previous, position, info)

        if wrapper.cond:
            cond = self._translate_condition(wrapper.cond,
                                             wrapper.names, ctx)

            new_val = self.viper.CondExp(cond, unfolding, previous, position,
                                         info)
            return new_val
        else:
            return unfolding

    def _translate_assert_wrapper(self, wrapper: Wrapper, previous: Expr,
                                  function: PythonMethod,
                                  ctx: Context) -> Expr:
        info = self.no_info(ctx)
        position = self.to_position(wrapper.node, ctx)
        if not previous:
            raise InvalidProgramException(function.node,
                                          'function.return.missing')

        if len(wrapper.a.args) != 1:
            raise InvalidProgramException(wrapper.a, 'invalid.contract.call')

        ass_stmt, ass = self.translate_expr(wrapper.a.args[0], ctx,
                                            self.viper.Bool, True)
        if ass_stmt:
            raise InvalidProgramException(wrapper.node, 'purity.violated')

        asserting = self.viper.Asserting(ass, previous, position, info)

        if wrapper.cond:
            cond = self._translate_condition(wrapper.cond,
                                             wrapper.names, ctx)

            new_val = self.viper.CondExp(cond, asserting, previous, position,
                                         info)
            return new_val
        else:
            return asserting

    def _translate_wrapper_expr(self, wrapper: Wrapper,
                                ctx: Context) -> Expr:
        info = self.no_info(ctx)
        position = self.to_position(wrapper.node, ctx)
        if isinstance(wrapper.expr, BinOpWrapper):
            assert isinstance(wrapper, AssignWrapper)
            stmt, val = self.translate_expr(wrapper.expr.rhs, ctx)
            val = self.to_int(val, ctx)
            var = ctx.var_aliases[wrapper.name].ref()
            var = self.to_int(var, ctx)
            if isinstance(wrapper.expr.op, ast.Add):
                val = self.viper.Add(var, val, position, info)
            elif isinstance(wrapper.expr.op, ast.Sub):
                val = self.viper.Sub(var, val, position, info)
            elif isinstance(wrapper.expr.op, ast.Mult):
                val = self.viper.Mul(var, val, position, info)
            else:
                raise UnsupportedException(wrapper.node)
        elif isinstance(wrapper.expr, SubjectVarRef):
            return ctx.var_aliases[wrapper.expr.subj_sil_name].ref()
        elif isinstance(wrapper.expr, MatchPatternExpr):
            mpe = wrapper.expr
            subj_ref = ctx.var_aliases[mpe.subj_sil_name].ref()
            stmt_translator = self.config.stmt_translator
            stmts, val = stmt_translator._translate_match_pattern_cond(
                mpe.pattern, subj_ref, mpe.subj_type, mpe.match_node, ctx)
            if stmts:
                raise InvalidProgramException(mpe.match_node, 'purity.violated')
            if mpe.guard is not None:
                with ctx.aliases_context():
                    for cap_name, sil_name in mpe.guard_aliases.items():
                        ctx.set_alias(cap_name, ctx.var_aliases[sil_name], None)
                    guard_stmts, guard_expr = self.translate_expr(
                        mpe.guard, ctx, target_type=self.viper.Bool)
                if guard_stmts:
                    raise InvalidProgramException(mpe.match_node, 'purity.violated')
                guard_pos = self.to_position(mpe.guard, ctx)
                val = self.viper.And(val, guard_expr, guard_pos, info)
            return val
        else:
            stmt, val = self.translate_expr(wrapper.expr, ctx)
        if stmt:
            raise InvalidProgramException(wrapper.expr,
                                          'purity.violated')
        return val

    def _translate_wrapper(self, wrapper: Wrapper, previous: Expr,
                           function: PythonMethod, ctx: Context) -> Expr:
        if isinstance(wrapper, ReturnWrapper):
            return self._translate_return_wrapper(wrapper, previous,
                                                  function, ctx)
        elif isinstance(wrapper, AssignWrapper):
            return self._translate_assign_wrapper(wrapper, previous,
                                                  function, ctx)
        elif isinstance(wrapper, UnfoldWrapper):
            return self._translate_unfold_wrapper(wrapper, previous,
                                                  function, ctx)
        elif isinstance(wrapper, AssertWrapper):
            return self._translate_assert_wrapper(wrapper, previous,
                                                  function, ctx)
        else:
            raise UnsupportedException(wrapper)

    def _translate_to_wrappers(self, nodes: List[ast.AST],
                               ctx: Context) -> List[Wrapper]:
        return flatten([self.translate_pure([], node, ctx)for node in nodes])

    def _collect_names(self, wrappers: List[Wrapper], function: PythonMethod):
        """
        First walk through wrappers. For every assignment, we create a new
        variable with a different name. Future references to the original
        name need to refer to the new name, so we create dicts that map old
        to new names.
        """
        previous = None
        added = {}

        for wrapper in wrappers:
            if previous:
                wrapper.names.update(previous.names)
            if added:
                wrapper.names.update(added)
            added = {}
            if isinstance(wrapper, AssignWrapper):
                name = wrapper.name
                cls = self._get_wrapper_var_type(wrapper, function)
                new_name = function.create_variable(name, cls, self.translator)
                added[name] = new_name
                wrapper.var = new_name
            previous = wrapper

    def _get_wrapper_var_type(self, wrapper: AssignWrapper,
                              function: PythonMethod) -> PythonType:
        name = wrapper.name
        cls = function.get_variable(name).type
        return cls

    def translate_exprs(self, nodes: List[ast.AST],
                        function: PythonMethod, ctx: Context) -> Expr:
        """
        Translates a list of nodes to a single (let-)expression if the nodes
        are only returns, assignments and if-blocks. First translates them to
        Assign- and ReturnWrappers with conditions derived from surrounding
        if-blocks (if any), then creates one big expression out of a list
        of wrappers.
        """
        # Translate to wrapper objects
        wrappers = self._translate_to_wrappers(nodes, ctx)
        self._collect_names(wrappers, function)

        # Second walk through wrappers, starting at the end. Translate all of
        # them into one big expression. Assigns become a let, returns just the
        # returned value, and if something happens in an if block, we put it
        assert not ctx.var_aliases
        previous = None
        for wrapper in reversed(wrappers):
            ctx.var_aliases = wrapper.names.copy()
            previous = self._translate_wrapper(wrapper, previous, function, ctx)

        ctx.var_aliases = {}
        return previous

    def _translate_condition(self, conds: List, names: Dict[str, PythonVar],
                             ctx: Context) -> Expr:
        """
        Translates the conditions in conds to a big conjunctive expression,
        using the renamings in names.
        """
        previous = self.viper.TrueLit(self.no_position(ctx), self.no_info(ctx))
        previous_node = None
        for cond in conds:
            if isinstance(cond, NotWrapper):
                current = self.to_bool(ctx.var_aliases.get(cond.cond).ref(cond.node, ctx), ctx)
                current = self.viper.Not(current, self.no_position(ctx),
                                         self.no_info(ctx))
                cur_node = ast.UnaryOp(ast.Not(), cond.node, lineno=cond.node.lineno, col_offset=cond.node.col_offset,
                                       end_lineno=cond.node.end_lineno)
            elif isinstance(cond, CondWrapper):
                current = self.to_bool(ctx.var_aliases.get(cond.cond).ref(cond.node, ctx), ctx)
                cur_node = cond.node
            else:
                raise Exception()
            if not previous_node:
                previous_node = cur_node
            else:
                previous_node = ast.BoolOp(ast.And(), [previous_node, cur_node], lineno=previous_node.lineno,
                                           end_lineno=cur_node.end_lineno, col_offset=previous_node.col_offset)
            previous = self.viper.And(self.to_bool(previous, ctx),
                                      self.to_bool(current, ctx),
                                      self.to_position(previous_node, ctx),
                                      self.no_info(ctx))
        return previous
