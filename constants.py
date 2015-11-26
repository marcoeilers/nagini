__author__ = 'marco'

def getobject(package, name):
    return getattr(getattr(package, name+'$'), 'MODULE$')

class ViperAST:
    def __init__(self, java, scala, viper, sourcefile):
        ast = viper.silver.ast
        self.ast = ast
        self.java = java
        self.scala = scala
        def getconst(name):
            return getobject(ast, name)
        self.addop = getconst("AddOp")
        self.andop = getconst("AndOp")
        self.divop = getconst("DivOp")
        self.fracop = getconst("FracOp")
        self.geop = getconst("GeOp")
        self.gtop = getconst("GtOp")
        self.impliesop = getconst("ImpliesOp")
        self.intpermmulop = getconst("IntPermMulOp")
        self.leop = getconst("LeOp")
        self.ltop = getconst("LtOp")
        self.modop = getconst("ModOp")
        self.mulop = getconst("MulOp")
        self.negop = getconst("NegOp")
        self.notop = getconst("NotOp")
        self.orop = getconst("OrOp")
        self.permaddop = getconst("PermAddOp")
        self.permdivop = getconst("PermDivOp")
        self.subop = getconst("SubOp")
        self.noposition = getconst("NoPosition")
        self.noinfo = getconst("NoInfo")
        self.typeint = getconst("Int")
        self.typebool = getconst("Bool")
        self.sourcefile = sourcefile
        self.none = getobject(scala, "None")


    def emptyseq(self):
        return self.scala.collection.mutable.ListBuffer()

    def singletonseq(self, element):
        result = self.scala.collection.mutable.ArraySeq(1)
        result.update(0, element)
        return result

    def toBigInt(self, num):
        return self.scala.math.BigInt(self.java.math.BigInteger.valueOf(num))

    def program(self, domains, fields, functions, predicates, methods, position, info):
        return self.ast.Program(domains, fields, functions, predicates, methods, position, info)

    def function(self, name, args, type, pres, posts, body, position, info):
        return self.ast.Function(name, args, type, pres, posts, self.scala.Some(body), position, info)

    def eqcmp(self, left, right, position, info):
        return self.ast.EqCmp(left, right, position, info)

    def intlit(self, num, position, info):
        return self.ast.IntLit(self.toBigInt(num), position, info)

    def funcapp(self, name, args, position, info, type, formalargs):
        return self.ast.FuncApp(name, args, position, info, type, formalargs)

    def localvardecl(self, name, type, position, info):
        return self.ast.LocalVarDecl(name, type, position, info)

    def localvar(self, name, type, position, info):
        return self.ast.LocalVar(name, type, position, info)

    def result(self, type, position, info):
        return self.ast.Result(type, position, info)

    def toposition(self, expr):
        path = self.java.nio.file.Paths.get(str(self.sourcefile), [])
        start = self.ast.LineColumnPosition(expr.lineno, expr.col_offset)
        end = self.none
        return self.ast.SourcePosition(path, start, end)

