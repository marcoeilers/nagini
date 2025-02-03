"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Utility functions."""


from typing import List

from nagini_translation.lib.context import Context
from nagini_translation.lib.program_nodes import PythonMethod
from nagini_translation.lib.typedefs import (
    Info,
    Position,
    Stmt,
)


def find_method_by_sil_name(ctx: Context, sil_name: str) -> PythonMethod:
    """Find Python method from the global module based on its Silver name."""
    module = ctx.module.global_module
    methods = module.methods
    for method in methods.values():
        if method.sil_name == sil_name:
            return method
    classes = module.classes
    for cls in classes.values():
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
