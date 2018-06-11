"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

from typing import List, Tuple

from nagini_translation.lib.typedefs import Expr, Info, Position, Seqn, Var
from nagini_translation.lib.viper_ast import ViperAST


class ViperASTExtended(ViperAST):
    """
    Extends the Viper AST, to provide access to extension nodes.
    """

    def __init__(self, jvm, java, scala, viper, sourcefile):
        super().__init__(jvm, java, scala, viper, sourcefile)
        self.ast_extensions = viper.silver.sif

    def Return(self, expr: Expr, res_var: Var, position: Position, info: Info):
        return_node = self.ast_extensions.SIFReturnStmt(expr, res_var)
        return self.ast.ExtensionStmt(return_node, position, info, self.NoTrafos)

    def Break(self, position: Position, info: Info):
        break_node = self.ast_extensions.SIFBreakStmt()
        return self.ast.ExtensionStmt(break_node, position, info, self.NoTrafos)

    def Continue(self, position: Position, info: Info):
        cont_node = self.ast_extensions.SIFContinueStmt()
        return self.ast.ExtensionStmt(cont_node, position, info, self.NoTrafos)

    def Skip(self):
        return self.Seqn([], self.NoPosition, self.NoInfo)

    def Goto(self, name: str, position: Position, info: Info):
        """ Don't add the gotos, not needed in extended AST. """
        return self.Skip()

    def Label(self, name: str, position: Position, info: Info):
        """ Don't add the labels, not needed in extended AST. """
        return self.Skip()

    def Raise(self, create_stmts: Seqn, assignment: Var, position: Position, info: Info):
        raise_node = self.ast_extensions.SIFRaiseStmt(create_stmts, assignment)
        return self.ast.ExtensionStmt(raise_node, position, info, self.NoTrafos)

    def SIFExceptionHandler(self, exception: Expr, handler: Seqn):
        return self.ast_extensions.SIFExceptionHandler(exception, handler)

    def Try(self, body: Seqn, catch_blocks: List['silver.sif.SIFExceptionHandler'],
            else_block: Seqn, finally_block: Seqn, position: Position, info: Info):
        catch_blocks_seq = self.to_seq(catch_blocks)
        try_node = self.ast_extensions.SIFTryCatchStmt(body, catch_blocks_seq,
                                                       else_block, finally_block)
        return self.ast.ExtensionStmt(try_node, position, info, self.NoTrafos)

    def Low(self, expr: Expr, position: Position, info: Info):
        return self.ast.Low(expr, position, info, self.NoTrafos)

    def LowEvent(self, position: Position, info: Info):
        return self.ast.LowEvent(position, info, self.NoTrafos)
