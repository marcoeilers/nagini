import types


def getobject(package, name):
    return getattr(getattr(package, name + '$'), 'MODULE$')


class Function0:
    def apply(self):
        pass


LONG_SIZE = 2147483647


class ViperAST:
    """
    Provides convenient access to the classes which constitute the Viper AST.
    All constructors convert Python lists to Scala sequences, Python ints
    to Scala BigInts, and wrap Scala Option types where necessary.
    """

    def __init__(self, jvm, java, scala, viper, sourcefile):
        ast = viper.silver.ast
        self.ast = ast
        self.java = java
        self.scala = scala
        self.jvm = jvm

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
        self.Ref = getconst("Ref")
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
        return result.toList()

    def to_list(self, seq):
        result = []
        iterator = seq.toIterator()
        while iterator.hasNext():
            result.append(iterator.next())
        return result

    def to_map(self, dict):
        result = self.scala.collection.immutable.HashMap()
        for k, v in dict.items():
            result = result.updated(k, v)
        return result

    def to_big_int(self, num):
        # We cannot give integers directly to Scala if they don't
        # fit into a C long int, so we have to split things up.
        negative = num < 0
        if negative:
            num = -num
        cutoff = LONG_SIZE
        cutoff_int = self.java.math.BigInteger.valueOf(cutoff)
        rest = num
        result_int = self.java.math.BigInteger.valueOf(0)
        while rest > 0:
            current_part = rest % cutoff
            current_int = self.java.math.BigInteger.valueOf(current_part)
            result_int = result_int.multiply(cutoff_int)
            result_int = result_int.add(current_int)
            rest = rest // cutoff
        return self.scala.math.BigInt(result_int)

    def Program(self, domains, fields, functions, predicates, methods, position,
                info):
        return self.ast.Program(self.to_seq(domains), self.to_seq(fields),
                                self.to_seq(functions), self.to_seq(predicates),
                                self.to_seq(methods), position, info)

    def Function(self, name, args, type, pres, posts, body, position, info):
        body = self.scala.Some(body) if body is not None else self.none
        return self.ast.Function(name, self.to_seq(args), type,
                                 self.to_seq(pres),
                                 self.to_seq(posts),
                                 body, position, info)

    def Method(self, name, args, returns, pres, posts, locals, body, position,
               info):
        return self.ast.Method(name, self.to_seq(args), self.to_seq(returns),
                               self.to_seq(pres), self.to_seq(posts),
                               self.to_seq(locals), body, position, info)

    def Field(self, name, type, position, info):
        return self.ast.Field(name, type, position, info)

    def Predicate(self, name, args, body, position, info):
        body = self.scala.Some(body) if body is not None else self.none
        return self.ast.Predicate(name, self.to_seq(args),
                                  body, position, info)

    def PredicateAccess(self, args, pred_name, position, info):
        return self.ast.PredicateAccess(self.to_seq(args), pred_name, position,
                                        info)

    def PredicateAccessPredicate(self, loc, perm, position, info):
        return self.ast.PredicateAccessPredicate(loc, perm, position, info)

    def Fold(self, predicate, position, info):
        return self.ast.Fold(predicate, position, info)

    def Unfold(self, predicate, position, info):
        return self.ast.Unfold(predicate, position, info)

    def Unfolding(self, predicate, expr, position, info):
        return self.ast.Unfolding(predicate, expr, position, info)

    def SeqType(self, element_type):
        return self.ast.SeqType(element_type)

    def SetType(self, element_type):
        return self.ast.SetType(element_type)

    def Domain(self, name, functions, axioms, typevars, position, info):
        return self.ast.Domain(name, self.to_seq(functions),
                               self.to_seq(axioms), self.to_seq(typevars),
                               position, info)

    def DomainFunc(self, name, args, type, unique, position, info, domain_name):
        return self.ast.DomainFunc(name, self.to_seq(args), type, unique,
                                   position, info, domain_name)

    def DomainAxiom(self, name, expr, position, info, domain_name):
        return self.ast.DomainAxiom(name, expr, position, info, domain_name)

    def DomainType(self, name, typevarsmap, typevars):
        map = self.to_map(typevarsmap)
        seq = self.to_seq(typevars)
        return self.ast.DomainType(name, map,
                                   seq)

    def DomainFuncApp(self, funcname, args, typevarmap, typepassed, argspassed,
                      position, info, domain_name):
        def typepassedapply(slf):
            return typepassed

        def argspassedapply(slf):
            return self.to_seq(argspassed)

        typepassedfunc = self.to_function0(typepassedapply)
        argspassedfunc = self.to_function0(argspassedapply)
        result = self.ast.DomainFuncApp(funcname, self.to_seq(args),
                                        self.to_map(typevarmap), position, info,
                                        typepassedfunc, argspassedfunc,
                                        domain_name)
        return result

    def TypeVar(self, name):
        return self.ast.TypeVar(name)

    def MethodCall(self, methodname, args, targets, position, info):
        return self.ast.MethodCall(methodname, self.to_seq(args),
                                   self.to_seq(targets), position, info)

    def NewStmt(self, lhs, fields, position, info):
        return self.ast.NewStmt(lhs, self.to_seq(fields), position, info)

    def Label(self, name, position, info):
        return self.ast.Label(name, position, info)

    def Goto(self, name, position, info):
        return self.ast.Goto(name, position, info)

    def Seqn(self, body, position, info):
        return self.ast.Seqn(self.to_seq(body), position, info)

    def LocalVarAssign(self, lhs, rhs, position, info):
        return self.ast.LocalVarAssign(lhs, rhs, position, info)

    def FieldAssign(self, lhs, rhs, position, info):
        return self.ast.FieldAssign(lhs, rhs, position, info)

    def FieldAccess(self, receiver, field, position, info):
        return self.ast.FieldAccess(receiver, field, position, info)

    def FieldAccessPredicate(self, fieldacc, perm, position, info):
        return self.ast.FieldAccessPredicate(fieldacc, perm, position, info)

    def Old(self, expr, position, info):
        return self.ast.Old(expr, position, info)

    def Inhale(self, expr, position, info):
        return self.ast.Inhale(expr, position, info)

    def Exhale(self, expr, position, info):
        return self.ast.Exhale(expr, position, info)

    def InhaleExhaleExp(self, inhale, exhale, position, info):
        return self.ast.InhaleExhaleExp(inhale, exhale, position, info)

    def Assert(self, expr, position, info):
        return self.ast.Assert(expr, position, info)

    def FullPerm(self, position, info):
        return self.ast.FullPerm(position, info)

    def FractionalPerm(self, left, right, position, info):
        return self.ast.FractionalPerm(left, right, position, info)

    def Not(self, expr, position, info):
        return self.ast.Not(expr, position, info)

    def Minus(self, expr, position, info):
        return self.ast.Minus(expr, position, info)

    def CondExp(self, cond, then, els, position, info):
        return self.ast.CondExp(cond, then, els, position, info)

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

    def Implies(self, left, right, position, info):
        return self.ast.Implies(left, right, position, info)

    def FuncApp(self, name, args, position, info, type, formalargs):
        return self.ast.FuncApp(name, self.to_seq(args), position, info, type,
                                self.to_seq(formalargs))

    def ExplicitSeq(self, elems, position, info):
        return self.ast.ExplicitSeq(self.to_seq(elems), position, info)

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

    def NullLit(self, position, info):
        return self.ast.NullLit(position, info)

    def Forall(self, variables, triggers, exp, position, info):
        return self.ast.Forall(self.to_seq(variables), self.to_seq(triggers),
                               exp, position, info)

    def Trigger(self, exps, position, info):
        return self.ast.Trigger(self.to_seq(exps), position, info)

    def While(self, cond, invariants, locals, body, position, info):
        return self.ast.While(cond, self.to_seq(invariants),
                              self.to_seq(locals),
                              body, position, info)

    def Let(self, variable, exp, body, position, info):
        return self.ast.Let(variable, exp, body, position, info)

    def to_function0(self, func):
        func0 = Function0()
        func0.apply = types.MethodType(func, func0)
        result = self.jvm.get_proxy('scala.Function0', func0)
        return result

    def SimpleInfo(self, comments):
        return self.ast.SimpleInfo(self.to_seq(comments))

    def to_position(self, expr):
        if expr is None:
            return self.NoPosition
        path = self.java.nio.file.Paths.get(str(self.sourcefile), [])
        start = self.ast.LineColumnPosition(expr.lineno, expr.col_offset)
        if hasattr(expr, 'end_lineno') and hasattr(expr, 'end_col_offset'):
            end = self.ast.LineColumnPosition(expr.end_lineno,
                                              expr.end_col_offset)
            end = self.scala.Some(end)
        else:
            end = self.none
        return self.ast.SourcePosition(path, start, end)
