"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

from typing import List, Optional

from nagini_translation.lib.typedefs import (
    Expr, Info, Position, Seqn, Stmt, Var, VarAssign, While
)
from nagini_translation.lib.viper_ast import ViperAST
from nagini_translation.sif.lib.util import (
    in_postcondition_of_dyn_bound_call, in_override_check
)


class ViperASTExtended(ViperAST):
    """
    Extends the Viper AST, to provide access to extension nodes.
    """

    def __init__(self, jvm, java, scala, viper, sourcefile):
        super().__init__(jvm, java, scala, viper, sourcefile)
        self.ast_extensions = viper.silver.sif
        self.all_low_methods = set()
        self.preserves_low_methods = set()
        self.equality_comp_functions = set()
        self.ctx = None
        self.type_factory = None

    def is_extension_available(self) -> bool:
        """
        Checks if the extended AST is available, i.e., the SIF AST extension is on the
        Java classpath.
        """
        return self.jvm.is_known_class(self.ast_extensions.SIFReturnStmt)

    def Return(self, expr: Optional[Expr], res_var: Optional[Var], position: Position,
               info: Info):
        expr_opt = self.scala.Some(expr) if expr is not None else self.none
        res_var_opt = self.scala.Some(res_var) if res_var is not None else self.none
        return self.ast_extensions.SIFReturnStmt(expr_opt, res_var_opt,
                                                 position, info, self.NoTrafos)

    def Break(self, position: Position, info: Info):
        return self.ast_extensions.SIFBreakStmt(position, info, self.NoTrafos)

    def Continue(self, position: Position, info: Info):
        return self.ast_extensions.SIFContinueStmt(position, info, self.NoTrafos)

    def Skip(self) -> Seqn:
        return self.Seqn([], self.NoPosition, self.NoInfo)

    def Goto(self, name: str, position: Position, info: Info) -> Stmt:
        """ Don't add the gotos, not needed in extended AST. """
        return self.Skip()

    def Label(self, name: str, position: Position, info: Info) -> Stmt:
        """ Don't add the labels, not needed in extended AST. """
        return self.Skip()

    def Raise(self, assignment: Optional[VarAssign], position: Position, info: Info):
        ass_opt = self.scala.Some(assignment) if assignment is not None else self.none
        return self.ast_extensions.SIFRaiseStmt(ass_opt, position, info, self.NoTrafos)

    def SIFExceptionHandler(self, err_var: Var, exception: Expr, handler: Seqn):
        return self.ast_extensions.SIFExceptionHandler(
            err_var, exception, handler, self.NoPosition, self.NoInfo, self.NoTrafos)

    def SIFWhileElse(self, loop: While, els: Stmt):
        return self.ast_extensions.SIFWhileElse(
            loop, els, self.NoPosition, self.NoInfo, self.NoTrafos)

    def Try(self, body: Seqn, catch_blocks: List['silver.sif.SIFExceptionHandler'],
            else_block: Optional[Seqn], finally_block: Optional[Seqn],
            position: Position, info: Info):
        catch_blocks_seq = self.to_seq(catch_blocks)
        else_opt = self.scala.Some(else_block) if else_block is not None else self.none
        fin_opt = (self.scala.Some(finally_block)
                   if finally_block is not None else self.none)
        return self.ast_extensions.SIFTryCatchStmt(
            body, catch_blocks_seq, else_opt, fin_opt, position, info, self.NoTrafos)

    def Low(self, expr: Expr, comp: Optional[str], position: Position, info: Info):
        if comp:
            self.used_names.add(comp)
            comp_opt = self.scala.Some(comp)
        else:
            comp_opt = self.none
        return self.ast_extensions.SIFLowExp(
            expr, comp_opt, self.to_map({}), position, info, self.NoTrafos)

    def LowEvent(self, position: Position, info: Info):
        return self.ast_extensions.SIFLowEventExp(position, info, self.NoTrafos)

    def LowExit(self, position: Position, info: Info):
        return self.ast_extensions.SIFLowExitExp(position, info, self.NoTrafos)

    def Declassify(self, expr: Expr, position: Position, info: Info):
        return self.ast_extensions.SIFDeclassifyStmt(expr, position, info, self.NoTrafos)

    def InlinedCall(self, stmts: Seqn, position: Position, info: Info):
        return self.ast_extensions.SIFInlinedCallStmt(stmts, position, info, self.NoTrafos)

    def AssertNoException(self, position: Position, info: Info):
        return self.ast_extensions.SIFAssertNoException(position, info, self.NoTrafos)

    def TerminatesSif(self, cond: Expr, position: Position, info: Info):
        return self.ast_extensions.SIFTerminatesExp(cond, position, info, self.NoTrafos)

    def PredicateAccessPredicate(self, loc, perm, position, info):
        if self.ctx and self.type_factory:
            dyn_check = in_postcondition_of_dyn_bound_call(self.type_factory, self.ctx)
            if dyn_check:
                info = self.ConsInfo(
                    self.SIFDynCheckInfo([], dyn_check, in_override_check(self.ctx)),
                    info)
        return super().PredicateAccessPredicate(loc, perm, position, info)

    def SIFInfo(self, comments: List[str],
                continue_unaware: bool = False,
                obligation_var: bool = False) -> 'silver.sif.SIFInfo':
        return self.ast_extensions.SIFInfo(
            self.to_seq(comments), continue_unaware, obligation_var)

    def SIFDynCheckInfo(self, comments: List[str],
                        dyn_check: Expr,
                        dyn_check_only: bool = False) -> 'silver.sif.SIFDynCheckInfo':
        return self.ast_extensions.SIFDynCheckInfo(self.to_seq(comments), dyn_check,
                                                   dyn_check_only)
