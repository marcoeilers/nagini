import ast

from typing import TypeVar, List, Tuple, Optional
import mypy

from viper_ast import ViperAST
from jvmaccess import JVM
from typeinfo import TypeInfo

CONTRACT_FUNCS = ['Requires', 'Ensures', 'Invariant']

contract_keywords = set(["Requires", "Ensures", "Invariant", "Assume",
                         "Assert", "Old", "Result", "Pure"])

T = TypeVar('T')
V = TypeVar('V')


class UnsupportedException(Exception):
    """
    Exception that is thrown when attempting to translate a Python element not
    currently supported
    """

    def __init__(self, astElement: ast.AST):
        super(UnsupportedException, self).__init__(str(astElement))


def unzip(list_of_pairs: List[Tuple[T, V]]) -> Tuple[List[T], List[V]]:
    """
    Unzips a list of pairs into two lists
    """
    vars_and_body = [list(t) for t in zip(*list_of_pairs)]
    vars = vars_and_body[0]
    body = vars_and_body[1]
    return vars, body


def flatten(list_of_lists: List[List[T]]) -> List[T]:
    """
    Flattens a list of lists into a flat list
    """
    return [item for sublist in list_of_lists for item in sublist]


class Translator:
    """
    Translates a Python AST to a Silver AST
    """

    def __init__(self, jvm: JVM, sourcefile: str, typeinfo: TypeInfo):
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

    def translate_expr(self, node: ast.AST) -> 'viper.silver.ast.Node':
        """
        Generic visitor function for translating an expression
        """
        method = 'translate_' + node.__class__.__name__
        visitor = getattr(self, method, self.translate_generic)
        return visitor(node)

    def translate_generic(self, node: ast.AST) -> 'viper.silver.ast.Node':
        """
        Visitor that is used if no other visitor is implemented.
        Simply raises an exception.
        """
        raise UnsupportedException(node)

    def translate_contract(self, node: ast.AST) -> 'viper.silver.ast.Node':
        """
        Generic visitor function for translating contracts (i.e. calls to
        contract functions)
        """
        method = 'translate_contract_' + node.__class__.__name__
        visitor = getattr(self, method, self.translate_generic)
        return visitor(node)

    def translate_contract_generic(self,
                                   node: ast.AST) -> 'viper.silver.ast.Node':
        """
        Contract visitor that is used if no other visitor is implemented.
        Simply raises an exception.
        """
        raise UnsupportedException(node)

    def translate_stmt(self, node: ast.AST) -> 'viper.silver.ast.Node':
        """
        Generic visitor function for translating statements
        """
        method = 'translate_stmt_' + node.__class__.__name__
        visitor = getattr(self, method, self.translate_generic)
        return visitor(node)

    def translate_contract_Call(self,
                                node: ast.Call) -> 'viper.silver.ast.Node':
        if self.is_funccall(node) in CONTRACT_FUNCS:
            return self.translate_expr(node.args[0])
        else:
            raise UnsupportedException(node)

    def translate_contract_Expr(self,
                                node: ast.Expr) -> 'viper.silver.ast.Node':
        if isinstance(node.value, ast.Call):
            return self.translate_contract(node.value)
        else:
            raise UnsupportedException(node)

    def translate_Num(self, node: ast.Num) -> 'viper.silver.ast.IntLit':
        return self.viper.IntLit(node.n, self.viper.to_position(node),
                                 self.viper.NoInfo)

    def translate_Return(self, node: ast.Return) -> 'viper.silver.ast.Exp':
        return self.translate_expr(node.value)

    def translate_Call(self, node: ast.Call) -> 'viper.silver.ast.Exp':
        if self.is_funccall(node) in CONTRACT_FUNCS:
            raise Exception()
        elif self.is_funccall(node) == "Result":
            type = self.types.getfunctype(self.prefix)
            if self.methodcontext:
                return self.viper.LocalVar('_res', self.getvipertype(type),
                                           self.viper.NoPosition,
                                           self.viper.NoInfo)
            else:
                return self.viper.Result(self.getvipertype(type),
                                         self.viper.to_position(node),
                                         self.viper.NoInfo)
        else:
            args = []
            formalargs = []
            for arg in node.args:
                args.append(self.translate_expr(arg))
            name = self.is_funccall(node)
            target = self.funcsAndMethods[name]
            for arg in target.args.args:
                formalargs.append(
                    self.translate_parameter_prefix(arg, [name]))
            return self.viper.FuncApp(self.is_funccall(node), args,
                                      self.viper.to_position(node),
                                      self.viper.NoInfo,
                                      self.viper.Int, formalargs)

    def translate_Expr(self, node: ast.Expr) -> 'viper.silver.ast.Exp':
        if isinstance(node.value, ast.Call):
            return self.translate_expr(node.value)
        else:
            raise UnsupportedException(node)

    def translate_Name(self, node: ast.Name) -> 'viper.silver.ast.Exp':
        type = self.types.gettype(self.prefix, node.id)
        return self.viper.LocalVar(node.id, self.getvipertype(type),
                                   self.viper.to_position(node),
                                   self.viper.NoInfo)

    def translate_BinOp(self, node: ast.BinOp) -> 'viper.silver.ast.Exp':
        left = self.translate_expr(node.left)
        right = self.translate_expr(node.right)
        if isinstance(node.op, ast.Add):
            return self.viper.Add(left,
                                  right,
                                  self.viper.to_position(node),
                                  self.viper.NoInfo)
        elif isinstance(node.op, ast.Sub):
            return self.viper.Sub(left,
                                  right,
                                  self.viper.to_position(node),
                                  self.viper.NoInfo)
        elif isinstance(node.op, ast.Mult):
            return self.viper.Mul(left,
                                  right,
                                  self.viper.to_position(node),
                                  self.viper.NoInfo)
        elif isinstance(node.op, ast.FloorDiv):
            return self.viper.Div(left,
                                  right,
                                  self.viper.to_position(node),
                                  self.viper.NoInfo)
        elif isinstance(node.op, ast.Mod):
            return self.viper.Mod(left,
                                  right,
                                  self.viper.to_position(node),
                                  self.viper.NoInfo)
        else:
            raise UnsupportedException(node)

    def translate_Compare(self, node: ast.Compare) -> 'viper.silver.ast.Exp':
        if len(node.ops) == 1 and len(node.comparators) == 1:
            left = self.translate_expr(node.left)
            right = self.translate_expr(node.comparators[0])
            if isinstance(node.ops[0], ast.Eq):
                return self.viper.EqCmp(left,
                                        right,
                                        self.viper.to_position(node),
                                        self.viper.NoInfo)
            elif isinstance(node.ops[0], ast.Gt):
                return self.viper.GtCmp(left,
                                        right,
                                        self.viper.to_position(node),
                                        self.viper.NoInfo)
            elif isinstance(node.ops[0], ast.GtE):
                return self.viper.GeCmp(left,
                                        right,
                                        self.viper.to_position(node),
                                        self.viper.NoInfo)
            elif isinstance(node.ops[0], ast.Lt):
                return self.viper.LtCmp(left,
                                        right,
                                        self.viper.to_position(node),
                                        self.viper.NoInfo)
            elif isinstance(node.ops[0], ast.LtE):
                return self.viper.LeCmp(left,
                                        right,
                                        self.viper.to_position(node),
                                        self.viper.NoInfo)
            elif isinstance(node.ops[0], ast.NotEq):
                return self.viper.NeCmp(left,
                                        right,
                                        self.viper.to_position(node),
                                        self.viper.NoInfo)
            else:
                raise UnsupportedException(node)
        else:
            raise UnsupportedException(node)

    def translate_NameConstant(self,
                               node: ast.NameConstant) -> 'viper.silver.ast.Exp':
        if node.value == True:
            return self.viper.TrueLit(self.viper.to_position(node),
                                      self.viper.NoInfo)
        elif node.value == False:
            return self.viper.FalseLit(self.viper.to_position(node),
                                       self.viper.NoInfo)
        else:
            raise UnsupportedException(node)

    def translate_BoolOp(self, node: ast.BoolOp) -> 'viper.silver.ast.Exp':
        if len(node.values) == 2:
            if isinstance(node.op, ast.And):
                return self.viper.And(self.translate_expr(node.values[0]),
                                      self.translate_expr(node.values[1]),
                                      self.viper.to_position(node),
                                      self.viper.NoInfo)
            elif isinstance(node.op, ast.Or):
                return self.viper.Or(self.translate_expr(node.values[0]),
                                     self.translate_expr(node.values[1]),
                                     self.viper.to_position(node),
                                     self.viper.NoInfo)
            else:
                raise UnsupportedException(node)
        else:
            raise UnsupportedException(node)

    def translate_stmt_AugAssign(self,
                                 node: ast.AugAssign) -> 'viper.silver.ast.Stmt':
        type = self.types.gettype(self.prefix, node.target.id)
        var = self.viper.LocalVar(node.target.id, self.getvipertype(type),
                                  self.viper.to_position(node),
                                  self.viper.NoInfo)
        if isinstance(node.op, ast.Add):
            newval = self.viper.Add(var, self.translate_expr(node.value),
                                    self.viper.to_position(node),
                                    self.viper.NoInfo)
        elif isinstance(node.op, ast.Sub):
            newval = self.viper.Sub(var, self.translate_expr(node.value),
                                    self.viper.to_position(node),
                                    self.viper.NoInfo)
        return (
            [],
            self.viper.LocalVarAssign(var, newval, self.viper.to_position(node),
                                      self.viper.NoInfo))

    def translate_stmt_If(self, node: ast.If) -> 'viper.silver.ast.Stmt':
        cond = self.translate_expr(node.test)
        thnvars, thnbody = unzip(
            [self.translate_stmt(stmt) for stmt in node.body])
        thn = self.translate_block(thnbody,
                                   self.viper.to_position(node),
                                   self.viper.NoInfo)
        elsvars, elsbody = unzip(
            [self.translate_stmt(stmt) for stmt in node.orelse])
        els = self.translate_block(
            elsbody,
            self.viper.to_position(node), self.viper.NoInfo)
        return (flatten(thnvars) + flatten(elsvars),
                self.viper.If(cond, thn, els, self.viper.to_position(node),
                              self.viper.NoInfo))

    def translate_stmt_Assign(self,
                              node: ast.Assign) -> 'viper.silver.ast.Stmt':
        if len(node.targets) == 1:
            type = self.types.gettype(self.prefix, node.targets[0].id)
            return ([(node.targets[0].id, type)], self.viper.LocalVarAssign(
                self.viper.LocalVar(node.targets[0].id, self.getvipertype(type),
                                    self.viper.to_position(node),
                                    self.viper.NoInfo),
                self.translate_expr(node.value), self.viper.to_position(node),
                self.viper.NoInfo))
        else:
            raise UnsupportedException(node)

    def translate_stmt_While(self, node: ast.While) -> 'viper.silver.ast.Stmt':
        cond = self.translate_expr(node.test)
        invariants = []
        locals = []
        bodyindex = 0
        while self.is_invariant(node.body[bodyindex]):
            invariants.append(self.translate_contract(node.body[bodyindex]))
            bodyindex += 1
        vars, body = unzip(
            [self.translate_stmt(stmt) for stmt in node.body[bodyindex:]])
        vars = flatten(vars)
        body = self.translate_block(body, self.viper.to_position(node),
                                    self.viper.NoInfo)
        return (vars, self.viper.While(cond, invariants, locals, body,
                                       self.viper.to_position(node),
                                       self.viper.NoInfo))

    def translate_stmt_Return(self,
                              node: ast.Return) -> 'viper.silver.ast.Stmt':
        type = self.types.getfunctype(self.prefix)
        assign = self.viper.LocalVarAssign(
            self.viper.LocalVar('_res', self.getvipertype(type),
                                self.viper.NoPosition, self.viper.NoInfo),
            self.translate_expr(node.value), self.viper.to_position(node),
            self.viper.NoInfo)
        jmp_to_end = self.viper.Goto("__end", self.viper.to_position(node),
                                     self.viper.NoInfo)
        return (
            [],
            self.viper.Seqn([assign, jmp_to_end], self.viper.to_position(node),
                            self.viper.NoInfo))

    def getvipertype(self, pytype: mypy.types.Type) -> 'viper.silver.ast.Type':
        return self.builtins[pytype.type.fullname()]

    def is_funccall(self, stmt: ast.AST) -> Optional[str]:
        """
        Checks if stmt is a function call and returns its name if it is, None
        otherwise.
        """
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            return stmt.value.func.id
        elif isinstance(stmt, ast.Call):
            return stmt.func.id
        else:
            return None

    def is_pre(self, stmt: ast.AST) -> bool:
        return self.is_funccall(stmt) == 'Requires'

    def is_post(self, stmt: ast.AST) -> bool:
        return self.is_funccall(stmt) == 'Ensures'

    def is_invariant(self, stmt: ast.AST) -> bool:
        return self.is_funccall(stmt) == 'Invariant'

    def is_pure(self, func) -> bool:
        return len(func.decorator_list) == 1 and func.decorator_list[
                                                     0].id == 'Pure'

    def translate_parameter(self, param: str) -> 'viper.ast.LocalVarDecl':
        return self.translate_parameter_prefix(param, self.prefix)

    def translate_parameter_prefix(self, param: str, prefix: List[
        str]) -> 'viper.ast.LocalVarDecl':
        type = self.types.gettype(prefix, param.arg)
        return self.viper.LocalVarDecl(param.arg, self.getvipertype(type),
                                       self.viper.to_position(param),
                                       self.viper.NoInfo)

    def translate_function(self, func: ast.FunctionDef) -> Optional[
        'viper.silver.ast.Function']:
        """
        Translates a Python function annotated as Pure to a Viper function
        """
        if func.name in contract_keywords:
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
                pres.append(self.translate_contract(func.body[bodyindex]))
                bodyindex += 1
            while self.is_post(func.body[bodyindex]):
                postcond = self.translate_contract(func.body[bodyindex])
                posts.append(postcond)
                bodyindex += 1
            assert len(func.body) == bodyindex + 1
            body = self.translate_expr(func.body[bodyindex])
            self.prefix = oldprefix
            return self.viper.Function(func.name, args, type, pres, posts, body,
                                       self.viper.NoPosition, self.viper.NoInfo)

    def translate_method(self, func: ast.FunctionDef) -> Optional[
        'viper.silver.ast.Method']:
        """
        Translates an impure Python function to a Viper method
        """
        if func.name in contract_keywords:
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
                pres.append(self.translate_contract(func.body[bodyindex]))
                bodyindex += 1
            while self.is_post(func.body[bodyindex]):
                postcond = self.translate_contract(func.body[bodyindex])
                posts.append(postcond)
                bodyindex += 1
            vars, body = unzip(
                [self.translate_stmt(stmt) for stmt in func.body[bodyindex:]])
            vars_to_declare = sorted(set(flatten(vars)))
            locals += [self.viper.LocalVarDecl(name, self.getvipertype(type),
                                               self.viper.NoPosition,
                                               self.viper.NoInfo) for name, type
                       in vars_to_declare]
            body += [self.viper.Label("__end", self.viper.NoPosition,
                                      self.viper.NoInfo)]
            bodyblock = self.translate_block(body, self.viper.to_position(func),
                                             self.viper.NoInfo)
            self.prefix = oldprefix
            return self.viper.Method(func.name, args, results, pres, posts,
                                     locals, bodyblock,
                                     self.viper.to_position(func),
                                     self.viper.NoInfo)

    def translate_block(self, stmtlist: List['viper.silver.ast.Stmt'],
                        position: 'viper.silver.ast.Position',
                        info: 'viper.silver.ast.Info') -> 'viper.silver.ast.Seqn':
        """
        Wraps a (Python) list of (Viper) statements into a Viper block
        """
        body = []
        for stmt in stmtlist:
            body.append(stmt)
        return self.viper.Seqn(body, position, info)

    def translate_module(self,
                         module: ast.Module) -> 'viper.silver.ast.Program':
        """
        Translates a Python module to a Viper program
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
