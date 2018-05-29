"""
TODO
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
