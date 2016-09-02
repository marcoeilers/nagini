"""Utility functions."""


from typing import List

from py2viper_translation.lib.context import Context
from py2viper_translation.lib.program_nodes import PythonMethod
from py2viper_translation.lib.typedefs import (
    Info,
    Position,
    Stmt,
)


def find_method_by_sil_name(ctx: Context, sil_name: str) -> PythonMethod:
    """Find Python method based on its Silver name."""
    for method in ctx.program.methods.values():
        if method.sil_name == sil_name:
            return method
    for cls in ctx.program.classes.values():
        for method in cls.methods.values():
            if method.sil_name == sil_name:
                return method
    return None


def bound_obligations(
        instances: List['ObligationInstance'],
        translator: 'AbstractTranslator', ctx: Context,
        position: Position, info: Info) -> List[Stmt]:
    """Construct statements for bounding fresh obligations."""
    statements = []
    for instance in instances:
        if not instance.obligation_instance.is_fresh():
            continue
        statement = instance.obligation_instance.get_obligation_bound(ctx)
        statements.append(statement)
    translated_statements = [
        statement.translate(translator, ctx, position, info)
        for statement in statements]
    return translated_statements
