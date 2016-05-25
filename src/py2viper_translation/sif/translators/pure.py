import ast

from py2viper_translation.lib.constants import TUPLE_TYPE, BOOL_TYPE
from py2viper_translation.lib.program_nodes import PythonVar
from py2viper_translation.lib.util import InvalidProgramException, \
    UnsupportedException
from py2viper_translation.sif.lib.context import SIFContext
from py2viper_translation.sif.lib.program_nodes import SIFPythonMethod
from py2viper_translation.translators.pure import PureTranslator, Wrapper, \
    AssignWrapper, ReturnWrapper
from py2viper_translation.lib.typedefs import Expr
from typing import List


class TLAssignWrapper(AssignWrapper):
    """
    Custom wrapper for an assignment to timeLevel which does not need to be
    duplicated.
    """
    pass


class SIFPureTranslator(PureTranslator):
    """
    SIF version of the PureTranslator.
    """
    def translate_pure_If(self, conds: List, node: ast.If,
                          ctx: SIFContext):
        """
        Translates an if-block to a list of Return- and AssignWrappers which
        contain the condition(s) introduced by the if-block.
        Injects a TLAssignWrapper before the if-block.
        """
        tl_var = ctx.current_function.create_variable('tl',
            ctx.program.classes[BOOL_TYPE], self.translator)
        tl_let = TLAssignWrapper(tl_var.name, conds, node.test, node)
        return [tl_let] + super().translate_pure_If(conds, node, ctx)

    def _translate_wrapper(self, wrapper: Wrapper, previous: Expr,
                           function: SIFPythonMethod, ctx: SIFContext) -> Expr:

        if isinstance(wrapper, ReturnWrapper):
            return self._translate_return_wrapper(wrapper, previous,
                                                  function, ctx)
        elif isinstance(wrapper, TLAssignWrapper):
            return self._translate_tl_assign_wrapper(wrapper, previous,
                                                     function, ctx)
        elif isinstance(wrapper, AssignWrapper):
            # Since wrappers are translated in reverse order, we first translate
            # in the prime context.
            aliases = {k: v.var_prime for (k, v) in wrapper.names.items ()}
            aliases.update({k: v.var_prime for (k, v) in function.args.items()})
            ctx.set_prime_ctx(aliases=aliases, backup=True)
            saved_var = wrapper.var
            wrapper.var = wrapper.var.var_prime
            previous = self._translate_assign_wrapper(wrapper, previous,
                                                      function, ctx)
            ctx.set_normal_ctx(restore=True)
            wrapper.var = saved_var
            previous = self._translate_assign_wrapper(wrapper, previous,
                                                      function, ctx)
            return previous
        else:
            raise UnsupportedException(wrapper)

    def _translate_return_wrapper(self, wrapper: Wrapper, previous: Expr,
                                  function: SIFPythonMethod,
                                  ctx: SIFContext) -> Expr:
        info = self.no_info(ctx)
        position = self.to_position(wrapper.node, ctx)
        # Translate expression twice (once in the prime ctx).
        val = self._translate_wrapper_expr(wrapper, ctx)
        aliases = {k: v.var_prime for (k, v) in wrapper.names.items()}
        aliases.update({k: v.var_prime for (k, v) in function.args.items()})
        ctx.set_prime_ctx(aliases=aliases, backup=True)
        val_p = self._translate_wrapper_expr(wrapper, ctx)
        ctx.set_normal_ctx(restore=True)
        # Create tuple as return value.
        tuple_cls = ctx.program.classes[TUPLE_TYPE]
        args = [val, val_p, self._get_tl_var(function, ctx).ref]
        arg_types = [function.type, function.type,
                     ctx.program.classes[BOOL_TYPE]]
        tuple_ = self.get_function_call(tuple_cls, '__create3__', args,
                                        arg_types, None, ctx)
        if wrapper.cond:
            if not previous:
                raise InvalidProgramException(function.node,
                                              'function.return.missing')
            cond = self._translate_condition(wrapper.cond,
                                             wrapper.names, ctx)
            return self.viper.CondExp(cond, tuple_, previous, position, info)
        else:
            if previous:
                raise InvalidProgramException(function.node,
                                              'function.dead.code')
            return tuple_

    def _translate_tl_assign_wrapper(self, wrapper: Wrapper, previous: Expr,
                                     function: SIFPythonMethod,
                                     ctx: SIFContext) -> Expr:
        """
        Translates a TLAssignWrapper to 'tl = tl || cond != cond'.
        """
        info = self.no_info(ctx)
        position = self.to_position(wrapper.node, ctx)
        cond = self._translate_wrapper_expr(wrapper, ctx)
        aliases = {k: v.var_prime for (k, v) in wrapper.names.items()}
        aliases.update({k: v.var_prime for (k, v) in function.args.items()})
        ctx.set_prime_ctx(aliases=aliases, backup=True)
        cond_p = self._translate_wrapper_expr(wrapper, ctx)
        ctx.set_normal_ctx(restore=True)
        tl_var = self._get_tl_var(function, ctx)
        ne = self.viper.NeCmp(cond, cond_p, position, info)
        rhs = self.viper.Or(tl_var.ref, ne, position, info)

        if wrapper.cond:
            conds = self._translate_condition(wrapper.cond,
                                              wrapper.names, ctx)
            new_val = self.viper.CondExp(conds, rhs, tl_var.ref, position,
                                         info)
            return self.viper.Let(wrapper.var.decl, new_val,
                                  previous, position, info)
        else:
            return self.viper.Let(wrapper.var.decl, rhs,
                                  previous, position, info)


    def _get_tl_var(self, function: SIFPythonMethod,
                    ctx: SIFContext) -> PythonVar:
        if function.tl_var.sil_name in ctx.var_aliases:
            return ctx.var_aliases[function.tl_var.name]
        else:
            return function.tl_var
