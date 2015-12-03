# pylint: disable=invalid-name
def getobject(package, name):
    return getattr(getattr(package, name + '$'), 'MODULE$')


class ViperAST:
    """
    Provides convenient access to the classes which constitute the Viper AST.
    All constructors convert Python lists to Scala sequences, Python ints
    to Scala BigInts, and wrap Scala Option types where necessary.
    """
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

    def empty_seq(self):
        return self.scala.collection.mutable.ListBuffer()

    def singleton_seq(self, element):
        result = self.scala.collection.mutable.ArraySeq(1)
        result.update(0, element)
        return result

    def append(self, list, toappend):
        if not toappend is None:
            lsttoappend = self.singleton_seq(toappend)
            list.append(lsttoappend)

    def to_seq(self, list):
        result = self.scala.collection.mutable.ArraySeq(len(list))
        for index in range(0, len(list)):
            result.update(index, list[index])
        return result

    def to_big_int(self, num):
        return self.scala.math.BigInt(self.java.math.BigInteger.valueOf(num))

    def Program(self, domains, fields, functions, predicates, methods, position,
                info):
        return self.ast.Program(self.to_seq(domains), self.to_seq(fields),
                                self.to_seq(functions), self.to_seq(predicates),
                                self.to_seq(methods), position, info)

    def Function(self, name, args, type, pres, posts, body, position, info):
        return self.ast.Function(name, self.to_seq(args), type, self.to_seq(pres),
                                 self.to_seq(posts),
                                 self.scala.Some(body), position, info)

    def Method(self, name, args, returns, pres, posts, locals, body, position,
               info):
        return self.ast.Method(name, self.to_seq(args), self.to_seq(returns),
                               self.to_seq(pres), self.to_seq(posts),
                               self.to_seq(locals), body, position, info)

    def Label(self, name, position, info):
        return self.ast.Label(name, position, info)

    def Goto(self, name, position, info):
        return self.ast.Goto(name, position, info)

    def Seqn(self, body, position, info):
        return self.ast.Seqn(self.to_seq(body), position, info)

    def LocalVarAssign(self, lhs, rhs, position, info):
        return self.ast.LocalVarAssign(lhs, rhs, position, info)

    def EqCmp(self, left, right, position, info):
        return self.ast.EqCmp(left, right, position, info)

    def NeCmp(self, left, right, position, info):
        return self.ast.NeCmp(left, right, position, info)

    def GtCmp(self, left, right, position, info):
        return self.ast.GtCmp(left, right, position, info)

    def GeCmp(self, left, right, position, info):
        return self.ast.GeCmp(left, right, position, info)

    def LtCmp(self, left, right, position, info):
        return self.ast.LtCmp(left, right, position, info)

    def LeCmp(self, left, right, position, info):
        return self.ast.LeCmp(left, right, position, info)

    def IntLit(self, num, position, info):
        return self.ast.IntLit(self.to_big_int(num), position, info)

    def FuncApp(self, name, args, position, info, type, formalargs):
        return self.ast.FuncApp(name, self.to_seq(args), position, info, type,
                                self.to_seq(formalargs))

    def LocalVarDecl(self, name, type, position, info):
        return self.ast.LocalVarDecl(name, type, position, info)

    def LocalVar(self, name, type, position, info):
        return self.ast.LocalVar(name, type, position, info)

    def Result(self, type, position, info):
        return self.ast.Result(type, position, info)

    def Add(self, left, right, position, info):
        return self.ast.Add(left, right, position, info)

    def Sub(self, left, right, position, info):
        return self.ast.Sub(left, right, position, info)

    def Mul(self, left, right, position, info):
        return self.ast.Mul(left, right, position, info)

    def Div(self, left, right, position, info):
        return self.ast.Div(left, right, position, info)

    def Mod(self, left, right, position, info):
        return self.ast.Mod(left, right, position, info)

    def And(self, left, right, position, info):
        return self.ast.And(left, right, position, info)

    def Or(self, left, right, position, info):
        return self.ast.Or(left, right, position, info)

    def If(self, cond, thn, els, position, info):
        return self.ast.If(cond, thn, els, position, info)

    def TrueLit(self, position, info):
        return self.ast.TrueLit(position, info)

    def FalseLit(self, position, info):
        return self.ast.FalseLit(position, info)

    def While(self, cond, invariants, locals, body, position, info):
        return self.ast.While(cond, self.to_seq(invariants), self.to_seq(locals),
                              body, position, info)

    def to_position(self, expr):
        path = self.java.nio.file.Paths.get(str(self.sourcefile), [])
        start = self.ast.LineColumnPosition(expr.lineno, expr.col_offset)
        end = self.none
        return self.ast.SourcePosition(path, start, end)
