from py2viper_translation.lib.program_nodes import (
    PythonIOOperation,
    PythonVar,
    )
from py2viper_translation.translators.abstract import Context
from py2viper_translation.translators.common import CommonTranslator
from typing import Tuple, List

if False:         # Just to make mypy happy.
    import viper  # noqa


class IOOperationTranslator(CommonTranslator):

    def translate_io_operation(
            self,
            operation: PythonIOOperation,
            ctx: Context,
            ) -> Tuple[
                'viper.silver.ast.Predicate',
                List['viper.silver.ast.Function'],
                List['viper.silver.ast.Method'],
                ]:
        """ Translates IO operation to Silver.
        """
        args = [
            arg.decl
            for arg in operation.get_arguments()
            ]
        position = self.to_position(operation.node, ctx)
        info = self.no_info(ctx)

        predicate = self.viper.Predicate(operation.sil_name, args, None,
                                         position, info)

        getters = []
        for result in operation.get_results():
            name = self._construct_getter_name(operation, result)
            typ = self.translate_type(result.type, ctx)
            getter = self.viper.Function(name, args, typ, [], [], None,
                                         position, info)
            getters.append(getter)

        return (
            predicate,
            getters,
            []
            )

    def _construct_getter_name(self, operation: PythonIOOperation,
                               result: PythonVar) -> str:
        return 'get__{0}__{1}'.format(
            operation.sil_name,
            result.sil_name,
            )
