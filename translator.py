import ast
import builtins
from constants import ViperAST


contract_funcs = ['Requires', 'Ensures']
contract_keywords = set(["Requires", "Ensures", "Invariant", "Assume",
                         "Assert", "Old", "Result", "Pure"])

class Translator:
    def __init__(self, jpype, sourcefile, typeinfo):
        self.java = jpype.java
        self.scala = jpype.scala
        self.viper = jpype.viper
        self.types = typeinfo
        self.index = 0
        self.prefix = []



        viper = ViperAST(self.java, self.scala, self.viper, sourcefile)
        self.viper = viper

        self.builtins = {'builtins.int' : viper.typeint,
                         'builtins.bool' : viper.typebool}

        def translate_num(slf : ast.Num):
            return viper.intlit(slf.n, viper.toposition(slf), viper.noinfo)
        ast.Num.translate_expr = translate_num

        def translate_compare(slf : ast.Compare):
            if len(slf.ops) == 1 and isinstance(slf.ops[0], ast.Eq) and len(slf.comparators) == 1:
                return viper.eqcmp(slf.left.translate_expr(), slf.comparators[0].translate_expr(), viper.toposition(slf), viper.noinfo)
        ast.Compare.translate_expr = translate_compare

        def translate_return(slf : ast.Return):
            return slf.value.translate_expr()
        ast.Return.translate_expr = translate_return

        def translate_call(slf : ast.Call):
            if self.is_funccall(slf) in contract_funcs:
                raise Exception()
            elif self.is_funccall(slf) == "Result":
                type = self.types.getfunctype(self.prefix)
                return viper.result(self.gettype(type), viper.toposition(slf), viper.noinfo)
            else:
                args = viper.emptyseq()
                formalargs = viper.emptyseq()
                return viper.funcapp(self.is_funccall(slf), args, viper.toposition(slf), viper.noinfo, viper.typeint, formalargs)

        def translate_call_contract(slf : ast.Call):
            if self.is_funccall(slf) in contract_funcs:
                return slf.args[0].translate_expr()
            else:
                raise Exception()
        ast.Call.translate_expr = translate_call
        ast.Call.translate_contract = translate_call_contract

        def translate_expr(slf : ast.Expr):
            if isinstance(slf.value, ast.Call):
                return slf.value.translate_expr()
        ast.Expr.translate_expr = translate_expr

        def translate_expr_contract(slf : ast.Expr):
            if isinstance(slf.value, ast.Call):
                return slf.value.translate_contract()
        ast.Expr.translate_contract = translate_expr_contract

        def translate_name(slf : ast.Name):
            return viper.localvar(slf.id, viper.typeint, viper.toposition(slf), viper.noinfo)
        ast.Name.translate_expr = translate_name

    def gettype(self, pytype):
        return self.builtins[pytype.type.fullname()]


    def is_funccall(self, stmt):
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            return stmt.value.func.id
        elif isinstance(stmt, ast.Call):
            return stmt.func.id
        else:
            return None

    def is_pre(self, stmt):
        return self.is_funccall(stmt) == 'Requires'

    def is_post(self, stmt):
        return self.is_funccall(stmt) == 'Ensures'

    def append(self, list, toappend):
        if not toappend is None:
            lsttoappend = self.viper.singletonseq(toappend)
            list.append(lsttoappend)

    def translate_parameter(self, param):
        type = self.types.gettype(self.prefix, param.arg)
        return self.viper.localvardecl(param.arg, self.gettype(type), self.viper.toposition(param), self.viper.noinfo)

    def translate_function(self, func : ast.FunctionDef):
        if func.name in contract_keywords:
            return None
        else:
            oldprefix = self.prefix
            self.prefix = self.prefix + [func.name]
            args = self.viper.emptyseq()
            for arg in func.args.args:
                self.append(args, self.translate_parameter(arg))
            type = self.gettype(self.types.gettype(oldprefix, func.name)) #self.viper.typeint
            pres = self.viper.emptyseq()
            posts = self.viper.emptyseq()
            bodyindex = 0
            while self.is_pre(func.body[bodyindex]):
                self.append(pres, func.body[bodyindex].translate_contract())
                bodyindex += 1
            while self.is_post(func.body[bodyindex]):
                postcond = func.body[bodyindex].translate_contract()
                self.append(posts, postcond)
                bodyindex += 1
            body = func.body[bodyindex].translate_expr()
            self.prefix = oldprefix
            return self.viper.function(func.name, args, type, pres, posts, body, self.viper.noposition, self.viper.noinfo)

    def translate_module(self, module : ast.Module):
        domains = self.viper.emptyseq()
        fields = self.viper.emptyseq()
        functions = self.viper.emptyseq()
        predicates = self.viper.emptyseq()
        methods = self.viper.emptyseq()
        for stmt in module.body:
            if isinstance(stmt, ast.FunctionDef):
                self.append(functions, self.translate_function(stmt))
        prog = self.viper.program(domains, fields, functions, predicates, methods, self.viper.noposition, self.viper.noinfo)
        return prog





