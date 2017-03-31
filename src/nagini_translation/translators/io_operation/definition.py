"""Translation of IO operation definition."""


from typing import List, Tuple

from nagini_translation.lib.constants import PRIMITIVES
from nagini_translation.lib.context import Context
from nagini_translation.lib.program_nodes import (
    PythonIOOperation,
    PythonVar,
)
from nagini_translation.lib.typedefs import (
    Function,
    Info,
    Method,
    Position,
    Predicate,
    VarDecl,
)
from nagini_translation.translators.io_operation.common import (
    IOOperationCommonTranslator,
)
from nagini_translation.translators.io_operation.termination_check import (
    TerminationCheckGenerator,
)
from nagini_translation.translators.io_operation.utils import (
    construct_getter_name,
)


class IOOperationDefinitionTranslator(IOOperationCommonTranslator):
    """Class responsible for translating IO operation definitions."""

    def translate_io_operation(
            self, operation: PythonIOOperation,
            ctx: Context) -> Tuple[Predicate, List[Function], List[Method]]:
        """Translate IO operation to Silver.

        This means:

        1.  Create a predicate representing IO operation.
        2.  Create body-less functions for all IO operation results.
        3.  Create a method for IO operation termination check.

        .. todo:: Vytautas

            Change from ``List`` of methods to single method, if it
            turns out that we need only one method.
        """
        args = [
            arg.decl
            for arg in operation.get_parameters()
        ]
        position = self.to_position(operation.node, ctx)
        info = self.no_info(ctx)

        predicate = self.viper.Predicate(operation.sil_name, args, None,
                                         position, info)

        getters = [
            self._construct_getter(
                operation, result, args, position, info, ctx)
            for result in operation.get_results()]

        if not operation.is_basic():
            self._translate_defining_getters(operation, ctx)

        method = self._create_termination_check(operation, ctx)
        checks = [method]

        return (
            predicate,
            getters,
            checks,
        )

    def _construct_getter(
            self, operation: PythonIOOperation, operation_result: PythonVar,
            args: List[VarDecl], position: Position,
            info: Info, ctx: Context) -> Function:
        name = construct_getter_name(operation, operation_result)
        typ = self.translate_type(operation_result.type, ctx)
        if operation_result.type.name not in PRIMITIVES:
            getter_result = self.viper.Result(typ, position, info)
            result_type_expr = self.type_check(
                getter_result, operation_result.type, position, ctx)
            posts = [result_type_expr]
        else:
            posts = []
        getter = self.viper.Function(
            name, args, typ, [], posts, None, position, info)
        return getter

    def _translate_defining_getters(
            self, main_operation: PythonIOOperation,
            ctx: Context) -> None:
        """Translate defining getter instances of existential variables."""
        assert not main_operation.is_basic()
        assert ctx.current_function is None
        ctx.current_function = main_operation

        existentials = main_operation.get_io_existentials()
        existentials.sort(key=lambda var: var.defining_order)

        for existential in existentials:
            node, result = existential.get_defining_info()
            getter = self.create_result_getter(node, result, ctx)
            existential.set_existential_ref(getter)

        ctx.current_function = None

    def _create_termination_check(
            self, operation: PythonIOOperation,
            ctx: Context) -> Method:
        """Create a termination check."""
        assert not ctx.current_function
        ctx.current_function = operation

        name = ctx.module.get_fresh_name(
            operation.sil_name + '__termination_check')
        parameters = [
            parameter.decl
            for parameter in operation.get_parameters()
        ]

        statement, termination_condition = self.translate_expr(
            operation.get_terminates(), ctx, target_type=self.viper.Bool,
            expression=True)
        assert not statement
        statement, termination_measure = self.translate_expr(
            operation.get_termination_measure(), ctx,
            target_type=self.viper.Int, expression=True)
        assert not statement

        generator = TerminationCheckGenerator(
            self, ctx, termination_condition, termination_measure,
            operation.get_termination_measure())
        if operation.is_basic():
            checks = generator.create_checks()
        else:
            checks = generator.create_checks(operation.get_body())

        info = self.no_info(ctx)
        position = self.to_position(operation.get_termination_measure(), ctx)

        body = self.translate_block(checks, position, info)
        pres = self._create_typeof_pres(operation.get_parameters(), ctx)
        ctx.current_function = None
        result = self.viper.Method(
            name=name, args=parameters, returns=[], pres=pres, posts=[],
            locals=[], body=body, position=self.no_position(ctx), info=info)

        return result

    def _create_typeof_pres(self, args,
                            ctx: Context):
        """
        Creates 'typeof' preconditions for function arguments.
        """
        pres = []
        for arg in args:
            if not arg.type.name in PRIMITIVES:
                type_check = self.get_parameter_typeof(arg, ctx)
                pres.append(type_check)
        return pres

    def get_parameter_typeof(self, param,
                             ctx: Context):
        """
        Creates an expression checking if the given parameter has its type,
        to be assumed in preconditions and/or postconditions. If possible,
        the expression is wrapped in an InhaleExhaleExpression s.t. it is
        just assumed, not checked. Generally this seems to be possible with
        types, but not with type arg numbers, because the latter encodes length
        for tuples.
        """
        no_pos = self.no_position(ctx)
        result = self.var_type_check(param.sil_name, param.type, no_pos, ctx)
        return result
