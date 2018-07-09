"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import ast

from nagini_translation.translators.call import CallTranslator
from nagini_translation.translators.abstract import Context

class ExtendedASTCallTranslator(CallTranslator):
    """
    Extended AST version of call translator.
    """

    def get_error_var(self, stmt: ast.AST, ctx: Context) -> 'silver.ast.LocalVarRef':
        return ctx.current_function.error_var.ref()
