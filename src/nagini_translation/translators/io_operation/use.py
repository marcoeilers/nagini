"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Translation of IO operation use."""


import ast

from typing import cast, List

from nagini_translation.lib.constants import CALLABLE_TYPE
from nagini_translation.lib.context import Context
from nagini_translation.lib.program_nodes import (
    PythonIOExistentialVar,
    PythonMethod,
    PythonIOOperation,
    TypeVar,
)
from nagini_translation.lib.typedefs import (
    Expr,
    Stmt,
    StmtsAndExpr,
)
from nagini_translation.lib.util import (
    get_func_name,
    InvalidProgramException,
    UnsupportedException,
)
from nagini_translation.translators.io_operation.common import (
    IOOperationCommonTranslator,
)
from nagini_translation.translators.io_operation.opener import Opener
from nagini_translation.translators.io_operation.result_translator import (
    ResultTranslator,
)
from nagini_translation.translators.io_operation.utils import (
    get_variable,
    is_top_level_assertion,
    raise_invalid_operation_use,
    raise_invalid_existential_var,
    raise_invalid_get_ghost_output,
)


class IOOperationUseTranslator(IOOperationCommonTranslator):
    """Class responsible for translating IO operation use."""

    def translate_io_operation_call(self, node: ast.Call,
                                    ctx: Context) -> StmtsAndExpr:
        """Translate a call to an IO operation.

        That is:

        1.  Emit a predicate access corresponding to the operation.
        2.  Either define getter invocations corresponding to the
            operation results, or emit equalities between each result
            and already defined getter invocation.
        """
        assert ctx.actual_function

        operation = self.get_target(node, ctx)
        parameters = operation.get_parameters()
        args = self.translate_args(node.args[:len(parameters)], parameters, ctx)
        perm = self._construct_full_perm(node, ctx)

        # Translate predicate.
        predicate = self.create_predicate_access(
            operation.sil_name, args, perm, node, ctx)

        # Translate results.
        equations = self._translate_results(operation, node, ctx)

        # And everything.
        expr = predicate
        for equation in equations:
            expr = self.viper.And(expr, equation,
                                  self.to_position(node, ctx),
                                  self.no_info(ctx))
        return [], expr

    def is_io_existential_defining_equality(self, node: ast.expr,
                                            ctx: Context) -> bool:
        """Check if ``node`` defines IO existential variable.

        That is, node is equality of form:
        ``existential_variable == something``.
        """
        if (is_top_level_assertion(node) and
                isinstance(node, ast.Compare)):
            if (len(node.ops) == 1 and
                    len(node.comparators) == 1 and
                    isinstance(node.left, ast.Name) and
                    isinstance(node.ops[0], ast.Eq)):
                var = get_variable(node.left.id, ctx)
                return (
                    isinstance(var, PythonIOExistentialVar) and
                    not var.is_defined())
        return False

    def define_io_existential(self, node: ast.Compare, ctx: Context) -> None:
        """From defining equality defines IO existential variable."""
        assert self.is_io_existential_defining_equality(node, ctx)

        # TODO: The result of this call must not only be an expression,
        # but a pure expression.
        right_stmt, right = self.translate_expr(
            node.comparators[0], ctx)
        assert not right_stmt   # Should be handled by expression=True.

        name_node = cast(ast.Name, node.left)
        var = get_variable(name_node.id, ctx)

        expression_type = self.get_type(node.comparators[0], ctx)
        if var.type != expression_type:
            raise_invalid_existential_var(
                'defining_expression_type_mismatch', node)

        var.set_ref(right, self.viper.Old(right, right.pos(), right.info()))

    def translate_get_ghost_output(
            self, node: ast.Assign, ctx: Context) -> List[Stmt]:
        """Translate ``GetGhostOutput``."""
        if len(node.targets) != 1:
            raise_invalid_get_ghost_output('multiple_targets', node)
        if not isinstance(node.targets[0], ast.Name):
            raise_invalid_get_ghost_output('target_not_variable', node)
        target_name = cast(ast.Name, node.targets[0]).id
        target = ctx.actual_function.get_variable(target_name)
        assert target

        operation_call, result_name_node = cast(ast.Call, node.value).args

        if not isinstance(result_name_node, ast.Str):
            raise_invalid_get_ghost_output('result_identifier_not_str', node)
        result_name = cast(ast.Str, result_name_node).s

        if not (isinstance(operation_call, ast.Call) and
                isinstance(operation_call.func, ast.Name)):
            raise_invalid_get_ghost_output('argument_not_io_operation', node)
        operation_call = cast(ast.Call, operation_call)
        operation_name = cast(ast.Name, operation_call.func).id

        if operation_name not in ctx.module.io_operations:
            raise_invalid_get_ghost_output('argument_not_io_operation', node)
        operation = ctx.module.io_operations[operation_name]

        result = None
        for result in operation.get_results():
            if result.name == result_name:
                break
        else:
            raise_invalid_get_ghost_output('invalid_result_identifier', node)
        assert result

        if result.type != target.type:
            raise_invalid_get_ghost_output('type_mismatch', node)

        if len(operation_call.args) != len(operation.get_parameters()):
            raise_invalid_operation_use('result_used_argument', node)
        getter = self.create_result_getter(operation_call, result, ctx)

        position = self.to_position(node, ctx)
        info = self.no_info(ctx)
        set_defined = self.set_var_defined(target, position, info)
        assignment = self.viper.LocalVarAssign(target.ref(), getter,
                                               position, info)

        return [assignment, set_defined]

    def translate_io_contractfunc_call(self, node: ast.Call,
                                       ctx: Context, impure: bool, statement: bool) -> StmtsAndExpr:
        """Translate a call to a IO contract function.

        Currently supported functions:

        +   ``token``
        +   ``ctoken``
        +   ``Open``
        """
        func_name = get_func_name(node)
        if func_name == 'token':
            if not impure:
                raise InvalidProgramException(node, 'invalid.contract.position')
            return self.translate_must_invoke_token(node, ctx)
        elif func_name == 'ctoken':
            if not impure:
                raise InvalidProgramException(node, 'invalid.contract.position')
            return self.translate_must_invoke_ctoken(node, ctx)
        elif func_name == 'Open':
            if not statement:
                raise InvalidProgramException(node, 'invalid.contract.position')
            return self._translate_open(node, ctx)
        elif func_name == 'Eval':
            return self._translate_eval(node, ctx)
        elif func_name == 'eval_io':
            if not impure:
                raise InvalidProgramException(node, 'invalid.contract.position')
            return self._translate_eval_io(node, ctx)
        else:
            raise UnsupportedException(node,
                                       'Unsupported contract function.')

    def _translate_eval_io(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translates a reference to the eval_io IOOperation as usual. Also stores the
        information that given argument function is among the argument functions used with
        eval_io in the program; this information is used to generate additional return
        type postconditions for the result getter of eval_io.
        """
        if not isinstance(node.args[1], ast.Name):
            raise InvalidProgramException(node, 'invalid.eval.function')
        target = self.get_target(node.args[1], ctx)
        if (ctx.current_function.name != 'Eval' and
                (not isinstance(target, PythonMethod) or not target.pure)):
            raise InvalidProgramException(node, 'invalid.eval.function')
        stmt, res = self.translate_io_operation_call(node, ctx)
        func_stmt, func_arg = self.translate_expr(node.args[1], ctx)
        if func_stmt:
            raise InvalidProgramException(node, 'purity.violated')
        eval_io = self.get_target(node, ctx)

        arg_type = self.get_type(node.args[1], ctx)
        if arg_type.name != CALLABLE_TYPE:
            eval_io.func_args.append((func_arg, arg_type))
        return stmt, res

    def _translate_eval(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to the Eval method (which implements the eval_io IOOperation).
        The translation is like for other method calls, except we also inhale that the
        result of the operation is equal to the given function applied to the given
        argument.
        """
        position = self.to_position(node, ctx)
        info = self.no_info(ctx)
        if not isinstance(node.args[1], ast.Name):
            raise InvalidProgramException(node, 'invalid.eval.function')
        target = self.get_target(node.args[1], ctx)
        if not target.pure:
            raise InvalidProgramException(node, 'invalid.eval.function')
        arg_stmt, arg = self.translate_expr(node.args[2], ctx)
        if arg_stmt:
            raise InvalidProgramException(node, 'purity.violated')
        arg_type = self.get_type(node.args[2], ctx)
        func_stmt, func_val = self.translate_normal_call(target, [], [arg], [arg_type],
                                                         node, ctx)
        if func_stmt:
            raise InvalidProgramException(node, 'purity.violated')
        call_stmt, call = self.translate_normal_call_node(node, ctx)
        args = []
        for arg in node.args:
            stmt, arg_val = self.translate_expr(arg, ctx)
            assert not stmt
            args.append(arg_val)

        eval_io = self._get_eval_io_operation(ctx)
        getter = self.create_result_getter(node, eval_io.get_results()[0], ctx, args,
                                           eval_io)
        assume = self.viper.Inhale(self.viper.EqCmp(func_val, getter, position, info),
                                   position, info)
        return call_stmt + [assume], call

    def _get_eval_io_operation(self, ctx: Context) -> PythonIOOperation:
        for module in ctx.module.from_imports:
            if module.type_prefix == 'nagini_contracts.io_builtins':
                io_builtins = module
                break
        else:
            contracts = ctx.module.namespaces['nagini_contracts']
            io_builtins = contracts.namespaces['io_builtins']
        eval_io = io_builtins.io_operations['eval_io']
        return eval_io

    def _translate_open(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """Translate ``Open(io_operation)``."""
        assert ctx.actual_function
        full_perm = self._construct_full_perm(node, ctx)
        opener = Opener(node, ctx, self, full_perm)
        return opener.translate()

    def _translate_results(
            self, operation: PythonIOOperation, node: ast.Call,
            ctx: Context) -> List[Expr]:
        """Translate IO operation results.

        That is: define getters corresponding to operation results or
        emit equalities between each result and getter definition.
        """
        result_translator = ResultTranslator(operation, node, self, ctx)
        return result_translator.translate()

    def _construct_full_perm(self, node: ast.Call,
                             ctx: Context) -> 'viper_ast.FullPerm':
        """Construct silver full perm AST node."""
        return self.viper.FullPerm(self.to_position(node, ctx),
                                   self.no_info(ctx))
