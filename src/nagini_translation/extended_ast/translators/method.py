"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

from nagini_translation.lib.typedefs import Stmt
from nagini_translation.lib.program_nodes import PythonMethod
from nagini_translation.translators.abstract import Context
from nagini_translation.translators.method import MethodTranslator

from typing import List

class ExtendedASTMethodTranslator(MethodTranslator):
    """
    Extended AST version of method translator.
    """

    def _method_body_postamble(self, method: PythonMethod, ctx: Context) -> List[Stmt]:
        """
        With the extended AST we don't need the goto statment or the catch blocks.
        """
        return []

    def _create_method_epilog(self, method: PythonMethod, ctx: Context) -> List[Stmt]:
        """
        With the extended AST we don't need a label at the end of the method.
        """
        return []
