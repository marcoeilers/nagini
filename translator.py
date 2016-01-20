import ast
import mypy

from constants import CONTRACT_FUNCS, PRIMITIVES
from analyzer import Analyzer, PythonMethod, PythonClass, PythonField, PythonVar
from contracts.transformer import contract_keywords
from jvmaccess import JVM
from typeinfo import TypeInfo
from typing import TypeVar, List, Tuple, Optional, Dict
from viper_ast import ViperAST
from util import flatten, unzip, UnsupportedException

T = TypeVar('T')
V = TypeVar('V')

VarsAndStmt = Tuple[List[Tuple[str, mypy.types.Type]], 'silver.ast.Stmt']

class LetWrapper:
    def __init__(self, vardecl, expr, node):
        self.vardecl = vardecl
        self.expr = expr
        self.node = node

class Translator:
    """
    Translates a Python AST to a Silver AST
    """

    def __init__(self, jvm: JVM, sourcefile: str, typeinfo: TypeInfo):
        self.jvm = jvm
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

    def translate_exprs(self, nodes: List[ast.AST]):
        results = []
        for node in nodes:
            results.insert(0, self.translate_expr(node))
        result = None
        for letOrExpr in results:
            if result is None:
                assert not isinstance(letOrExpr, LetWrapper)
                result = letOrExpr
            else:
                assert isinstance(letOrExpr, LetWrapper)
                result = self.viper.Let(letOrExpr.vardecl, letOrExpr.expr, result, self.viper.to_position(letOrExpr.node),
                                         self.viper.NoInfo)
        assert result is not None
        return result

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

    def translate_Assign(self, node: ast.Assign):
        if len(node.targets) != 1:
            raise UnsupportedException(node)
        target = self.currentFunction.getVariable(node.targets[0].id).decl
        expr = self.translate_expr(node.value)
        return LetWrapper(target, expr, node)

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
            type = self.types.getfunctype(self.currentFunction.getScopePrefix())
            if not self.currentFunction.pure:
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
            target = self.program.getFuncOrMethod(name)
            assert target.pure
            for arg in target.args:
                formalargs.append(target.args[arg].decl)
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
        return self.currentFunction.getVariable(node.id).ref

    def translate_Attribute(self, node: ast.Attribute):
        receiver = self.translate_expr(node.value)
        rectype = self.getType(node.value)
        result = rectype.getField(node.attr)
        while result.inherited is not None:
            result = result.inherited
        return self.viper.FieldAccess(receiver, result.field, self.viper.to_position(node), self.viper.NoInfo)

    def getType(self, node):
        if isinstance(node, ast.Attribute):
            receiver = self.getType(node.value)
            return receiver.getField(node.attr).type
        elif isinstance(node, ast.Name):
            return self.currentFunction.getVariable(node.id).clazz

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
        var = self.currentFunction.getVariable(node.target.id).ref
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
        target = node.targets[0]
        var = self.translate_expr(target)
        assignment = self.viper.LocalVarAssign if isinstance(target, ast.Name) else self.viper.FieldAssign
        assign = assignment(var,
            self.translate_expr(node.value), self.viper.to_position(node),
            self.viper.NoInfo)
        return ([], assign)

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
        type = self.types.getfunctype(self.currentFunction.getScopePrefix())
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

    # def translate_parameter(self, param: str) -> 'viper.ast.LocalVarDecl':
    #     return self.translate_parameter_prefix(param, self.prefix)
    #
    # def translate_parameter_prefix(self, param: str, prefix: List[str]) \
    #         -> 'viper.ast.LocalVarDecl':
    #     type = self.types.gettype(prefix, param.arg)
    #     print(type)
    #     return self.viper.LocalVarDecl(param.arg, self.getvipertype(type),
    #                                    self.viper.to_position(param),
    #                                    self.viper.NoInfo)

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
                self.types.getfunctype(oldprefix + [func.name]))  # self.viper.typeint
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
                self.types.getfunctype(oldprefix + [func.name]))  # self.viper.typeint
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

    def create_type(self, clazz: PythonClass) -> Tuple[
        'DomainFunc', 'DomainAxiom']:
        supertype = clazz.superclass.silName if clazz.superclass is not None else 'object'
        position = self.viper.to_position(clazz.node)
        info = self.viper.NoInfo
        return (self.create_type_function(clazz.silName, position, info),
                self.create_subtype_axiom(clazz.silName, supertype, position,
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
        typevar = self.viper.LocalVar('class', self.typetype(), position, info)
        typefunc = self.viper.DomainFuncApp(type, [], {}, self.typetype(), [],
                                            position, info)
        supertypefunc = self.viper.DomainFuncApp(supertype, [], {},
                                                 self.typetype(), [], position,
                                                 info)
        body = self.viper.DomainFuncApp('issubtype', [typefunc, supertypefunc], {},
                                        self.viper.Bool, [typevar, typevar],
                                        position, info)
        return self.viper.DomainAxiom('subtype_' + type, body, position, info)

    def create_transitivity_axiom(self):
        argsub = self.viper.LocalVarDecl('sub', self.typetype(), self.viper.NoPosition, self.viper.NoInfo)
        varsub = self.viper.LocalVar('sub', self.typetype(), self.viper.NoPosition, self.viper.NoInfo)
        argmiddle = self.viper.LocalVarDecl('middle', self.typetype(), self.viper.NoPosition, self.viper.NoInfo)
        varmiddle = self.viper.LocalVar('middle', self.typetype(), self.viper.NoPosition, self.viper.NoInfo)
        argsuper = self.viper.LocalVarDecl('super', self.typetype(), self.viper.NoPosition, self.viper.NoInfo)
        varsuper = self.viper.LocalVar('super', self.typetype(), self.viper.NoPosition, self.viper.NoInfo)

        submiddle = self.viper.DomainFuncApp('issubtype', [varsub, varmiddle], {},
                                            self.viper.Bool, [varsub, varmiddle],
                                            self.viper.NoPosition, self.viper.NoInfo)
        middlesuper = self.viper.DomainFuncApp('issubtype', [varmiddle, varsuper], {},
                                            self.viper.Bool, [varmiddle, varsuper],
                                            self.viper.NoPosition, self.viper.NoInfo)
        subsuper = self.viper.DomainFuncApp('issubtype', [varsub, varsuper], {},
                                            self.viper.Bool, [varsub, varsuper],
                                            self.viper.NoPosition, self.viper.NoInfo)
        implication = self.viper.Implies(self.viper.And(submiddle, middlesuper, self.viper.NoPosition, self.viper.NoInfo), subsuper, self.viper.NoPosition, self.viper.NoInfo)
        trigger = self.viper.Trigger([submiddle, middlesuper], self.viper.NoPosition, self.viper.NoInfo)
        body = self.viper.Forall([argsub, argmiddle, argsuper], [trigger], implication, self.viper.NoPosition, self.viper.NoInfo)
        return self.viper.DomainAxiom('issubtype_transitivity', body, self.viper.NoPosition, self.viper.NoInfo)

    def create_reflexivity_axiom(self):
        arg = self.viper.LocalVarDecl('type', self.typetype(), self.viper.NoPosition, self.viper.NoInfo)
        var = self.viper.LocalVar('type', self.typetype(), self.viper.NoPosition, self.viper.NoInfo)
        reflexivesubtype = self.viper.DomainFuncApp('issubtype', [var, var], {},
                                            self.viper.Bool, [var, var],
                                            self.viper.NoPosition, self.viper.NoInfo)
        triggerexp = reflexivesubtype
        trigger = self.viper.Trigger([triggerexp], self.viper.NoPosition, self.viper.NoInfo)
        body = self.viper.Forall([arg], [trigger], reflexivesubtype, self.viper.NoPosition, self.viper.NoInfo)
        return self.viper.DomainAxiom('issubtype_reflexivity', body, self.viper.NoPosition, self.viper.NoInfo)

    def typeof_func(self):
        """
        Creates the typeof domain function
        """
        objvar = self.viper.LocalVarDecl('obj', self.viper.Ref,
                                         self.viper.NoPosition,
                                         self.viper.NoInfo)
        return self.viper.DomainFunc('typeof', [objvar],
                                     self.typetype(), False,
                                     self.viper.NoPosition, self.viper.NoInfo)

    def issubtype_func(self):
        """
        Creates the issubtype domain function
        """
        subvar = self.viper.LocalVarDecl('sub', self.typetype(),
                                           self.viper.NoPosition,
                                           self.viper.NoInfo)
        supervar = self.viper.LocalVarDecl('super', self.typetype(),
                                           self.viper.NoPosition,
                                           self.viper.NoInfo)
        return self.viper.DomainFunc('issubtype', [subvar, supervar],
                                     self.viper.Bool, False,
                                     self.viper.NoPosition, self.viper.NoInfo)

    def hasType(self, name, type: PythonClass):
        objvar = self.viper.LocalVar(name, self.viper.Ref,
                                         self.viper.NoPosition,
                                         self.viper.NoInfo)
        typefunc =  self.viper.DomainFuncApp('typeof', [objvar], {},
                                     self.typetype(), [objvar],
                                     self.viper.NoPosition, self.viper.NoInfo)
        supertypefunc = self.viper.DomainFuncApp(type.silName, [], {},
                                     self.typetype(), [],
                                     self.viper.NoPosition, self.viper.NoInfo)
        varsub = self.viper.LocalVar('sub', self.typetype(), self.viper.NoPosition, self.viper.NoInfo)
        varsuper = self.viper.LocalVar('super', self.typetype(), self.viper.NoPosition, self.viper.NoInfo)
        subtypefunc = self.viper.DomainFuncApp('issubtype', [typefunc, supertypefunc], {},
                                            self.viper.Bool, [varsub, varsuper],
                                            self.viper.NoPosition, self.viper.NoInfo)
        return subtypefunc

    def translate_pythonvar_decl(self, var):
        return self.viper.LocalVarDecl(var.silName, self.translate_type_new(var.clazz), self.viper.NoPosition, self.viper.NoInfo)

    def translate_pythonvar_ref(self, var):
        return self.viper.LocalVar(var.silName, self.translate_type_new(var.clazz), self.viper.NoPosition, self.viper.NoInfo)

    def translate_type_new(self, clazz: PythonClass): # returns Ref, Int, ...
        if 'builtins.' + clazz.name in self.builtins:
            return self.builtins['builtins.' + clazz.name]
        else:
            return self.viper.Ref

    def get_parameter_typeof(self, param):
        return self.hasType(param.silName, param.clazz)

    def translate_field(self, field: PythonField):
        return self.viper.Field(field.clazz.silName + '_'  + field.silName, self.translate_type_new(field.type), self.viper.to_position(field.node), self.viper.NoInfo)

    def translate_function_new(self, func: PythonMethod):
        oldfunction = self.currentFunction
        self.currentFunction = func
        type = self.translate_type_new(func.type)
        args = []
        for arg in func.args:
            args.append(func.args[arg].decl)
        assert len(func.declaredExceptions) == 0
        # create preconditions
        pres = []
        for pre in func.precondition:
            pres.append(self.translate_expr(pre))
        # create postconditions
        posts = []
        for post in func.postcondition:
            posts.append(self.translate_expr(post))
        # create typeof preconditions
        for arg in func.args:
            if not func.args[arg].clazz.name in PRIMITIVES:
                pres.append(self.get_parameter_typeof(func.args[arg]))
        bodyindex = 0
        statements = func.node.body
        while self.is_pre(statements[bodyindex]):
            bodyindex += 1
        while self.is_post(statements[bodyindex]):
            bodyindex += 1
        # translate body
        body = self.translate_exprs(statements[bodyindex:])
        self.currentFunction = oldfunction
        name = func.silName
        if func.clazz is not None:
            name = func.clazz.silName + '_' + name
        return self.viper.Function(name, args, type, pres, posts, body,
                                       self.viper.NoPosition, self.viper.NoInfo)

    def translate_method_new(self, method: PythonMethod):
        oldfunction = self.currentFunction
        self.currentFunction = method
        results = []
        if method.type is not None:
            type = self.translate_type_new(method.type)
            results.append(self.viper.LocalVarDecl('_res', type,
                                               self.viper.to_position(method.node),
                                               self.viper.NoInfo))
        args = []
        for arg in method.args:
            args.append(method.args[arg].decl)
        # create preconditions
        pres = []
        for pre in method.precondition:
            pres.append(self.translate_expr(pre))
        # create postconditions
        posts = []
        for post in method.postcondition:
            posts.append(self.translate_expr(post))
        # create typeof preconditions
        for arg in method.args:
            if not method.args[arg].clazz.name in PRIMITIVES:
                pres.append(self.get_parameter_typeof(method.args[arg]))
        bodyindex = 0
        statements = method.node.body
        while self.is_pre(statements[bodyindex]):
            bodyindex += 1
        while self.is_post(statements[bodyindex]):
            bodyindex += 1
        # translate body
        vars, body = unzip(
                [self.translate_stmt(stmt) for stmt in method.node.body[bodyindex:]])
        locals = []
        for local in method.locals:
            locals.append(method.locals[local].decl)
        body += [self.viper.Label("__end", self.viper.NoPosition,
                                      self.viper.NoInfo)]
        bodyblock = self.translate_block(body, self.viper.to_position(method.node),
                                             self.viper.NoInfo)
        self.currentFunction = oldfunction
        name = method.silName
        if method.clazz is not None:
            name = method.clazz.silName + '_' + name
        return self.viper.Method(name, args, results, pres, posts,
                                     locals, bodyblock,
                                     self.viper.to_position(method.node),
                                     self.viper.NoInfo)

    def translate_program(self, module: ast.Module):
        self.currentClass = None
        self.currentFunction = None
        analyzer = Analyzer(self.jvm, self.viper, self.types)
        analyzer.visit_default(module)
        analyzer.process(self)
        program = analyzer.program
        self.program = program
        domains = []
        fields = []
        functions = []
        predicates = []
        methods = []

        typeof = self.typeof_func()
        issubtype = self.issubtype_func()
        objectfunc = self.create_type_function('object', self.viper.NoPosition,
                                               self.viper.NoInfo)
        typefuncs = [objectfunc, typeof, issubtype]
        typeaxioms = [self.create_reflexivity_axiom(), self.create_transitivity_axiom()]

        for clazzname in program.classes:
            if clazzname in PRIMITIVES:
                continue
            clazz = program.classes[clazzname]
            for fieldname in clazz.fields:
                field = clazz.fields[fieldname]
                if field.inherited is None:
                    silField = self.translate_field(field)
                    field.field = silField
                    fields.append(silField)

        for function in program.functions:
            functions.append(self.translate_function_new(program.functions[function]))
        for method in program.methods:
            methods.append(self.translate_method_new(program.methods[method]))
        for clazzname in program.classes:
            if clazzname in PRIMITIVES:
                continue
            clazz = program.classes[clazzname]
            funcs, axioms = self.create_type(clazz)
            typefuncs.append(funcs)
            typeaxioms.append(axioms)
            for funcname in clazz.functions:
                func = clazz.functions[funcname]
                functions.append(self.translate_function_new(func))
            for methodname in clazz.methods:
                method = clazz.methods[methodname]
                methods.append(self.translate_method_new(method))

        domains.append(
            self.viper.Domain(self.typedomain, typefuncs, typeaxioms, [],
                              self.viper.NoPosition, self.viper.NoInfo))

        prog = self.viper.Program(domains, fields, functions, predicates,
                                  methods, self.viper.NoPosition,
                                  self.viper.NoInfo)
        return prog

    
    def translate_module(self, module: ast.Module) -> 'silver.ast.Program':
        """
        Translates a Python module to a Viper program
        """
        return self.translate_program(module)
        domains = []
        fields = []
        functions = []
        predicates = []
        methods = []

        typeof = self.typeof_func()
        issubtype = self.issubtype_func()
        objectfunc = self.create_type_function('object', self.viper.NoPosition,
                                               self.viper.NoInfo)
        typefuncs = [objectfunc, typeof, issubtype]
        typeaxioms = [self.create_reflexivity_axiom(), self.create_transitivity_axiom()]
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
