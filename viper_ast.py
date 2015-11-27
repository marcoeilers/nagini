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
        self.AddOp = getconst("AddOp")
        self.AndOp = getconst("AndOp")
        self.DivOp = getconst("DivOp")
        self.FracOp = getconst("FracOp")
        self.GeOp = getconst("GeOp")
        self.GtOp = getconst("GtOp")
        self.ImpliesOp = getconst("ImpliesOp")
        self.IntPermMulOp = getconst("IntPermMulOp")
        self.LeOp = getconst("LeOp")
        self.LtOp = getconst("LtOp")
        self.ModOp = getconst("ModOp")
        self.MulOp = getconst("MulOp")
        self.NegOp = getconst("NegOp")
        self.NotOp = getconst("NotOp")
        self.OrOp = getconst("OrOp")
        self.PermAddOp = getconst("PermAddOp")
        self.PermDivOp = getconst("PermDivOp")
        self.SubOp = getconst("SubOp")
        self.NoPosition = getconst("NoPosition")
        self.NoInfo = getconst("NoInfo")
        self.Int = getconst("Int")
        self.Bool = getconst("Bool")
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

    def Program(self, domains, fields, functions, predicates, methods, position, info):
        return self.ast.Program(domains, fields, functions, predicates, methods, position, info)

    def Function(self, name, args, type, pres, posts, body, position, info):
        return self.ast.Function(name, args, type, pres, posts, self.scala.Some(body), position, info)

    def EqCmp(self, left, right, position, info):
        return self.ast.EqCmp(left, right, position, info)

    def IntLit(self, num, position, info):
        return self.ast.IntLit(self.toBigInt(num), position, info)

    def FuncApp(self, name, args, position, info, type, formalargs):
        return self.ast.FuncApp(name, args, position, info, type, formalargs)

    def LocalVarDecl(self, name, type, position, info):
        return self.ast.LocalVarDecl(name, type, position, info)

    def LocalVar(self, name, type, position, info):
        return self.ast.LocalVar(name, type, position, info)

    def Result(self, type, position, info):
        return self.ast.Result(type, position, info)

    def toposition(self, expr):
        path = self.java.nio.file.Paths.get(str(self.sourcefile), [])
        start = self.ast.LineColumnPosition(expr.lineno, expr.col_offset)
        end = self.none
        return self.ast.SourcePosition(path, start, end)

