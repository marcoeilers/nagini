import ast
from viper_ast import ViperAST

CONTRACT_FUNCS = ['Requires', 'Ensures', 'Invariant']
CONTRACT_KEYWORDS = set(["Requires", "Ensures", "Invariant", "Assume",
                         "Assert", "Old", "Result", "Pure"])

translate_stmt = lambda stmt: stmt.translate_stmt()


class UnsupportedException(Exception):
    """
    Exception that is thrown when attempting to translate a Python element not currently supported
    """

    def __init__(self, astElement):
        super(UnsupportedException, self).__init__(str(astElement))


def unzip(list_of_pairs):
    vars_and_body = [list(t) for t in zip(*list_of_pairs)]
    vars = vars_and_body[0]
    body = vars_and_body[1]
    return vars, body

def flatten(list_of_lists):
    return [item for sublist in list_of_lists for item in sublist]


class Translator:
    """
    Translates a Python AST to a Silver AST
    """

    def __init__(self, jvm, sourcefile, typeinfo):
        self.java = jvm.java
        self.scala = jvm.scala
        self.viper = jvm.viper
        self.types = typeinfo
        self.prefix = []
        self.methodcontext = False
        self.funcsAndMethods = {}

        viper = ViperAST(self.java, self.scala, self.viper, sourcefile)
        self.viper = viper

        self.builtins = {'builtins.int': viper.Int,
                         'builtins.bool': viper.Bool}

        def translate_num(slf: ast.Num):
            return viper.IntLit(slf.n, viper.to_position(slf), viper.NoInfo)

        ast.Num.translate_expr = translate_num

        def translate_compare(slf: ast.Compare):
            if len(slf.ops) == 1 and len(slf.comparators) == 1:
                if isinstance(slf.ops[0], ast.Eq):
                    return viper.EqCmp(slf.left.translate_expr(),
                                       slf.comparators[0].translate_expr(),
                                       viper.to_position(slf), viper.NoInfo)
                elif isinstance(slf.ops[0], ast.Gt):
                    return viper.GtCmp(slf.left.translate_expr(),
                                       slf.comparators[0].translate_expr(),
                                       viper.to_position(slf), viper.NoInfo)
                elif isinstance(slf.ops[0], ast.GtE):
                    return viper.GeCmp(slf.left.translate_expr(),
                                       slf.comparators[0].translate_expr(),
                                       viper.to_position(slf), viper.NoInfo)
                elif isinstance(slf.ops[0], ast.Lt):
                    return viper.LtCmp(slf.left.translate_expr(),
                                       slf.comparators[0].translate_expr(),
                                       viper.to_position(slf), viper.NoInfo)
                elif isinstance(slf.ops[0], ast.LtE):
                    return viper.LeCmp(slf.left.translate_expr(),
                                       slf.comparators[0].translate_expr(),
                                       viper.to_position(slf), viper.NoInfo)
                elif isinstance(slf.ops[0], ast.NotEq):
                    return viper.NeCmp(slf.left.translate_expr(),
                                       slf.comparators[0].translate_expr(),
                                       viper.to_position(slf), viper.NoInfo)
                else:
                    raise UnsupportedException(slf)
            else:
                raise UnsupportedException(slf)

        ast.Compare.translate_expr = translate_compare

        def translate_return(slf: ast.Return):
            return slf.value.translate_expr()

        def translate_stmt_return(slf: ast.Return):
            type = self.types.getfunctype(self.prefix)
            assign = viper.LocalVarAssign(
                viper.LocalVar('_res', self.getvipertype(type),
                               viper.NoPosition, viper.NoInfo),
                slf.value.translate_expr(), viper.to_position(slf), viper.NoInfo)
            jmp_to_end = viper.Goto("__end", viper.to_position(slf),
                                    viper.NoInfo)
            return ([], viper.Seqn([assign, jmp_to_end], viper.to_position(slf),
                              viper.NoInfo))

        ast.Return.translate_expr = translate_return
        ast.Return.translate_stmt = translate_stmt_return

        def translate_call(slf: ast.Call):
            if self.is_funccall(slf) in CONTRACT_FUNCS:
                raise Exception()
            elif self.is_funccall(slf) == "Result":
                type = self.types.getfunctype(self.prefix)
                if self.methodcontext:
                    return viper.LocalVar('_res', self.getvipertype(type),
                                          viper.NoPosition, viper.NoInfo)
                else:
                    return viper.Result(self.getvipertype(type),
                                        viper.to_position(slf), viper.NoInfo)
            else:
                args = []
                formalargs = []
                for arg in slf.args:
                    args.append(arg.translate_expr())
                name = self.is_funccall(slf)
                target = self.funcsAndMethods[name]
                for arg in target.args.args:
                    formalargs.append(
                        self.translate_parameter_prefix(arg, [name]))
                return viper.FuncApp(self.is_funccall(slf), args,
                                     viper.to_position(slf), viper.NoInfo,
                                     viper.Int, formalargs)

        def translate_call_contract(slf: ast.Call):
            if self.is_funccall(slf) in CONTRACT_FUNCS:
                return slf.args[0].translate_expr()
            else:
                raise UnsupportedException(slf)

        ast.Call.translate_expr = translate_call
        ast.Call.translate_contract = translate_call_contract

        def translate_expr(slf: ast.Expr):
            if isinstance(slf.value, ast.Call):
                return slf.value.translate_expr()
            else:
                raise UnsupportedException(slf)

        ast.Expr.translate_expr = translate_expr

        def translate_expr_contract(slf: ast.Expr):
            if isinstance(slf.value, ast.Call):
                return slf.value.translate_contract()
            else:
                raise UnsupportedException(slf)

        ast.Expr.translate_contract = translate_expr_contract

        def translate_name(slf: ast.Name):
            type = self.types.gettype(self.prefix, slf.id)
            return viper.LocalVar(slf.id, self.getvipertype(type),
                                  viper.to_position(slf), viper.NoInfo)

        ast.Name.translate_expr = translate_name

        def translate_binop(slf: ast.BinOp):
            if isinstance(slf.op, ast.Add):
                return viper.Add(slf.left.translate_expr(),
                                 slf.right.translate_expr(),
                                 viper.to_position(slf), viper.NoInfo)
            elif isinstance(slf.op, ast.Sub):
                return viper.Sub(slf.left.translate_expr(),
                                 slf.right.translate_expr(),
                                 viper.to_position(slf), viper.NoInfo)
            elif isinstance(slf.op, ast.Mult):
                return viper.Mul(slf.left.translate_expr(),
                                 slf.right.translate_expr(),
                                 viper.to_position(slf), viper.NoInfo)
            elif isinstance(slf.op, ast.FloorDiv):
                return viper.Div(slf.left.translate_expr(),
                                 slf.right.translate_expr(),
                                 viper.to_position(slf), viper.NoInfo)
            elif isinstance(slf.op, ast.Mod):
                return viper.Mod(slf.left.translate_expr(),
                                 slf.right.translate_expr(),
                                 viper.to_position(slf), viper.NoInfo)
            else:
                raise UnsupportedException(slf)

        ast.BinOp.translate_expr = translate_binop

        def translate_boolop(slf: ast.BoolOp):
            if len(slf.values) == 2:
                if isinstance(slf.op, ast.And):
                    return viper.And(slf.values[0].translate_expr(),
                                     slf.values[1].translate_expr(),
                                     viper.to_position(slf), viper.NoInfo)
                elif isinstance(slf.op, ast.Or):
                    return viper.Or(slf.values[0].translate_expr(),
                                    slf.values[1].translate_expr(),
                                    viper.to_position(slf), viper.NoInfo)
                else:
                    raise UnsupportedException(slf)
            else:
                raise UnsupportedException(slf)

        ast.BoolOp.translate_expr = translate_boolop

        def translate_stmt_augassign(slf: ast.AugAssign):
            type = self.types.gettype(self.prefix, slf.target.id)
            var = viper.LocalVar(slf.target.id, self.getvipertype(type),
                                 viper.to_position(slf), viper.NoInfo)
            if isinstance(slf.op, ast.Add):
                newval = viper.Add(var, slf.value.translate_expr(),
                                   viper.to_position(slf), viper.NoInfo)
            elif isinstance(slf.op, ast.Sub):
                newval = viper.Sub(var, slf.value.translate_expr(),
                                   viper.to_position(slf), viper.NoInfo)
            return ([], viper.LocalVarAssign(var, newval, viper.to_position(slf),
                                        viper.NoInfo))

        ast.AugAssign.translate_stmt = translate_stmt_augassign

        def translate_stmt_if(slf: ast.If):
            cond = slf.test.translate_expr()
            thnvars, thnbody = unzip([stmt.translate_stmt() for stmt in slf.body])
            thn = self.translate_block(thnbody,
                viper.to_position(slf), viper.NoInfo)
            elsvars, elsbody = unzip([stmt.translate_stmt() for stmt in slf.orelse])
            els = self.translate_block(
                elsbody,
                viper.to_position(slf), viper.NoInfo)
            return (flatten(thnvars) + flatten(elsvars), viper.If(cond, thn, els, viper.to_position(slf), viper.NoInfo))

        ast.If.translate_stmt = translate_stmt_if

        def translate_stmt_assign(slf: ast.Assign):
            if len(slf.targets) == 1:
                type = self.types.gettype(self.prefix, slf.targets[0].id)
                return ([(slf.targets[0].id, type)], viper.LocalVarAssign(
                    viper.LocalVar(slf.targets[0].id, self.getvipertype(type),
                                   viper.to_position(slf), viper.NoInfo),
                    slf.value.translate_expr(), viper.to_position(slf),
                    viper.NoInfo))
            else:
                raise UnsupportedException(slf)

        ast.Assign.translate_stmt = translate_stmt_assign

        def translate_stmt_while(slf: ast.While):
            cond = slf.test.translate_expr()
            invariants = []
            locals = []
            bodyindex = 0
            while self.is_invariant(slf.body[bodyindex]):
                invariants.append(slf.body[bodyindex].translate_contract())
                bodyindex += 1
            vars, body = unzip([stmt.translate_stmt() for stmt in slf.body[bodyindex:]])
            vars = flatten(vars)
            body = self.translate_block(body, viper.to_position(slf),
                                        viper.NoInfo)
            return (vars, viper.While(cond, invariants, locals, body,
                               viper.to_position(slf), viper.NoInfo))

        ast.While.translate_stmt = translate_stmt_while

        def translate_constant(slf: ast.NameConstant):
            if slf.value == True:
                return viper.TrueLit(viper.to_position(slf), viper.NoInfo)
            elif slf.value == False:
                return viper.FalseLit(viper.to_position(slf), viper.NoInfo)
            else:
                raise UnsupportedException(slf)

        ast.NameConstant.translate_expr = translate_constant

    def getvipertype(self, pytype):
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

    def is_invariant(self, stmt):
        return self.is_funccall(stmt) == 'Invariant'

    def is_pure(self, func):
        return len(func.decorator_list) == 1 and func.decorator_list[
                                                     0].id == 'Pure'

    def translate_parameter(self, param):
        return self.translate_parameter_prefix(param, self.prefix)

    def translate_parameter_prefix(self, param, prefix):
        type = self.types.gettype(prefix, param.arg)
        return self.viper.LocalVarDecl(param.arg, self.getvipertype(type),
                                       self.viper.to_position(param),
                                       self.viper.NoInfo)

    def translate_function(self, func: ast.FunctionDef):
        """
        Translates a Python function annotated as Pure to a Viper function
        :param func:
        :return:
        """
        if func.name in CONTRACT_KEYWORDS:
            return None
        else:
            self.methodcontext = False
            oldprefix = self.prefix
            self.prefix = self.prefix + [func.name]
            args = []
            for arg in func.args.args:
                args.append(self.translate_parameter(arg))
            type = self.getvipertype(
                self.types.gettype(oldprefix, func.name))  # self.viper.typeint
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
            return self.viper.Function(func.name, args, type, pres, posts, body,
                                       self.viper.NoPosition, self.viper.NoInfo)

    def translate_method(self, func: ast.FunctionDef):
        """
        Translates an impure Python function to a Viper method
        :param func:
        :return:
        """
        if func.name in CONTRACT_KEYWORDS:
            return None
        else:
            self.methodcontext = True
            oldprefix = self.prefix
            self.prefix = self.prefix + [func.name]
            args = []
            for arg in func.args.args:
                args.append(self.translate_parameter(arg))
            type = self.getvipertype(
                self.types.gettype(oldprefix, func.name))  # self.viper.typeint
            results = [self.viper.LocalVarDecl('_res', type,
                                               self.viper.to_position(func),
                                               self.viper.NoInfo)]
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
            vars, body = unzip([stmt.translate_stmt() for stmt in func.body[bodyindex:]])
            vars_to_declare = sorted(set(flatten(vars)))
            locals += [self.viper.LocalVarDecl(name, self.getvipertype(type), self.viper.NoPosition, self.viper.NoInfo) for name, type in vars_to_declare]
            body += [self.viper.Label("__end", self.viper.NoPosition,
                                      self.viper.NoInfo)]
            bodyblock = self.translate_block(body, self.viper.to_position(func),
                                             self.viper.NoInfo)
            self.prefix = oldprefix
            return self.viper.Method(func.name, args, results, pres, posts,
                                     locals, bodyblock,
                                     self.viper.to_position(func),
                                     self.viper.NoInfo)

    def translate_block(self, stmtlist, position, info):
        """
        Wraps a (Python) list of (Viper) statements into a Viper block
        :param stmtlist:
        :param position:
        :param info:
        :return:
        """
        body = []
        for stmt in stmtlist:
            body.append(stmt)
        return self.viper.Seqn(body, position, info)

    def translate_module(self, module: ast.Module):
        """
        Translates a PYthon module to a Viper program
        :param module:
        :return:
        """
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
        prog = self.viper.Program(domains, fields, functions, predicates,
                                  methods, self.viper.NoPosition,
                                  self.viper.NoInfo)
        return prog
