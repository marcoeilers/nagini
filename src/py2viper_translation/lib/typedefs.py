from typing import List, Tuple


Expr = 'silver.ast.Exp'

Stmt = 'silver.ast.Stmt'

StmtsAndExpr = Tuple[List[Stmt], Expr]

VarDecl = 'silver.ast.LocalVarDecl'

DomainFuncApp = 'silver.ast.DomainFuncApp'
