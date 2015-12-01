import ast
from viper_ast import ViperAST


contract_funcs = ['Requires', 'Ensures']
contract_keywords = set(["Requires", "Ensures", "Invariant", "Assume",
                         "Assert", "Old", "Result", "Pure"])

class Translator:
    def __init__(self, jvm, sourcefile, typeinfo):
        self.java = jvm.java
        self.scala = jvm.scala
        self.viper = jvm.viper
        self.types = typeinfo
        self.index = 0
        self.prefix = []
        self.methodcontext = False

        self.funcsAndMethods = {}


        viper = ViperAST(self.java, self.scala, self.viper, sourcefile)
        self.viper = viper

        self.builtins = {'builtins.int' : viper.Int,
                         'builtins.bool' : viper.Bool}

        def translate_num(slf : ast.Num):
            return viper.IntLit(slf.n, viper.toposition(slf), viper.NoInfo)
        ast.Num.translate_expr = translate_num

        def translate_compare(slf : ast.Compare):
            if len(slf.ops) == 1 and isinstance(slf.ops[0], ast.Eq) and len(slf.comparators) == 1:
                return viper.EqCmp(slf.left.translate_expr(), slf.comparators[0].translate_expr(), viper.toposition(slf), viper.NoInfo)
        ast.Compare.translate_expr = translate_compare

        def translate_return(slf : ast.Return):
            return slf.value.translate_expr()
        def translate_stmt_return(slf : ast.Return):
            type = self.types.getfunctype(self.prefix)
            return viper.LocalVarAssign(viper.LocalVar('_res', self.gettype(type), viper.NoPosition, viper.NoInfo), slf.value.translate_expr(), viper.toposition(slf), viper.NoInfo)
        ast.Return.translate_expr = translate_return
        ast.Return.translate_stmt = translate_stmt_return

        def translate_call(slf : ast.Call):
            if self.is_funccall(slf) in contract_funcs:
                raise Exception()
            elif self.is_funccall(slf) == "Result":
                type = self.types.getfunctype(self.prefix)
                if self.methodcontext:
                    return viper.LocalVar('_res', self.gettype(type), viper.NoPosition, viper.NoInfo)
                else:
                    return viper.Result(self.gettype(type), viper.toposition(slf), viper.NoInfo)
            else:
                args = []
                formalargs = []
                for arg in slf.args:
                    args.append(arg.translate_expr())
                name = self.is_funccall(slf)
                target = self.funcsAndMethods[name]
                for arg in target.args.args:
                    formalargs.append(self.translate_parameter_prefix(arg, [name]))
                return viper.FuncApp(self.is_funccall(slf), args, viper.toposition(slf), viper.NoInfo, viper.Int, formalargs)

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
            return viper.LocalVar(slf.id, viper.Int, viper.toposition(slf), viper.NoInfo)
        ast.Name.translate_expr = translate_name

        def translate_binop(slf : ast.BinOp):
            if isinstance(slf.op, ast.Add):
                return viper.Add(slf.left.translate_expr(), slf.right.translate_expr(), viper.toposition(slf), viper.NoInfo)
            elif isinstance(slf.op, ast.Sub):
                return viper.Sub(slf.left.translate_expr(), slf.right.translate_expr(), viper.toposition(slf), viper.NoInfo)
        ast.BinOp.translate_expr = translate_binop

        def translate_boolop(slf : ast.BoolOp):
            if len(slf.values) == 2:
                if isinstance(slf.op, ast.And):
                    return viper.And(slf.values[0].translate_expr(), slf.values[1].translate_expr(), viper.toposition(slf), viper.NoInfo)
        ast.BoolOp.translate_expr = translate_boolop

        def translate_stmt_if(slf : ast.If):
            cond = slf.test.translate_expr()
            oldprefix = self.prefix
            currentindex = self.index
            self.prefix = oldprefix + ['then' + str(currentindex)]
            thn = self.translate_block(slf.body, viper.toposition(slf), viper.NoInfo)
            self.prefix = oldprefix + ['else' + str(currentindex)]
            els = self.translate_block(slf.orelse, viper.toposition(slf), viper.NoInfo)
            self.prefix = oldprefix
            return viper.If(cond, thn, els, viper.toposition(slf), viper.NoInfo)
        ast.If.translate_stmt = translate_stmt_if

        def translate_stmt_assign(slf : ast.Assign):
            if len(slf.targets) == 1:
                type = self.types.gettype(self.prefix, slf.targets[0].id)
                return viper.LocalVarAssign(viper.LocalVar(slf.targets[0].id, self.gettype(type), viper.toposition(slf), viper.NoInfo), slf.value.translate_expr(), viper.toposition(slf), viper.NoInfo)
        ast.Assign.translate_stmt = translate_stmt_assign

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

    def is_pure(self, func):
        return len(func.decorator_list) == 1 and func.decorator_list[0].id == 'Pure'

    def translate_parameter(self, param):
        return self.translate_parameter_prefix(param, self.prefix)

    def translate_parameter_prefix(self, param, prefix):
        type = self.types.gettype(prefix, param.arg)
        return self.viper.LocalVarDecl(param.arg, self.gettype(type), self.viper.toposition(param), self.viper.NoInfo)

    def translate_function(self, func : ast.FunctionDef):
        if func.name in contract_keywords:
            return None
        else:
            self.methodcontext = False
            oldprefix = self.prefix
            self.prefix = self.prefix + [func.name]
            args = []
            for arg in func.args.args:
                args.append(self.translate_parameter(arg))
            type = self.gettype(self.types.gettype(oldprefix, func.name)) #self.viper.typeint
            pres = []
            posts = []
            bodyindex = 0
            while self.is_pre(func.body[bodyindex]):
                pres.append(func.body[bodyindex].translate_contract())
                bodyindex += 1
            while self.is_post(func.body[bodyindex]):
                postcond = func.body[bodyindex].translate_contract()
                posts.append(postcond)
                bodyindex += 1
            assert len(func.body) == bodyindex + 1
            body = func.body[bodyindex].translate_expr()
            self.prefix = oldprefix
            return self.viper.Function(func.name, args, type, pres, posts, body, self.viper.NoPosition, self.viper.NoInfo)

    def translate_method(self, func : ast.FunctionDef):
        if func.name in contract_keywords:
            return None
        else:
            self.methodcontext = True
            oldprefix = self.prefix
            self.prefix = self.prefix + [func.name]
            args = []
            for arg in func.args.args:
                args.append(self.translate_parameter(arg))
            type = self.gettype(self.types.gettype(oldprefix, func.name)) #self.viper.typeint
            results = [self.viper.LocalVarDecl('_res', type, self.viper.toposition(func), self.viper.NoInfo)]
            pres = []
            posts = []
            locals = []
            bodyindex = 0
            while self.is_pre(func.body[bodyindex]):
                pres.append(func.body[bodyindex].translate_contract())
                bodyindex += 1
            while self.is_post(func.body[bodyindex]):
                postcond = func.body[bodyindex].translate_contract()
                posts.append(postcond)
                bodyindex += 1
            body = self.translate_block(func.body[bodyindex:], self.viper.toposition(func), self.viper.NoInfo)
            self.prefix = oldprefix
            return self.viper.Method(func.name, args, results, pres, posts, locals, body, self.viper.toposition(func), self.viper.NoInfo)

    def translate_block(self, stmtlist, position, info):
        body = []
        for stmt in stmtlist:
            body.append(stmt.translate_stmt())
        return self.viper.Seqn(body, position, info)

    def translate_module(self, module : ast.Module):
        domains = []
        fields = []
        functions = []
        predicates = []
        methods = []
        for stmt in module.body:
            if isinstance(stmt, ast.FunctionDef):
                self.funcsAndMethods[stmt.name] = stmt
        for stmt in module.body:
            if isinstance(stmt, ast.FunctionDef):
                if self.is_pure(stmt):
                    functions.append(self.translate_function(stmt))
                else:
                    methods.append(self.translate_method(stmt))
        prog = self.viper.Program(domains, fields, functions, predicates, methods, self.viper.NoPosition, self.viper.NoInfo)
        return prog





