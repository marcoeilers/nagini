import ast

from py2viper_translation.lib.constants import BOOL_TYPE
from py2viper_translation.lib.typedefs import Expr
from py2viper_translation.lib.util import (
    flatten,
    InvalidProgramException,
    UnsupportedException,
)
from py2viper_translation.sif.lib.context import SIFContext
from py2viper_translation.sif.lib.program_nodes import (
    SIFPythonMethod,
    TL_VAR_NAME,
)
from py2viper_translation.sif.translators.func_triple_domain_factory import (
    FuncTripleDomainFactory as FTDF,
)
from py2viper_translation.translators.pure import (
    AssignWrapper,
    NotWrapper,
    PureTranslator,
    ReturnWrapper,
    Wrapper,
)
from typing import List


class TLAssignWrapper(AssignWrapper):
    """
    Custom wrapper for an assignment to timeLevel which does not need to be
    duplicated.
    """

    def __init__(self, name: str, conds: List, expr: ast.AST,
                 node: ast.AST, sif=True):
        super().__init__(name, conds, expr, node)
        self.sif = sif


class TLJoinWrapper(AssignWrapper):
    """
    Custom wrapper for an assignment to timeLevel after an if-block.
    """
    def __init__(self, conds: List, join_wrappers: List[Wrapper]):
        super().__init__(TL_VAR_NAME, conds, None, None)
        assert len(join_wrappers) > 1
        self.join_wrappers = join_wrappers


class SIFPureTranslator(PureTranslator):
    """
    SIF version of the PureTranslator.
    """
    # TODO: The (SIF)PureTranslator needs to be refactored to move the
    # translation and processing logic into the wrappers. Using 'isinstance'
    # in so many places is bad design and contradicts the OOP concept.
    def translate_pure_If(self, conds: List, node: ast.If,
                          ctx: SIFContext):
        """
        Translates an if-block to a list of Return- and AssignWrappers which
        contain the condition(s) introduced by the if-block.
        Injects a TLAssignWrapper before the if-block.
        """
        tl_let = TLAssignWrapper(TL_VAR_NAME, conds, node.test, node)
        cond = node.test
        cond_var = ctx.current_function.create_variable('cond',
            ctx.module.global_module.classes[BOOL_TYPE], self.translator)
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
        res = [tl_let] + [cond_let] + then + else_
        # Search for the last assignment to TL in the 'then' and 'else' blocks.
        join_wrappers = [tl_let]
        for wrapper in reversed(then):
            if isinstance(wrapper, TLAssignWrapper):
                join_wrappers.append(wrapper)
                break
        for wrapper in reversed(else_):
            if isinstance(wrapper, TLAssignWrapper):
                join_wrappers.append(wrapper)
                break
        if len(join_wrappers) > 1:
            res.append(TLJoinWrapper(conds, join_wrappers))

        return res

    def translate_pure_Assign(self, conds: List, node: ast.Assign,
                              ctx: SIFContext) -> List[Wrapper]:
        """
        Translates an assign statement to an AssignWrapper. If the RHS is a
        call, generate assignment to timelevel.
        """
        wrappers = super().translate_pure_Assign(conds, node, ctx)
        if isinstance(node.value, ast.Call):
            tl_let = TLAssignWrapper(TL_VAR_NAME, conds, node.value, node,
                                     False)
            wrappers.append(tl_let)
        return wrappers

    def _translate_wrapper(self, wrapper: Wrapper, previous: Expr,
                           function: SIFPythonMethod, ctx: SIFContext) -> Expr:
        if isinstance(wrapper, ReturnWrapper):
            return self._translate_return_wrapper(wrapper, previous,
                                                  function, ctx)
        elif isinstance(wrapper, TLAssignWrapper):
            return self._translate_tl_assign_wrapper(wrapper, previous,
                                                     function, ctx)
        elif isinstance(wrapper, AssignWrapper):
            return self._translate_assign_wrapper(wrapper, previous,
                                                  function, ctx)
        else:
            raise UnsupportedException(wrapper)

    def _translate_assign_wrapper(self, wrapper: Wrapper, previous: Expr,
                                  function: SIFPythonMethod,
                                  ctx: SIFContext):
        info = self.no_info(ctx)
        position = self.to_position(wrapper.node, ctx)
        if not previous:
            raise InvalidProgramException(function.node,
                                          'function.return.missing')
        if wrapper.cond:
            if wrapper.name in ctx.var_aliases:
                old_val = ctx.var_aliases[wrapper.name].ref()
            else:
                # v
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
            new_val = self.viper.CondExp(wrapper.cond, wrapper.expr,
                                         old_val, position, info)
            return self.viper.Let(wrapper.var.decl, new_val,
                                  previous, position, info)
        else:
            return self.viper.Let(wrapper.var.decl, wrapper.expr,
                                  previous, position, info)

    def _translate_return_wrapper(self, wrapper: Wrapper, previous: Expr,
                                  function: SIFPythonMethod,
                                  ctx: SIFContext) -> Expr:
        info = self.no_info(ctx)
        position = self.to_position(wrapper.node, ctx)
        if wrapper.cond:
            if not previous:
                raise InvalidProgramException(function.node,
                                              'function.return.missing')
            return self.viper.CondExp(wrapper.cond, wrapper.expr, previous,
                                      position, info)
        else:
            if previous:
                raise InvalidProgramException(function.node,
                                              'function.dead.code')
            return wrapper.expr

    def _translate_tl_assign_wrapper(self, wrapper: Wrapper, previous: Expr,
                                     function: SIFPythonMethod,
                                     ctx: SIFContext) -> Expr:
        info = self.no_info(ctx)
        position = self.to_position(wrapper.node, ctx)
        if wrapper.cond:
            old_val = ctx.var_aliases[wrapper.name].ref()
            new_val = self.viper.CondExp(wrapper.cond, wrapper.expr,
                                         old_val, position, info)
            return self.viper.Let(wrapper.var.decl, new_val,
                                  previous, position, info)
        else:
            return self.viper.Let(wrapper.var.decl, wrapper.expr,
                                  previous, position, info)

    def _translate_to_wrappers(self, nodes: List[ast.AST],
                               ctx: SIFContext) -> List[Wrapper]:
        # Add a wrapper for '__tl_0 = __tl'
        tl_var = ctx.current_function.create_variable(TL_VAR_NAME,
            ctx.module.global_module.classes[BOOL_TYPE], self.translator)
        node = ast.Name(id=ctx.current_function.tl_var.name, ctx=ast.Load())
        tl_wrapper = TLAssignWrapper(tl_var.name, [], node, None, False)
        return [tl_wrapper] + super()._translate_to_wrappers(nodes, ctx)

    def _translate_assign_wrapper_expr(self, wrapper: Wrapper,
                                       function: SIFPythonMethod,
                                       ctx: SIFContext) -> Expr:
        if wrapper.cond:
            wrapper.cond = self._translate_condition(wrapper.cond,
                                                     wrapper.names, ctx)
        return self._translate_wrapper_expr(wrapper, ctx)

    def _translate_return_wrapper_expr(self, wrapper: Wrapper,
                                       function: SIFPythonMethod,
                                       ctx: SIFContext) -> Expr:
        info = self.no_info(ctx)
        position = self.to_position(wrapper.node, ctx)
        if wrapper.cond:
            wrapper.cond = self._translate_condition(wrapper.cond,
                                                     wrapper.names, ctx)
        # Translate expression twice (once in the prime ctx).
        val = self._translate_wrapper_expr(wrapper, ctx)
        aliases = {k: v.var_prime for (k, v) in wrapper.names.items()}
        aliases.update({k: v.var_prime for (k, v) in function.args.items()})
        ctx.set_prime_ctx(aliases=aliases)
        val_p = self._translate_wrapper_expr(wrapper, ctx)
        ctx.set_normal_ctx()
        # Create FuncTriple as return value.
        args = [val, val_p, ctx.current_tl_var_expr]
        return self.config.func_triple_factory.get_call(FTDF.CREATE,
            args, function.type, position, info, ctx)

    def _translate_tl_assign_wrapper_expr(self, wrapper: TLAssignWrapper,
                                          function: SIFPythonMethod,
                                          ctx: SIFContext) -> Expr:
        info = self.no_info(ctx)
        position = self.to_position(wrapper.node, ctx)
        tl_var = ctx.current_tl_var_expr
        # If sif is set we translate expr to 'tl || expr != expr_p'.
        if wrapper.sif:
            cond = self._translate_wrapper_expr(wrapper, ctx)
            aliases = {k: v.var_prime for (k, v) in wrapper.names.items()}
            aliases.update({k: v.var_prime for (k, v) in function.args.items()})
            ctx.set_prime_ctx(aliases=aliases)
            cond_p = self._translate_wrapper_expr(wrapper, ctx)
            ctx.set_normal_ctx()
            ne = self.viper.NeCmp(cond, cond_p, position, info)
            rhs = self.viper.Or(tl_var, ne, position, info)
        else:
            rhs = self._translate_wrapper_expr(wrapper, ctx)
        if wrapper.cond:
            wrapper.cond = self._translate_condition(wrapper.cond,
                                                     wrapper.names, ctx)
        ctx.current_tl_var_expr = wrapper.var.ref()
        return rhs

    def _translate_tl_join_wrapper_expr(self, wrapper: TLJoinWrapper,
                                          function: SIFPythonMethod,
                                          ctx: SIFContext) -> Expr:
        if wrapper.cond:
            wrapper.cond = self._translate_condition(wrapper.cond,
                                                     wrapper.names, ctx)
        pos = self.no_position(ctx)
        info = self.no_info(ctx)
        or_expr = self.viper.Or(wrapper.join_wrappers[0].var.ref(),
                                wrapper.join_wrappers[1].var.ref(),
                                pos, info)
        for wrapper in wrapper.join_wrappers[2:]:
            or_expr = self.viper.Or(or_expr, wrapper.var.ref(), pos, info)
        ctx.current_tl_var_expr = wrapper.var.ref()
        return or_expr

    def _translate_wrapper_exprs(self, wrappers: List[Wrapper],
                                 function: SIFPythonMethod,
                                 ctx: SIFContext) -> List[Wrapper]:
        """
        Translate all expressions and conditions for each wrapper.
        """
        new_wrappers =[]
        for wrapper in wrappers:
            ctx.var_aliases = wrapper.names.copy()
            if isinstance(wrapper, ReturnWrapper):
                wrapper.expr = self._translate_return_wrapper_expr(wrapper,
                    function, ctx)
                new_wrappers.append(wrapper)
            elif isinstance(wrapper, TLAssignWrapper):
                wrapper.expr = self._translate_tl_assign_wrapper_expr(wrapper,
                    function, ctx)
                new_wrappers.append(wrapper)
            elif isinstance(wrapper, TLJoinWrapper):
                wrapper.expr = self._translate_tl_join_wrapper_expr(wrapper,
                    function, ctx)
                new_wrappers.append(wrapper)
            elif isinstance(wrapper, AssignWrapper):
                aliases = {k: v.var_prime for (k, v) in wrapper.names.items()}
                aliases.update({k: v.var_prime for (k, v) in
                                function.args.items()})
                wrapper_p = AssignWrapper(wrapper.name, wrapper.cond,
                                          wrapper.expr, wrapper.node)
                wrapper_p.var = wrapper.var.var_prime
                wrapper_p.names = aliases
                wrapper.expr = self._translate_assign_wrapper_expr(wrapper,
                    function, ctx)
                ctx.set_prime_ctx(aliases=aliases)
                wrapper_p.expr = self._translate_assign_wrapper_expr(wrapper_p,
                    function, ctx)
                ctx.set_normal_ctx()
                new_wrappers.append(wrapper)
                new_wrappers.append(wrapper_p)
            else:
                raise UnsupportedException(wrapper.node)
        return new_wrappers

    def translate_exprs(self, nodes: List[ast.AST],
                        function: SIFPythonMethod, ctx: SIFContext) -> Expr:
        # Reset the context to make sure it doesn't contain any artifacts from
        # from previous functions.
        ctx.reset()
        # Translate to wrapper objects
        wrappers = self._translate_to_wrappers(nodes, ctx)
        self._collect_names(wrappers, function)

        # Walk through wrappers and translate all expressions and conditions.
        wrappers = self._translate_wrapper_exprs(wrappers, function, ctx)

        # Walk through wrappers in reverse an connect them all to one big
        # expression.
        previous = None
        for wrapper in reversed(wrappers):
            ctx.var_aliases = wrapper.names.copy()
            previous = self._translate_wrapper(wrapper, previous, function, ctx)

        ctx.var_aliases = {}
        return previous
