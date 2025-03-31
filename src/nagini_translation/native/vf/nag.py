import nagini_translation.native.vf.vf as vf
from abc import ABC, abstractmethod
from fractions import Fraction

class NaginiPredicateFact(vf.PredicateFact):
    pass

class NaginiPureFPCall(vf.FPCall):
    pass

#inductive list_forallcond = True | inrange(int a, int b, int c) | lt(int a) | gt(int a) | lte(int a) | gte(int a) | fixp(fixpoint(int, bool) f) | neg(list_forallcond c) | and(list_forallcond c1, list_forallcond c2) | or(list_forallcond c1, list_forallcond c2);
class ListForallCond(vf.Inductive, ABC):
    pass

class ListForallCond_True(ListForallCond):
    def __str__(self):
        return "True"

class ListForallCond_InRange(ListForallCond):
    def __init__(self, a: vf.Expr[vf.Int], b: vf.Expr[vf.Int], c: vf.Expr[vf.Int]):
        self.a = a
        self.b = b
        self.c = c

    def __str__(self):
        return "inrange("+str(self.a)+", "+str(self.b)+", "+str(self.c)+")"
    
class ListForallCond_Lt(ListForallCond):
    def __init__(self, a: vf.Expr[vf.Int]):
        self.a = a

    def __str__(self):
        return "lt("+str(self.a)+")"
    
class ListForallCond_Gt(ListForallCond):
    def __init__(self, a: vf.Expr[vf.Int]):
        self.a = a

    def __str__(self):
        return "gt("+str(self.a)+")"
    
class ListForallCond_Lte(ListForallCond):
    def __init__(self, a: vf.Expr[vf.Int]):
        self.a = a

    def __str__(self):
        return "lte("+str(self.a)+")"

class ListForallCond_Gte(ListForallCond):
    def __init__(self, a: vf.Expr[vf.Int]):
        self.a = a

    def __str__(self):
        return "gte("+str(self.a)+")"
    
class ForallPredFact(vf.PredicateFact):
    def __init__(self, pairlist: vf.NameDefExpr, predname: vf.NameUseExpr, cond, wrapperpair: vf.NameUseExpr, frac=Fraction(1)):
        super().__init__("forall_predfact", pairlist, predname, cond, wrapperpair, vf.Nil, frac=frac)