"""Translation of IO operation definition."""


from typing import List, Tuple

from py2viper_translation.lib.context import Context
from py2viper_translation.lib.program_nodes import (
    PythonIOOperation,
)
from py2viper_translation.translators.io_operation.common import (
    IOOperationCommonTranslator,
)
from py2viper_translation.translators.io_operation.termination_check import (
    TerminationCheckGenerator,
)
from py2viper_translation.translators.io_operation.utils import (
    construct_getter_name,
)


class IOOperationDefinitionTranslator(IOOperationCommonTranslator):
    """Class responsible for translating IO operation definitions."""

    def translate_io_operation(
            self, operation: PythonIOOperation,
            ctx: Context) -> Tuple[
                'viper_ast.Predicate',
                List['viper_ast.Function'],
                List['viper_ast.Method']]:
        """Translate IO operation to Silver."""
        args = [
            arg.decl
            for arg in operation.get_parameters()
        ]
        position = self.to_position(operation.node, ctx)
        info = self.no_info(ctx)

        predicate = self.viper.Predicate(operation.sil_name, args, None,
                                         position, info)

        getters = []
        for result in operation.get_results():
            name = construct_getter_name(operation, result)
            typ = self.translate_type(result.type, ctx)
            getter = self.viper.Function(name, args, typ, [], [], None,
                                         position, info)
            getters.append(getter)

        if not operation.is_basic():
            self._translate_defining_getters(operation, ctx)

        method = self._create_termination_check(operation, ctx)
        checks = [method]

        return (
            predicate,
            getters,
            checks,
        )

    def _translate_defining_getters(
            self, main_operation: PythonIOOperation,
            ctx: Context) -> None:
        """Translate defining getters of existential variables."""
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
            ctx: Context) -> 'viper_ast.Method':
        """Create a termination check."""
        assert not ctx.current_function
        ctx.current_function = operation

        name = ctx.program.get_fresh_name(
            operation.sil_name + '__termination_check')
        parameters = [
            parameter.decl
            for parameter in operation.get_parameters()
        ]

        statement, termination_condition = self.translate_expr(
            operation.get_terminates(), ctx, expression=True)
        assert not statement
        statement, termination_measure = self.translate_expr(
            operation.get_termination_measure(), ctx, expression=True)
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

        ctx.current_function = None
        result = self.viper.Method(
            name=name, args=parameters, returns=[], pres=[], posts=[],
            locals=[], body=body, position=self.no_position(ctx), info=info)

        return result
