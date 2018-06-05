"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

from nagini_translation.lib.viper_ast import ViperAST

class ViperASTExtended(ViperAST):
    """
    Extends the Viper AST, to provide access to extension nodes.
    """

    def __init__(self, jvm, java, scala, viper, sourcefile):
        super().__init__(jvm, java, scala, viper, sourcefile)
        self.ast_extensions = viper.silver.sif

    def Return(self, expr, res_var, position, info):
        return_node = self.ast_extensions.SIFReturnStmt(expr, res_var)
        return self.ast.ExtensionStmt(return_node, position, info, self.NoTrafos)

    def Break(self, position, info):
        break_node = self.ast_extensions.SIFBreakStmt()
        return self.ast.ExtensionStmt(break_node, position, info, self.NoTrafos)

    def Continue(self, position, info):
        cont_node = self.ast_extensions.SIFContinueStmt()
        return self.ast.ExtensionStmt(cont_node, position, info, self.NoTrafos)

    def Skip(self):
        return self.Seqn([], self.NoPosition, self.NoInfo)

    def Goto(self, name, position, info):
        """ Don't add the gotos, not needed in extended AST. """
        return self.Skip()

    def Label(self, name, position, info):
        """ Don't add the labels, not needed in extended AST. """
        return self.Skip()

    def Low(self, expr, position, info):
        return self.ast.Low(expr, position, info, self.NoTrafos)

    def LowEvent(self, position, info):
        return self.ast.LowEvent(position, info, self.NoTrafos)
