from typing import List, Tuple


Expr = 'silver.ast.Exp'

Stmt = 'silver.ast.Stmt'

StmtsAndExpr = Tuple[List[Stmt], Expr]

VarDecl = 'silver.ast.LocalVarDecl'

Domain = 'silver.ast.Domain'

DomainFuncApp = 'silver.ast.DomainFuncApp'

Predicate = 'silver.ast.Predicate'

Program = 'silver.ast.Program'

Field = 'silver.ast.Field'

Function = 'silver.ast.Function'

Method = 'silver.ast.Method'

TypeVar = 'silver.ast.TypeVar'

Type = 'silver.ast.Type'

Position = 'silver.ast.Position'

Info = 'silver.ast.Info'

Node = 'silver.ast.Node'
