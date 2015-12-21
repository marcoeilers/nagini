import ast
import mypy

from contracts.transformer import contract_keywords
from jvmaccess import JVM
from typeinfo import TypeInfo
from typing import TypeVar, List, Tuple, Optional
from viper_ast import ViperAST

CONTRACT_FUNCS = ['Requires', 'Ensures', 'Invariant']

T = TypeVar('T')
V = TypeVar('V')

VarsAndStmt = Tuple[List[Tuple[str, mypy.types.Type]], 'silver.ast.Stmt']

class UnsupportedException(Exception):
    """
    Exception that is thrown when attempting to translate a Python element not
    currently supported
    """

    def __init__(self, astElement: ast.AST):
        super().__init__(str(astElement))


def unzip(pairs: List[Tuple[T, V]]) -> Tuple[List[T], List[V]]:
    """
    Unzips a list of pairs into two lists
    """
    vars_and_body = [list(t) for t in zip(*pairs)]
    vars = vars_and_body[0]
    body = vars_and_body[1]
    return vars, body


def flatten(lists: List[List[T]]) -> List[T]:
    """
    Flattens a list of lists into a flat list
    """
    return [item for sublist in lists for item in sublist]


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
        self.typedomain = "PyType"
        self.methodcontext = False
        self.funcsAndMethods = {}

        viper = ViperAST(jvm, self.java, self.scala, self.viper, sourcefile)
        self.viper = viper

        self.builtins = {'builtins.int': viper.Int,
                         'builtins.bool': viper.Bool}

    def translate_expr(self, node: ast.AST) -> 'silver.ast.Node':
        """
        Generic visitor function for translating an expression
        """
        method = 'translate_' + node.__class__.__name__
        visitor = getattr(self, method, self.translate_generic)
        return visitor(node)

    def translate_generic(self, node: ast.AST) -> 'silver.ast.Node':
        """
        Visitor that is used if no other visitor is implemented.
        Simply raises an exception.
        """
        raise UnsupportedException(node)

    def translate_contract(self, node: ast.AST) -> 'silver.ast.Node':
        """
        Generic visitor function for translating contracts (i.e. calls to
        contract functions)
        """
        method = 'translate_contract_' + node.__class__.__name__
        visitor = getattr(self, method, self.translate_generic)
        return visitor(node)

    def translate_stmt(self, node: ast.AST) -> 'silver.ast.Node':
        """
        Generic visitor function for translating statements
        """
        method = 'translate_stmt_' + node.__class__.__name__
        visitor = getattr(self, method, self.translate_generic)
        return visitor(node)

    def translate_contract_Call(self,
                                node: ast.Call) -> 'silver.ast.Node':
        if self.get_func_name(node) in CONTRACT_FUNCS:
            return self.translate_expr(node.args[0])
        else:
            raise UnsupportedException(node)

    def translate_contract_Expr(self,
                                node: ast.Expr) -> 'silver.ast.Node':
        if isinstance(node.value, ast.Call):
            return self.translate_contract(node.value)
        else:
            raise UnsupportedException(node)

    def translate_Num(self, node: ast.Num) -> 'silver.ast.IntLit':
        return self.viper.IntLit(node.n, self.viper.to_position(node),
                                 self.viper.NoInfo)

    def translate_Return(self, node: ast.Return) -> 'silver.ast.Exp':
        return self.translate_expr(node.value)

    def translate_Call(self, node: ast.Call) -> 'silver.ast.Exp':
        if self.get_func_name(node) in CONTRACT_FUNCS:
            raise ValueError("Contract call translated as normal call.")
        elif self.get_func_name(node) == "Result":
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
            name = self.get_func_name(node)
            target = self.funcsAndMethods[name]
            for arg in target.args.args:
                formalargs.append(
                    self.translate_parameter_prefix(arg, [name]))
            return self.viper.FuncApp(self.get_func_name(node), args,
                                      self.viper.to_position(node),
                                      self.viper.NoInfo,
                                      self.viper.Int, formalargs)

    def translate_Expr(self, node: ast.Expr) -> 'silver.ast.Exp':
        if isinstance(node.value, ast.Call):
            return self.translate_expr(node.value)
        else:
            raise UnsupportedException(node)

    def translate_Name(self, node: ast.Name) -> 'silver.ast.Exp':
        type = self.types.gettype(self.prefix, node.id)
        return self.viper.LocalVar(node.id, self.getvipertype(type),
                                   self.viper.to_position(node),
                                   self.viper.NoInfo)

    def translate_BinOp(self, node: ast.BinOp) -> 'silver.ast.Exp':
        left = self.translate_expr(node.left)
        right = self.translate_expr(node.right)
        if isinstance(node.op, ast.Add):
            return self.viper.Add(left, right,
                                  self.viper.to_position(node),
                                  self.viper.NoInfo)
        elif isinstance(node.op, ast.Sub):
            return self.viper.Sub(left, right,
                                  self.viper.to_position(node),
                                  self.viper.NoInfo)
        elif isinstance(node.op, ast.Mult):
            return self.viper.Mul(left, right,
                                  self.viper.to_position(node),
                                  self.viper.NoInfo)
        elif isinstance(node.op, ast.FloorDiv):
            return self.viper.Div(left, right,
                                  self.viper.to_position(node),
                                  self.viper.NoInfo)
        elif isinstance(node.op, ast.Mod):
            return self.viper.Mod(left, right,
                                  self.viper.to_position(node),
                                  self.viper.NoInfo)
        else:
            raise UnsupportedException(node)


    def translate_Compare(self, node: ast.Compare) -> 'silver.ast.Exp':
        if len(node.ops) != 1 or len(node.comparators) != 1:
            raise UnsupportedException(node)
        left = self.translate_expr(node.left)
        right = self.translate_expr(node.comparators[0])
        if isinstance(node.ops[0], ast.Eq):
            return self.viper.EqCmp(left, right,
                                    self.viper.to_position(node),
                                    self.viper.NoInfo)
        elif isinstance(node.ops[0], ast.Gt):
            return self.viper.GtCmp(left, right,
                                    self.viper.to_position(node),
                                    self.viper.NoInfo)
        elif isinstance(node.ops[0], ast.GtE):
            return self.viper.GeCmp(left, right,
                                    self.viper.to_position(node),
                                    self.viper.NoInfo)
        elif isinstance(node.ops[0], ast.Lt):
            return self.viper.LtCmp(left, right,
                                    self.viper.to_position(node),
                                    self.viper.NoInfo)
        elif isinstance(node.ops[0], ast.LtE):
            return self.viper.LeCmp(left, right,
                                    self.viper.to_position(node),
                                    self.viper.NoInfo)
        elif isinstance(node.ops[0], ast.NotEq):
            return self.viper.NeCmp(left, right,
                                    self.viper.to_position(node),
                                    self.viper.NoInfo)
        else:
            raise UnsupportedException(node)

    def translate_NameConstant(self,
                               node: ast.NameConstant) -> 'silver.ast.Exp':
        if node.value is True:
            return self.viper.TrueLit(self.viper.to_position(node),
                                      self.viper.NoInfo)
        elif node.value is False:
            return self.viper.FalseLit(self.viper.to_position(node),
                                       self.viper.NoInfo)
        else:
            raise UnsupportedException(node)

    def translate_BoolOp(self, node: ast.BoolOp) -> 'silver.ast.Exp':
        if len(node.values) != 2:
            raise UnsupportedException(node)
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

    def translate_stmt_AugAssign(self,
                                 node: ast.AugAssign) -> VarsAndStmt:
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
        return ([],
            self.viper.LocalVarAssign(var, newval, self.viper.to_position(node),
                                      self.viper.NoInfo))

    def translate_stmt_If(self, node: ast.If) -> VarsAndStmt:
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

    def translate_stmt_Assign(self, node: ast.Assign) -> VarsAndStmt:
        if len(node.targets) != 1:
            raise UnsupportedException(node)
        type = self.types.gettype(self.prefix, node.targets[0].id)
        var = self.viper.LocalVar(node.targets[0].id, self.getvipertype(type),
            self.viper.to_position(node), self.viper.NoInfo)
        assign = self.viper.LocalVarAssign(var,
            self.translate_expr(node.value), self.viper.to_position(node),
            self.viper.NoInfo)
        return ([(node.targets[0].id, type)], assign)

    def translate_stmt_While(self, node: ast.While) -> VarsAndStmt:
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
                              node: ast.Return) -> VarsAndStmt:
        type = self.types.getfunctype(self.prefix)
        assign = self.viper.LocalVarAssign(
            self.viper.LocalVar('_res', self.getvipertype(type),
                                self.viper.NoPosition, self.viper.NoInfo),
            self.translate_expr(node.value), self.viper.to_position(node),
            self.viper.NoInfo)
        jmp_to_end = self.viper.Goto("__end", self.viper.to_position(node),
                                     self.viper.NoInfo)
        return ([],
            self.viper.Seqn([assign, jmp_to_end], self.viper.to_position(node),
                            self.viper.NoInfo))

    def getvipertype(self, pytype: mypy.types.Type) -> VarsAndStmt:
        return self.builtins[pytype.type.fullname()]

    def get_func_name(self, stmt: ast.AST) -> Optional[str]:
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
        return self.get_func_name(stmt) == 'Requires'

    def is_post(self, stmt: ast.AST) -> bool:
        return self.get_func_name(stmt) == 'Ensures'

    def is_invariant(self, stmt: ast.AST) -> bool:
        return self.get_func_name(stmt) == 'Invariant'

    def is_pure(self, func) -> bool:
        return (len(func.decorator_list) == 1
                and func.decorator_list[0].id == 'Pure')

    def is_predicate(self, func) -> bool:
        return len(func.decorator_list) == 1 and func.decorator_list[
                                                     0].id == 'Predicate'

    def translate_parameter(self, param: str) -> 'viper.ast.LocalVarDecl':
        return self.translate_parameter_prefix(param, self.prefix)

    def translate_parameter_prefix(self, param: str, prefix: List[str]) \
            -> 'viper.ast.LocalVarDecl':
        type = self.types.gettype(prefix, param.arg)
        return self.viper.LocalVarDecl(param.arg, self.getvipertype(type),
                                       self.viper.to_position(param),
                                       self.viper.NoInfo)

    def translate_fields(self, clazz: ast.ClassDef) \
            -> List['silver.ast.Field']:
        pass

    def translate_function(self, func: ast.FunctionDef) \
            -> Optional['silver.ast.Function']:
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

    def translate_method(self, func: ast.FunctionDef) \
            -> Optional['silver.ast.Method']:
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

    def translate_block(self, stmtlist: List['silver.ast.Stmt'],
                        position: 'silver.ast.Position',
                        info: 'silver.ast.Info') -> 'silver.ast.Seqn':
        """
        Wraps a (Python) list of (Viper) statements into a Viper block
        """
        body = []
        for stmt in stmtlist:
            body.append(stmt)
        return self.viper.Seqn(body, position, info)

    def create_type(self, clazz: ast.ClassDef) -> Tuple[
        'DomainFunc', 'DomainAxiom']:
        if len(clazz.bases) > 1:
            raise UnsupportedException(clazz)
        supertype = clazz.bases[0].id if len(clazz.bases) == 1 else 'object'
        position = self.viper.to_position(clazz)
        info = self.viper.NoInfo
        return (self.create_type_function(clazz.name, position, info),
                self.create_subtype_axiom(clazz.name, supertype, position,
                                          info))

    def create_type_function(self, name, position, info):
        return self.viper.DomainFunc(name, [], self.typetype(), True, position,
                                     info)

    def typetype(self):
        """
        Creates a reference to the domain type we use for the Python types
        """
        return self.viper.DomainType(self.typedomain, {}, [])

    def create_subtype_axiom(self, type, supertype, position, info):
        """
        Creates a domain axiom that indicates a subtype relationship
        between type and supertype
        """
        arg = self.viper.LocalVarDecl('obj', self.viper.Ref, position, info)
        var = self.viper.LocalVar('obj', self.viper.Ref, position, info)
        typevar = self.viper.LocalVar('class', self.typetype(), position, info)
        typefunc = self.viper.DomainFuncApp(type, [], {}, self.typetype(), [],
                                            position, info)
        supertypefunc = self.viper.DomainFuncApp(supertype, [], {},
                                                 self.typetype(), [], position,
                                                 info)

        def instanceof(typefunc):
            return self.viper.DomainFuncApp('isinstance', [var, typefunc], {},
                                            self.viper.Bool, [var, typevar],
                                            position, info)

        instanceofsub = instanceof(typefunc)
        instanceofsuper = instanceof(supertypefunc)
        triggerexp = instanceofsub
        trigger = self.viper.Trigger([triggerexp], position, info)
        exp = self.viper.Implies(instanceofsub, instanceofsuper, position, info)
        body = self.viper.Forall([arg], [trigger], exp, position, info)
        return self.viper.DomainAxiom('subtype_' + type, body, position, info)

    def isinstance_func(self):
        """
        Creates the isinstance domain function
        """
        objvar = self.viper.LocalVarDecl('obj', self.viper.Ref,
                                         self.viper.NoPosition,
                                         self.viper.NoInfo)
        classvar = self.viper.LocalVarDecl('class', self.typetype(),
                                           self.viper.NoPosition,
                                           self.viper.NoInfo)
        return self.viper.DomainFunc('isinstance', [objvar, classvar],
                                     self.viper.Bool, False,
                                     self.viper.NoPosition, self.viper.NoInfo)
    
    def translate_module(self, module: ast.Module) -> 'silver.ast.Program':
        """
        Translates a Python module to a Viper program
        """
        domains = []
        fields = []
        functions = []
        predicates = []
        methods = []

        isinstancefunc = self.isinstance_func()
        objectfunc = self.create_type_function('object', self.viper.NoPosition,
                                               self.viper.NoInfo)
        typefuncs = [objectfunc, isinstancefunc]
        typeaxioms = []
        for stmt in module.body:
            if isinstance(stmt, ast.FunctionDef):
                self.funcsAndMethods[stmt.name] = stmt
        for stmt in module.body:
            if isinstance(stmt, ast.FunctionDef):
                if self.is_pure(stmt):
                    functions.append(self.translate_function(stmt))
                else:
                    methods.append(self.translate_method(stmt))
            elif isinstance(stmt, ast.ClassDef):
                funcs, axioms = self.create_type(stmt)
                typefuncs.append(funcs)
                typeaxioms.append(axioms)
                # add domain function to type domain
                # possibly add subtype axiom to type domain
                # add fields
                # add methods/functions
                pass

        domains.append(
            self.viper.Domain(self.typedomain, typefuncs, typeaxioms, [],
                              self.viper.NoPosition, self.viper.NoInfo))
        prog = self.viper.Program(domains, fields, functions, predicates,
                                  methods, self.viper.NoPosition,
                                  self.viper.NoInfo)
        return prog
