import ast

from py2viper_translation.abstract_translator import (
    CommonTranslator,
    TranslatorConfig,
    Expr,
    StmtAndExpr
)
from py2viper_translation.analyzer import PythonMethod, PythonVar
from py2viper_translation.util import (
    UnsupportedException,
    InvalidProgramException,
    flatten
)
from typing import List, Tuple, Optional, Union, Dict



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

Wrapper = Union[AssignWrapper, ReturnWrapper]

class PureTranslator(CommonTranslator):

    def translate_pure(self, conds: List, node: ast.AST, ctx) -> List[Wrapper]:
        method = 'translate_pure_' + node.__class__.__name__
        visitor = getattr(self, method, self.translate_pure_generic)
        return visitor(conds, node, ctx)

    def translate_pure_generic(self, conds: List,
                               node: ast.AST, ctx) -> List[Wrapper]:
        raise UnsupportedException(node)

    def translate_pure_If(self, conds: List, node: ast.If, ctx) -> List[Wrapper]:
        """
        Translates an if-block to a list of Return- and AssignWrappers which
        contain the condition(s) introduced by the if-block.
        """
        cond = node.test
        cond_var = ctx.current_function.create_variable('cond',
            ctx.program.classes['bool'], self.translator)
        cond_let = AssignWrapper(cond_var.name, conds, cond, node)
        then_cond = conds + [cond_var.name]
        else_cond = conds + [NotWrapper(cond_var.name)]
        then = [self.translate_pure(then_cond, stmt, ctx) for stmt in node.body]
        then = flatten(then)
        else_ = []
        if node.orelse:
            else_ = [self.translate_pure(else_cond, stmt, ctx) for stmt
                     in node.orelse]
            else_ = flatten(else_)
        return [cond_let] + then + else_

    def translate_pure_Return(self, conds: List,
                              node: ast.Return, ctx) -> List[Wrapper]:
        """
        Translates a return statement to a ReturnWrapper
        """
        wrapper = ReturnWrapper(conds, node.value, node)
        return [wrapper]

    def translate_pure_Assign(self, conds: List,
                              node: ast.Assign, ctx) -> List[Wrapper]:
        """
        Translates an assign statement to an AssignWrapper
        """
        assert len(node.targets) == 1
        assert isinstance(node.targets[0], ast.Name)
        wrapper = AssignWrapper(node.targets[0].id, conds, node.value, node)
        return [wrapper]

    def translate_exprs(self, nodes: List[ast.AST],
                        function: PythonMethod, ctx) -> Expr:
        """
        Translates a list of nodes to a single (let-)expression if the nodes
        are only returns, assignments and if-blocks. First translates them to
        Assign- and ReturnWrappers with conditions derived from surrounding
        if-blocks (if any), then creates one big expression out of a list
        of wrappers.
        """
        # Translate to wrapper objects
        wrappers = flatten([self.translate_pure([], node, ctx) for node in nodes])
        previous = None
        added = {}
        # First walk through wrappers. For every assignment, we create a new
        # variable with a different name. Future references to the original
        # name need to refer to the new name, so we create dicts that map old
        # to new names.
        for wrapper in wrappers:
            if previous:
                wrapper.names.update(previous.names)
            if added:
                wrapper.names.update(added)
            added = {}
            if isinstance(wrapper, AssignWrapper):
                name = wrapper.name
                cls = function.get_variable(name).type
                new_name = function.create_variable(name, cls, self.translator)
                added[name] = new_name
                wrapper.variable = new_name
            previous = wrapper
        previous = None
        info = self.noinfo(ctx)
        assert not ctx.var_aliases
        # Second walk through wrappers, starting at the end. Translate all of
        # them into one big expression. Assigns become a let, returns just the
        # returned value, and if something happens in an if block, we put it
        # into an if-expression.
        for wrapper in reversed(wrappers):
            position = self.to_position(wrapper.node, ctx)
            ctx.var_aliases = wrapper.names
            stmt, val = self.translate_expr(wrapper.expr, ctx)
            if stmt:
                raise InvalidProgramException(wrapper.expr,
                                              'purity.violated')
            if isinstance(wrapper, ReturnWrapper):
                if wrapper.cond:
                    if not previous:
                        raise InvalidProgramException(function.node,
                                                      'function.return.missing')
                    cond = self._translate_condition(wrapper.cond,
                                                     wrapper.names, ctx)
                    previous = self.viper.CondExp(cond, val, previous, position,
                                                  info)
                else:
                    if previous:
                        raise InvalidProgramException(function.node,
                                                      'function.dead.code')
                    previous = val
            elif isinstance(wrapper, AssignWrapper):
                if not previous:
                    raise InvalidProgramException(function.node,
                                                  'function.return.missing')
                if wrapper.cond:
                    cond = self._translate_condition(wrapper.cond,
                                                     wrapper.names, ctx)
                    old_val = wrapper.names[wrapper.name].ref
                    new_val = self.viper.CondExp(cond, val, old_val, position,
                                                 info)
                    let = self.viper.Let(wrapper.variable.decl, new_val,
                                         previous, position, info)
                    previous = let
                else:
                    let = self.viper.Let(wrapper.variable.decl, val,
                                         previous, position, info)
                    previous = let
            else:
                raise UnsupportedException(wrapper)
        ctx.var_aliases = None
        return previous


    def _translate_condition(self, conds: List,
                             names: Dict[str, PythonVar], ctx) -> Expr:
        """
        Translates the conditions in conds to a big conjunctive expression,
        using the renamings in names.
        """
        previous = self.viper.TrueLit(self.noposition(ctx), self.noinfo(ctx))
        for cond in conds:
            if isinstance(cond, NotWrapper):
                current = names.get(cond.cond).ref
                current = self.viper.Not(current, self.noposition(ctx),
                                         self.noinfo(ctx))
            else:
                current = names.get(cond).ref
            previous = self.viper.And(previous, current, self.noposition(ctx),
                                      self.noinfo(ctx))
        return previous