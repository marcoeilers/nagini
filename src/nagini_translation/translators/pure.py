"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import ast

from typing import Dict, List, Union

from nagini_translation.lib.constants import BOOL_TYPE
from nagini_translation.lib.program_nodes import PythonMethod, PythonType, PythonVar
from nagini_translation.lib.typedefs import (
    Expr,
)
from nagini_translation.lib.util import (
    flatten,
    InvalidProgramException,
    UnsupportedException,
)
from nagini_translation.translators.abstract import Context
from nagini_translation.translators.common import CommonTranslator


class AssignWrapper:
    """
    Represents an assignment of expr to a var named name, to
    be executed under conditions conds.
    """

    def __init__(self, name: str, conds: List, expr: ast.AST, node: ast.AST):
        self.name = name
        self.cond = conds
        self.expr = expr
        self.node = node
        self.names = {}
        self.var = None


class ReturnWrapper:
    """
    Represents a return of expr, to be executed under condition conds.
    """
    def __init__(self, cond: List, expr: ast.AST, node: ast.AST):
        self.cond = cond
        self.expr = expr
        self.node = node
        self.names = {}


class NotWrapper:
    """
    Represents a negation of the condition cond.
    """
    def __init__(self, cond):
        self.cond = cond


class BinOpWrapper:
    """
    Represents a binary operation to be performed on a variable;
    used to encode augmented assignments
    """
    def __init__(self, op: ast.BinOp, rhs: ast.AST):
        self.op = op
        self.rhs = rhs

Wrapper = Union[AssignWrapper, ReturnWrapper]


class PureTranslator(CommonTranslator):

    def translate_pure(self, conds: List, node: ast.AST,
                       ctx: Context) -> List[Wrapper]:
        method = 'translate_pure_' + node.__class__.__name__
        visitor = getattr(self, method, self.translate_pure_generic)
        return visitor(conds, node, ctx)

    def translate_pure_generic(self, conds: List,
                               node: ast.AST, ctx: Context) -> List[Wrapper]:
        raise UnsupportedException(node)

    def translate_pure_Expr(self, conds: List, node: ast.Expr,
                            ctx: Context) -> List[Wrapper]:
        if isinstance(node.value, ast.Str):
            # Ignore docstrings.
            return []
        raise UnsupportedException(node)

    def translate_pure_If(self, conds: List, node: ast.If,
                          ctx: Context) -> List[Wrapper]:
        """
        Translates an if-block to a list of Return- and AssignWrappers which
        contain the condition(s) introduced by the if-block.
        """
        cond = node.test
        cond_var = ctx.current_function.create_variable('cond',
            ctx.module.global_module.classes[BOOL_TYPE], self.translator)
        cond_let = AssignWrapper(cond_var.sil_name, conds, cond, node)
        then_cond = conds + [cond_var.sil_name]
        else_cond = conds + [NotWrapper(cond_var.sil_name)]
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
        wrapper = AssignWrapper(node.target.id, conds, val, node)
        return [wrapper]

    def translate_pure_Assign(self, conds: List, node: ast.Assign,
                              ctx: Context) -> List[Wrapper]:
        """
        Translates an assign statement to an AssignWrapper
        """
        assert len(node.targets) == 1
        assert isinstance(node.targets[0], ast.Name)
        wrapper = AssignWrapper(node.targets[0].id, conds, node.value, node)
        return [wrapper]

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
                return val
        else:
            if previous:
                raise InvalidProgramException(function.node,
                                              'function.dead.code')
            return val

    def _translate_assign_wrapper(self, wrapper: Wrapper, previous: Expr,
                                  function: PythonMethod,
                                  ctx: Context) -> Expr:
        info = self.no_info(ctx)
        position = self.to_position(wrapper.node, ctx)
        val = self.to_ref(self._translate_wrapper_expr(wrapper, ctx), ctx)
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
                old_val = self.to_ref(dummies[wrapper.var.decl.typ()], ctx)
            new_val = self.viper.CondExp(cond, val, old_val, position,
                                         info)
            return self.viper.Let(wrapper.var.decl, new_val,
                                  previous, position, info)
        else:
            return self.viper.Let(wrapper.var.decl, val,
                                  previous, position, info)

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
        for cond in conds:
            if isinstance(cond, NotWrapper):
                current = self.to_bool(ctx.var_aliases.get(cond.cond).ref(), ctx)
                current = self.viper.Not(current, self.no_position(ctx),
                                         self.no_info(ctx))
            else:
                current = ctx.var_aliases.get(cond).ref()
            previous = self.viper.And(self.to_bool(previous, ctx),
                                      self.to_bool(current, ctx),
                                      self.no_position(ctx),
                                      self.no_info(ctx))
        return previous
