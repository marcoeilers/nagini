"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

from nagini_translation.lib.typedefs import Stmt
from nagini_translation.translators.abstract import Context
from nagini_translation.translators.program import ProgramTranslator

from typing import List

class SIFProgramTranslator(ProgramTranslator):
    """
    Extended AST version of program translator.
    """

    def _create_inherit_check_postamble(self, stmts: List[Stmt],
                                        end_lbl: 'silver.ast.Label',
                                        ctx: Context) -> None:
        pass
