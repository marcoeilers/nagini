import ast

from analyzer import PythonVar, PythonMethod, PythonClass, PythonField, \
    PythonProgram, PythonExceptionHandler
from constants import CONTRACT_WRAPPER_FUNCS, CONTRACT_FUNCS, PRIMITIVES
from jvmaccess import JVM
from typeinfo import TypeInfo
from typing import Any, TypeVar, List, Tuple, Optional, Dict
from viper_ast import ViperAST
from util import flatten, UnsupportedException

T = TypeVar('T')
V = TypeVar('V')

Expr = 'silver.ast.Exp'
Stmt = 'silver.ast.Stmt'
StmtAndExpr = Tuple[List[Stmt], Expr]


class LetWrapper:
    """
    Represents a let-expression to be created later.
    Used so we can set/exchange expr later, which we cannot with the AST element
    """
    def __init__(self, vardecl: 'silver.ast.VarDecl', expr: 'silver.ast.Exp',
                 node: ast.AST):
        self.vardecl = vardecl
        self.expr = expr
        self.node = node


class InvalidProgramException(Exception):
    """
    Signals that the input program is invalid and cannot be translated
    """
    def __init__(self, node: ast.AST, code: str, message: str = None):
        self.node = node
        self.code = code
        self.message = message


class Translator:
    """
    Translates a Python AST to a Silver AST
    """

    def __init__(self, jvm: JVM, sourcefile: str, typeinfo: TypeInfo,
                 viperast: ViperAST):
        self.jvm = jvm
        self.java = jvm.java
        self.scala = jvm.scala
        self.viper = jvm.viper
        self.types = typeinfo
        self.prefix = []
        self.typedomain = "PyType"
        self.viper = viperast
        self.position = None
        self.info = None

        self.builtins = {'builtins.int': viperast.Int,
                         'builtins.bool': viperast.Bool}

    def translate_exprs(self, nodes: List[ast.AST], function) -> Expr:
        """
        Translates a list of nodes to a single (let-)expression if all
        nodes are assignments and the last is a return
        """
        results = []
        for node in nodes:
            stmts, expr = self.translate_expr(node)
            if len(stmts) != 0:
                raise InvalidProgramException(node, 'purity.violated')
            results.insert(0, expr)
        result = None
        for letOrExpr in results:
            if result is None:
                if isinstance(letOrExpr, LetWrapper):
                    raise InvalidProgramException(function.node,
                                                  'function.return.missing')
                result = letOrExpr
            else:
                if not isinstance(letOrExpr, LetWrapper):
                    raise InvalidProgramException(function.node,
                                                  'function.dead.code')
                result = self.viper.Let(letOrExpr.vardecl, letOrExpr.expr,
                                        result,
                                        self.to_position(letOrExpr.node),
                                        self.noinfo())
        if result is None:
            raise InvalidProgramException(function.node,
                                          'function.return.missing')
        return result

    def translate_expr(self, node: ast.AST) -> StmtAndExpr:
        """
        Generic visitor function for translating an expression
        """
        method = 'translate_' + node.__class__.__name__
        visitor = getattr(self, method, self.translate_generic)
        return visitor(node)

    def translate_perm(self, node: ast.AST) -> Expr:
        """
        Generic visitor function for translating a permission amount
        """
        method = 'translate_perm_' + node.__class__.__name__
        visitor = getattr(self, method, self.translate_generic)
        return visitor(node)

    def translate_perm_Num(self, node: ast.Num) -> Expr:
        if node.n == 1:
            return self.viper.FullPerm(self.to_position(node),
                                       self.noinfo())
        raise UnsupportedException(node)

    def translate_perm_BinOp(self, node: ast.BinOp) -> Expr:
        if isinstance(node.op, ast.Div):
            leftstmt, left = self.translate_expr(node.left)
            rightstmt, right = self.translate_expr(node.right)
            if len(leftstmt) != 0 or len(rightstmt) != 0:
                raise InvalidProgramException(node, 'purity.violated')
            return self.viper.FractionalPerm(left, right,
                                             self.to_position(node),
                                             self.noinfo())
        raise UnsupportedException(node)

    def translate_generic(self, node: ast.AST) -> None:
        """
        Visitor that is used if no other visitor is implemented.
        Simply raises an exception.
        """
        raise UnsupportedException(node)

    def translate_Assign(self, node: ast.Assign) -> StmtAndExpr:
        if len(node.targets) != 1:
            raise UnsupportedException(node)
        target = self.currentfunction.get_variable(node.targets[0].id).decl
        stmt, expr = self.translate_expr(node.value)
        return (stmt, LetWrapper(target, expr, node))

    def translate_contract(self, node: ast.AST) -> Expr:
        """
        Generic visitor function for translating contracts (i.e. calls to
        contract functions)
        """
        method = 'translate_contract_' + node.__class__.__name__
        visitor = getattr(self, method, self.translate_generic)
        return visitor(node)

    def translate_stmt(self, node: ast.AST) -> List[Stmt]:
        """
        Generic visitor function for translating statements
        """
        method = 'translate_stmt_' + node.__class__.__name__
        visitor = getattr(self, method, self.translate_generic)
        return visitor(node)

    def translate_contract_Call(self,
                                node: ast.Call) -> Expr:
        if self.get_func_name(node) in CONTRACT_WRAPPER_FUNCS:
            stmt, res = self.translate_expr(node.args[0])
            if len(stmt) != 0:
                raise InvalidProgramException(node, 'purity.violated')
            return res
        else:
            raise UnsupportedException(node)

    def translate_contract_Expr(self,
                                node: ast.Expr) -> Expr:
        if isinstance(node.value, ast.Call):
            return self.translate_contract(node.value)
        else:
            raise UnsupportedException(node)

    def translate_Num(self, node: ast.Num) -> StmtAndExpr:
        return ([], self.viper.IntLit(node.n, self.to_position(node),
                                      self.noinfo()))

    def translate_Return(self, node: ast.Return) -> StmtAndExpr:
        return self.translate_expr(node.value)

    def translate_contractfunc_call(self, node: ast.Call) -> StmtAndExpr:
        """
        Translates calls to contract functions like Result() and Acc()
        """
        if self.get_func_name(node) == "Result":
            assert len(node.args) == 0
            type = self.currentfunction.type
            if not self.currentfunction.pure:
                return (
                    [], self.viper.LocalVar('_res', self.translate_type(type),
                                            self.noposition(),
                                            self.noinfo()))
            else:
                return ([], self.viper.Result(self.translate_type(type),
                                              self.to_position(node),
                                              self.noinfo()))
        elif self.get_func_name(node) == 'Acc':
            stmt, fieldacc = self.translate_expr(node.args[0])
            if len(stmt) != 0:
                raise InvalidProgramException(node, 'purity.violated')
            if len(node.args) == 1:
                perm = self.viper.FullPerm(self.to_position(node),
                                           self.noinfo())
            elif len(node.args) == 2:
                perm = self.translate_perm(node.args[1])
            else:
                raise UnsupportedException(node)
            pred = self.viper.FieldAccessPredicate(fieldacc, perm,
                                                   self.to_position(node),
                                                   self.noinfo())
            return ([], pred)
        elif self.get_func_name(node) == 'Implies':
            assert len(node.args) == 2
            condstmt, cond = self.translate_expr(node.args[0])
            thenstmt, then = self.translate_expr(node.args[1])
            implication = self.viper.Implies(cond, then,
                                             self.to_position(node),
                                             self.noinfo())
            return (condstmt + thenstmt, implication)
        elif self.get_func_name(node) == 'Old':
            assert len(node.args) == 1
            stmt, exp = self.translate_expr(node.args[0])
            res = self.viper.Old(exp, self.to_position(node), self.noinfo())
            return (stmt, res)
        else:
            raise UnsupportedException(node)

    def translate_Call(self, node: ast.Call) -> StmtAndExpr:
        if self.get_func_name(node) in CONTRACT_WRAPPER_FUNCS:
            raise ValueError('Contract call translated as normal call.')
        elif self.get_func_name(node) in CONTRACT_FUNCS:
            return self.translate_contractfunc_call(node)
        elif self.get_func_name(node) == 'isinstance':
            assert len(node.args) == 2
            assert isinstance(node.args[1], ast.Name)
            stmt, obj = self.translate_expr(node.args[0])
            clazz = self.program.classes[node.args[1].id]
            return (stmt, self.hastype(obj, clazz))
        args = []
        formalargs = []
        argstmts = []
        for arg in node.args:
            argstmt, argexpr = self.translate_expr(arg)
            argstmts = argstmts + argstmt
            args.append(argexpr)
        name = self.get_func_name(node)
        if name in self.program.classes:
            # this is a constructor call
            targetClass = self.program.classes[name]
            targets = []
            resultVar = self.currentfunction.create_variable(name + '_res',
                                                             targetClass,
                                                             self)
            targets.append(resultVar.ref)
            target = targetClass.get_method('__init__')
            if target is not None:
                if len(target.declaredexceptions) > 0:
                    errorVar = self.currentfunction.create_variable(
                        target.name + '_err',
                        self.program.classes['Exception'], self)
                    targets.append(errorVar.ref)
            call = [self.viper.MethodCall(targetClass.silname + '___init__',
                                          args, targets,
                                          self.to_position(node),
                                          self.noinfo())]
            if target is not None and len(target.declaredexceptions) > 0:
                call = call + self.create_exception_catchers(errorVar,
                                                             self.currentfunction.handlers,
                                                             node)
            return (argstmts + call, resultVar.ref)
        if isinstance(node.func, ast.Attribute):
            # method called on an object
            recstmt, receiver = self.translate_expr(node.func.value)
            receiverclass = self.get_type(node.func.value)
            target = receiverclass.get_func_or_method(node.func.attr)
            receiverclass = target.clazz
            argstmts = recstmt + argstmts
            args = [receiver] + args
        else:
            # global function/method called
            receiverclass = None
            target = self.program.get_func_or_method(name)
        for arg in target.args:
            formalargs.append(target.args[arg].decl)
        targetname = target.silname
        if receiverclass is not None:
            targetname = receiverclass.silname + '_' + targetname
        if target.pure:
            type = self.translate_type(target.type)
            return (argstmts, self.viper.FuncApp(targetname, args,
                                                 self.to_position(
                                                     node),
                                                 self.noinfo(),
                                                 type,
                                                 formalargs))
        else:
            targets = []
            resultvar = None
            if self.currentfunction is None:
                if self.currentclass is None:
                    # global variable
                    raise InvalidProgramException(node, 'purity.violated')
                else:
                    # static field
                    raise UnsupportedException(node)
            if target.type is not None:
                resultvar = self.currentfunction.create_variable(
                    target.name + '_res', target.type, self)
                targets.append(resultvar.ref)
            if len(target.declaredexceptions) > 0:
                errorvar = self.currentfunction.create_variable(
                    target.name + '_err',
                    self.program.classes['Exception'], self)
                targets.append(errorvar.ref)
            call = [self.viper.MethodCall(targetname, args, targets,
                                          self.to_position(node),
                                          self.noinfo())]
            if len(target.declaredexceptions) > 0:
                call = call + self.create_exception_catchers(errorvar,
                                                             self.currentfunction.handlers,
                                                             node)
            return (
                argstmts + call, resultvar.ref if resultvar else None)

    def create_exception_catchers(self, var: PythonVar,
                                  handlers: List[PythonExceptionHandler],
                                  call: ast.Call) -> List[Stmt]:
        """
        Creates the code for catching an exception, i.e. redirecting control
        flow to the handlers or giving the exception to the caller function
        """
        cases = []
        position = self.to_position(call)
        errVar = self.viper.LocalVar('_err', self.viper.Ref,
                                     self.noposition(),
                                     self.noinfo())
        if len(self.currentfunction.declaredexceptions) > 0:
            assignerror = self.viper.LocalVarAssign(errVar, var.ref, position,
                                                    self.noinfo())
            gotoend = self.viper.Goto('__end', position,
                                      self.noinfo())
            uncaughtoption = self.translate_block([assignerror, gotoend],
                                                  position,
                                                  self.noinfo())
        else:
            uncaughtoption = self.viper.Exhale(
                self.viper.FalseLit(position, self.noinfo()), position,
                self.noinfo())
        for handler in handlers:
            if self.contains_stmt(handler.region, call):
                condition = self.varhastype(var.silname, handler.type)
                goto = self.viper.Goto(handler.name,
                                       self.to_position(handler.node),
                                       self.noinfo())
                cases.insert(0, (condition, goto))
        result = None
        for cond, goto in cases:
            if result is None:
                result = self.viper.If(cond, goto,
                                       uncaughtoption,
                                       self.to_position(handler.node),
                                       self.noinfo())
            else:
                result = self.viper.If(cond, goto, result)
        if result is None:
            errcase = uncaughtoption
        else:
            errcase = result
        errnotnull = self.viper.NeCmp(var.ref,
                                      self.viper.NullLit(self.noposition(),
                                                         self.noinfo()),
                                      position, self.noinfo())
        emptyblock = self.translate_block([], self.noposition(),
                                          self.noinfo())
        errcheck = self.viper.If(errnotnull, errcase, emptyblock,
                                 position,
                                 self.noinfo())
        return [errcheck]

    def contains_stmt(self, container: Any, contained: ast.AST) -> bool:
        """
        Checks if contained a part of the partial AST whose root is container
        """
        if container is contained:
            return True
        if isinstance(container, list):
            for stmt in container:
                if self.contains_stmt(stmt, contained):
                    return True
            return False
        elif isinstance(container, ast.AST):
            for field in container._fields:
                if self.contains_stmt(getattr(container, field), contained):
                    return True
            return False
        else:
            return False

    def translate_Expr(self, node: ast.Expr) -> StmtAndExpr:
        return self.translate_expr(node.value)

    def translate_Name(self, node: ast.Name) -> StmtAndExpr:
        if node.id in self.program.global_vars:
            var = self.program.global_vars[node.id]
            type = self.translate_type(var.clazz)
            funcapp = self.viper.FuncApp(var.silname, [],
                                         self.to_position(node),
                                         self.noinfo(), type, [])
            return ([], funcapp)
        else:
            return ([], self.currentfunction.get_variable(node.id).ref)

    def translate_Attribute(self, node: ast.Attribute) -> StmtAndExpr:
        stmt, receiver = self.translate_expr(node.value)
        rectype = self.get_type(node.value)
        result = rectype.get_field(node.attr)
        while result.inherited is not None:
            result = result.inherited
        if result.is_mangled():
            if result.clazz is not self.currentclass:
                raise InvalidProgramException(node, 'private.field.access')
        return (stmt, self.viper.FieldAccess(receiver, result.field,
                                             self.to_position(node),
                                             self.noinfo()))

    def get_type(self, node: ast.AST) -> PythonClass:
        """
        Returns the type of the expression represented by node as a PythonClass
        """
        if isinstance(node, ast.Attribute):
            receiver = self.get_type(node.value)
            return receiver.get_field(node.attr).type
        elif isinstance(node, ast.Name):
            return self.currentfunction.get_variable(node.id).clazz
        elif isinstance(node, ast.Call):

            if isinstance(node.func, ast.Name):
                if node.func.id in CONTRACT_FUNCS:
                    if node.func.id == 'Result':
                        return self.currentfunction.type
                    else:
                        raise UnsupportedException(node)
                if node.func.id in self.program.classes:
                    return self.program.classes[node.func.id]
                elif self.program.get_func_or_method(node.func.id) is not None:
                    return self.program.get_func_or_method(node.func.id).type
            elif isinstance(node.func, ast.Attribute):
                rectype = self.get_type(node.func.value)
                return rectype.get_func_or_method(node.func.attr).type
        else:
            raise UnsupportedException(node)

    def translate_UnaryOp(self, node: ast.UnaryOp) -> StmtAndExpr:
        stmt, expr = self.translate_expr(node.operand)
        if isinstance(node.op, ast.Not):
            return (stmt, self.viper.Not(expr, self.to_position(node),
                                         self.noinfo()))
        elif isinstance(node.op, ast.USub):
            return (stmt, self.viper.Minus(expr, self.to_position(node),
                                           self.noinfo()))
        else:
            raise UnsupportedException(node)

    def translate_IfExp(self, node: ast.IfExp) -> StmtAndExpr:
        position = self.to_position(node)
        condstmt, cond = self.translate_expr(node.test)
        thenstmt, then = self.translate_expr(node.body)
        elsstmt, els = self.translate_expr(node.orelse)
        if len(thenstmt) + len(elsstmt) > 0:
            thenblock = self.translate_block(thenstmt, position, self.noinfo())
            elsblock = self.translate_block(elsstmt, position, self.noinfo())
            ifstmt = self.viper.If(cond, thenblock, elsblock, position,
                                   self.noinfo())
            bodystmt = [ifstmt]
        else:
            bodystmt = []
        condexp = self.viper.CondExp(cond, then, els,
                                     self.to_position(node),
                                     self.noinfo())
        return (condstmt + bodystmt, condexp)

    def translate_BinOp(self, node: ast.BinOp) -> StmtAndExpr:
        lstmt, left = self.translate_expr(node.left)
        rstmt, right = self.translate_expr(node.right)
        stmt = lstmt + rstmt
        if isinstance(node.op, ast.Add):
            return (stmt, self.viper.Add(left, right,
                                         self.to_position(node),
                                         self.noinfo()))
        elif isinstance(node.op, ast.Sub):
            return (stmt, self.viper.Sub(left, right,
                                         self.to_position(node),
                                         self.noinfo()))
        elif isinstance(node.op, ast.Mult):
            return (stmt, self.viper.Mul(left, right,
                                         self.to_position(node),
                                         self.noinfo()))
        elif isinstance(node.op, ast.FloorDiv):
            return (stmt, self.viper.Div(left, right,
                                         self.to_position(node),
                                         self.noinfo()))
        elif isinstance(node.op, ast.Mod):
            return (stmt, self.viper.Mod(left, right,
                                         self.to_position(node),
                                         self.noinfo()))
        else:
            raise UnsupportedException(node)

    def translate_Compare(self, node: ast.Compare) -> StmtAndExpr:
        if len(node.ops) != 1 or len(node.comparators) != 1:
            raise UnsupportedException(node)
        lstmt, left = self.translate_expr(node.left)
        rstmt, right = self.translate_expr(node.comparators[0])
        stmts = lstmt + rstmt
        if isinstance(node.ops[0], ast.Eq):
            return (stmts, self.viper.EqCmp(left, right,
                                            self.to_position(node),
                                            self.noinfo()))
        elif isinstance(node.ops[0], ast.Gt):
            return (stmts, self.viper.GtCmp(left, right,
                                            self.to_position(node),
                                            self.noinfo()))
        elif isinstance(node.ops[0], ast.GtE):
            return (stmts, self.viper.GeCmp(left, right,
                                            self.to_position(node),
                                            self.noinfo()))
        elif isinstance(node.ops[0], ast.Lt):
            return (stmts, self.viper.LtCmp(left, right,
                                            self.to_position(node),
                                            self.noinfo()))
        elif isinstance(node.ops[0], ast.LtE):
            return (stmts, self.viper.LeCmp(left, right,
                                            self.to_position(node),
                                            self.noinfo()))
        elif isinstance(node.ops[0], ast.NotEq):
            return (stmts, self.viper.NeCmp(left, right,
                                            self.to_position(node),
                                            self.noinfo()))
        else:
            raise UnsupportedException(node)

    def translate_NameConstant(self,
                               node: ast.NameConstant) -> StmtAndExpr:
        if node.value is True:
            return ([], self.viper.TrueLit(self.to_position(node),
                                           self.noinfo()))
        elif node.value is False:
            return ([], self.viper.FalseLit(self.to_position(node),
                                            self.noinfo()))
        elif node.value is None:
            return (
            [], self.viper.NullLit(self.to_position(node), self.noinfo()))
        else:
            raise UnsupportedException(node)

    def translate_BoolOp(self, node: ast.BoolOp) -> StmtAndExpr:
        if len(node.values) != 2:
            raise UnsupportedException(node)
        position = self.to_position(node)
        lstmt, left = self.translate_expr(node.values[0])
        rstmt, right = self.translate_expr(node.values[1])
        if len(lstmt) + len(rstmt) > 0:
            cond = left
            if isinstance(node.op, ast.Or):
                cond = self.viper.Not(cond, position, self.noinfo())
            thenblock = self.translate_block(rstmt, position, self.noinfo())
            elsblock = self.translate_block([], position, self.noinfo())
            ifstmt = self.viper.If(cond, thenblock, elsblock, position,
                                   self.noinfo())
            stmt = lstmt + [ifstmt]
        else:
            stmt = []
        if isinstance(node.op, ast.And):
            return (stmt, self.viper.And(left,
                                         right,
                                         self.to_position(node),
                                         self.noinfo()))
        elif isinstance(node.op, ast.Or):
            return (stmt, self.viper.Or(left,
                                        right,
                                        self.to_position(node),
                                        self.noinfo()))
        else:
            raise UnsupportedException(node)

    def translate_stmt_AugAssign(self,
                                 node: ast.AugAssign) -> List[Stmt]:
        lstmt, lhs = self.translate_expr(node.target)
        if len(lstmt) > 0:
            raise InvalidProgramException(node, 'purity.violated')
        rstmt, rhs = self.translate_expr(node.value)
        if isinstance(node.op, ast.Add):
            newval = self.viper.Add(lhs, rhs,
                                    self.to_position(node),
                                    self.noinfo())
        elif isinstance(node.op, ast.Sub):
            newval = self.viper.Sub(lhs, rhs,
                                    self.to_position(node),
                                    self.noinfo())
        else:
            raise UnsupportedException(node)
        position = self.to_position(node)
        if isinstance(node.target, ast.Name):
            assign = self.viper.LocalVarAssign(lhs, newval, position,
                                               self.noinfo())
        elif isinstance(node.target, ast.Attribute):
            assign = self.viper.FieldAssign(lhs, newval, position,
                                            self.noinfo())
        return rstmt + [assign]

    def translate_stmt_Try(self, node: ast.Try) -> List[Stmt]:
        body = flatten([self.translate_stmt(stmt) for stmt in node.body])
        endlabel = self.viper.Label('post_' + node.silname,
                                    self.to_position(node),
                                    self.noinfo())
        return body + [endlabel]

    def translate_stmt_Raise(self, node: ast.Raise) -> List[Stmt]:
        var = self.currentfunction.create_variable('raise',
                                                   self.get_type(node.exc),
                                                   self)
        stmt, exception = self.translate_expr(node.exc)
        assignment = self.viper.LocalVarAssign(var.ref, exception,
                                               self.to_position(node),
                                               self.noinfo())
        catchers = self.create_exception_catchers(var,
                                                  self.currentfunction.handlers,
                                                  node)
        return stmt + [assignment] + catchers

    def translate_stmt_Call(self, node: ast.Call) -> List[Stmt]:
        if self.get_func_name(node) == 'Assert':
            assert len(node.args) == 1
            stmt, expr = self.translate_expr(node.args[0])
            assertion = self.viper.Assert(expr, self.to_position(node),
                                          self.noinfo())
            return stmt + [assertion]
        else:
            stmt, expr = self.translate_Call(node)
            if len(stmt) == 0:
                raise InvalidProgramException(node, 'no.effect')
            return stmt

    def translate_stmt_Expr(self, node: ast.Expr) -> List[Stmt]:
        if isinstance(node.value, ast.Call):
            return self.translate_stmt(node.value)
        else:
            raise UnsupportedException(node)

    def translate_stmt_If(self, node: ast.If) -> List[Stmt]:
        condstmt, cond = self.translate_expr(node.test)
        thnbody = flatten([self.translate_stmt(stmt) for stmt in node.body])
        thn = self.translate_block(thnbody,
                                   self.to_position(node),
                                   self.noinfo())
        elsbody = flatten([self.translate_stmt(stmt) for stmt in node.orelse])
        els = self.translate_block(
            elsbody,
            self.to_position(node), self.noinfo())
        return condstmt + [self.viper.If(cond, thn, els, self.to_position(node),
                                         self.noinfo())]

    def translate_stmt_Assign(self, node: ast.Assign) -> List[Stmt]:
        if len(node.targets) != 1:
            raise UnsupportedException(node)
        target = node.targets[0]
        lhsstmt, var = self.translate_expr(target)
        assignment = self.viper.LocalVarAssign if isinstance(target,
                                                             ast.Name) else self.viper.FieldAssign
        rhsstmt, rhs = self.translate_expr(node.value)
        assign = assignment(var,
                            rhs, self.to_position(node),
                            self.noinfo())
        return lhsstmt + rhsstmt + [assign]

    def translate_stmt_While(self, node: ast.While) -> List[Stmt]:
        condstmt, cond = self.translate_expr(node.test)
        if len(condstmt) > 0:
            raise InvalidProgramException(node, 'purity.violated')
        invariants = []
        locals = []
        bodyindex = 0
        while self.is_invariant(node.body[bodyindex]):
            invariants.append(self.translate_contract(node.body[bodyindex]))
            bodyindex += 1
        body = flatten(
            [self.translate_stmt(stmt) for stmt in node.body[bodyindex:]])
        body = self.translate_block(body, self.to_position(node),
                                    self.noinfo())
        return [self.viper.While(cond, invariants, locals, body,
                                 self.to_position(node),
                                 self.noinfo())]

    def translate_stmt_Return(self,
                              node: ast.Return) -> List[Stmt]:
        type = self.currentfunction.type
        rhsstmt, rhs = self.translate_expr(node.value)
        assign = self.viper.LocalVarAssign(
            self.viper.LocalVar('_res', self.translate_type(type),
                                self.noposition(), self.noinfo()),
            rhs, self.to_position(node),
            self.noinfo())
        jmp_to_end = self.viper.Goto("__end", self.to_position(node),
                                     self.noinfo())
        return rhsstmt + [assign, jmp_to_end]

    def get_func_name(self, stmt: ast.AST) -> Optional[str]:
        """
        Checks if stmt is a function call and returns its name if it is, None
        otherwise.
        """
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            call = stmt.value
        elif isinstance(stmt, ast.Call):
            call = stmt
        else:
            return None
        if isinstance(call.func, ast.Name):
            return call.func.id
        elif isinstance(call.func, ast.Attribute):
            return call.func.attr
        else:
            raise UnsupportedException(stmt)

    def is_pre(self, stmt: ast.AST) -> bool:
        return self.get_func_name(stmt) == 'Requires'

    def is_post(self, stmt: ast.AST) -> bool:
        return self.get_func_name(stmt) == 'Ensures'

    def is_exception_decl(self, stmt: ast.AST) -> bool:
        return self.get_func_name(stmt) == 'Exsures'

    def is_invariant(self, stmt: ast.AST) -> bool:
        return self.get_func_name(stmt) == 'Invariant'

    def is_pure(self, func) -> bool:
        return (len(func.decorator_list) == 1
                and func.decorator_list[0].id == 'Pure')

    def is_predicate(self, func) -> bool:
        return len(func.decorator_list) == 1 and func.decorator_list[
                                                     0].id == 'Predicate'

    def translate_block(self, stmtlist: List['silver.ast.Stmt'],
                        position: 'silver.ast.Position',
                        info: 'silver.ast.Info') -> Stmt:
        """
        Wraps a (Python) list of (Viper) statements into a Viper block
        """
        body = []
        for stmt in stmtlist:
            body.append(stmt)
        return self.viper.Seqn(body, position, info)

    def create_type(self, clazz: PythonClass) -> Tuple['silver.ast.DomainFunc',
                                                     'silver.ast.DomainAxiom']:
        """
        Creates the type domain function and subtype axiom for this class
        """
        supertype = clazz.superclass.silname if clazz.superclass is not None else 'object'
        position = self.to_position(clazz.node)
        info = self.noinfo()
        return (self.create_type_function(clazz.silname, position, info),
                self.create_subtype_axiom(clazz.silname, supertype, position,
                                          info))

    def create_type_function(self, name: str, position,
                             info) -> 'silver.ast.DomainFunc':
        return self.viper.DomainFunc(name, [], self.typetype(), True, position,
                                     info)

    def typetype(self) -> 'silver.ast.DomainType':
        """
        Creates a reference to the domain type we use for the Python types
        """
        return self.viper.DomainType(self.typedomain, {}, [])

    def create_subtype_axiom(self, type, supertype, position,
                             info) -> 'silver.ast.DomainAxiom':
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
        body = self.viper.DomainFuncApp('issubtype', [typefunc, supertypefunc],
                                        {},
                                        self.viper.Bool, [typevar, typevar],
                                        position, info)
        return self.viper.DomainAxiom('subtype_' + type, body, position, info)

    def create_transitivity_axiom(self) -> 'silver.ast.DomainAxiom':
        """
        Creates the transitivity axiom for the PyType domain
        """
        argsub = self.viper.LocalVarDecl('sub', self.typetype(),
                                         self.noposition(),
                                         self.noinfo())
        varsub = self.viper.LocalVar('sub', self.typetype(),
                                     self.noposition(), self.noinfo())
        argmiddle = self.viper.LocalVarDecl('middle', self.typetype(),
                                            self.noposition(),
                                            self.noinfo())
        varmiddle = self.viper.LocalVar('middle', self.typetype(),
                                        self.noposition(),
                                        self.noinfo())
        argsuper = self.viper.LocalVarDecl('super', self.typetype(),
                                           self.noposition(),
                                           self.noinfo())
        varsuper = self.viper.LocalVar('super', self.typetype(),
                                       self.noposition(), self.noinfo())

        submiddle = self.viper.DomainFuncApp('issubtype', [varsub, varmiddle],
                                             {},
                                             self.viper.Bool,
                                             [varsub, varmiddle],
                                             self.noposition(),
                                             self.noinfo())
        middlesuper = self.viper.DomainFuncApp('issubtype',
                                               [varmiddle, varsuper], {},
                                               self.viper.Bool,
                                               [varmiddle, varsuper],
                                               self.noposition(),
                                               self.noinfo())
        subsuper = self.viper.DomainFuncApp('issubtype', [varsub, varsuper], {},
                                            self.viper.Bool, [varsub, varsuper],
                                            self.noposition(),
                                            self.noinfo())
        implication = self.viper.Implies(
            self.viper.And(submiddle, middlesuper, self.noposition(),
                           self.noinfo()), subsuper, self.noposition(),
            self.noinfo())
        trigger = self.viper.Trigger([submiddle, middlesuper],
                                     self.noposition(), self.noinfo())
        body = self.viper.Forall([argsub, argmiddle, argsuper], [trigger],
                                 implication, self.noposition(),
                                 self.noinfo())
        return self.viper.DomainAxiom('issubtype_transitivity', body,
                                      self.noposition(), self.noinfo())

    def create_reflexivity_axiom(self) -> 'silver.ast.DomainAxiom':
        """
        Creates the reflexivity axiom for the PyType domain
        """
        arg = self.viper.LocalVarDecl('type', self.typetype(),
                                      self.noposition(), self.noinfo())
        var = self.viper.LocalVar('type', self.typetype(),
                                  self.noposition(), self.noinfo())
        reflexivesubtype = self.viper.DomainFuncApp('issubtype', [var, var], {},
                                                    self.viper.Bool, [var, var],
                                                    self.noposition(),
                                                    self.noinfo())
        triggerexp = reflexivesubtype
        trigger = self.viper.Trigger([triggerexp], self.noposition(),
                                     self.noinfo())
        body = self.viper.Forall([arg], [trigger], reflexivesubtype,
                                 self.noposition(), self.noinfo())
        return self.viper.DomainAxiom('issubtype_reflexivity', body,
                                      self.noposition(), self.noinfo())

    def typeof_func(self) -> 'silver.ast.DomainFunc':
        """
        Creates the typeof domain function
        """
        objvar = self.viper.LocalVarDecl('obj', self.viper.Ref,
                                         self.noposition(),
                                         self.noinfo())
        return self.viper.DomainFunc('typeof', [objvar],
                                     self.typetype(), False,
                                     self.noposition(), self.noinfo())

    def issubtype_func(self) -> 'silver.ast.DomainFunc':
        """
        Creates the issubtype domain function
        """
        subvar = self.viper.LocalVarDecl('sub', self.typetype(),
                                         self.noposition(),
                                         self.noinfo())
        supervar = self.viper.LocalVarDecl('super', self.typetype(),
                                           self.noposition(),
                                           self.noinfo())
        return self.viper.DomainFunc('issubtype', [subvar, supervar],
                                     self.viper.Bool, False,
                                     self.noposition(), self.noinfo())

    def varhastype(self, name: str,
                   type: PythonClass) -> 'silver.ast.DomainFuncApp':
        """
        Creates an expression checking if the var with the given name
        is of the given type
        """
        objvar = self.viper.LocalVar(name, self.viper.Ref,
                                     self.noposition(),
                                     self.noinfo())
        return self.hastype(objvar, type)

    def hastype(self, lhs: Expr, type: PythonClass):
        """
        Creates an expression checking if the given lhs expression
        is of the given type
        """
        typefunc = self.viper.DomainFuncApp('typeof', [lhs], {},
                                            self.typetype(), [lhs],
                                            self.noposition(),
                                            self.noinfo())
        supertypefunc = self.viper.DomainFuncApp(type.silname, [], {},
                                                 self.typetype(), [],
                                                 self.noposition(),
                                                 self.noinfo())
        varsub = self.viper.LocalVar('sub', self.typetype(),
                                     self.noposition(), self.noinfo())
        varsuper = self.viper.LocalVar('super', self.typetype(),
                                       self.noposition(), self.noinfo())
        subtypefunc = self.viper.DomainFuncApp('issubtype',
                                               [typefunc, supertypefunc], {},
                                               self.viper.Bool,
                                               [varsub, varsuper],
                                               self.noposition(),
                                               self.noinfo())
        return subtypefunc

    def translate_pythonvar_decl(self,
                                 var: PythonVar) -> 'silver.ast.LocalVarDecl':
        """
        Creates a variable declaration for the given PythonVar.
        To be called during the processing phase by the Analyzer.
        """
        return self.viper.LocalVarDecl(var.silname,
                                       self.translate_type(var.clazz),
                                       self.noposition(), self.noinfo())

    def translate_pythonvar_ref(self, var: PythonVar) -> Expr:
        """
        Creates a variable reference for the given PythonVar.
        To be called during the processing phase by the Analyzer.
        """
        return self.viper.LocalVar(var.silname,
                                   self.translate_type(var.clazz),
                                   self.noposition(), self.noinfo())

    def translate_type(self, clazz: PythonClass) -> 'silver.ast.Type':
        """
        Translates the given type to the corresponding Viper type (Int, Ref, ..)
        """
        if 'builtins.' + clazz.name in self.builtins:
            return self.builtins['builtins.' + clazz.name]
        else:
            return self.viper.Ref

    def get_parameter_typeof(self,
                             param: PythonVar) -> 'silver.ast.DomainFuncApp':
        return self.varhastype(param.silname, param.clazz)

    def translate_field(self, field: PythonField) -> 'silver.ast.Field':
        return self.viper.Field(field.clazz.silname + '_' + field.silname,
                                self.translate_type(field.type),
                                self.to_position(field.node),
                                self.noinfo())

    def get_body_start_index(self, statements: List[ast.AST]) -> int:
        """
        Returns the index of the first statement that is not a method contract
        """
        bodyindex = 0
        while self.is_pre(statements[bodyindex]):
            bodyindex += 1
        while self.is_post(statements[bodyindex]):
            bodyindex += 1
        while self.is_exception_decl(statements[bodyindex]):
            bodyindex += 1
        return bodyindex

    def translate_function(self, func: PythonMethod) -> 'silver.ast.Function':
        """
        Translates a pure Python function (may or not belong to a class) to a
        Viper function
        """
        oldfunction = self.currentfunction
        self.currentfunction = func
        type = self.translate_type(func.type)
        args = []
        for arg in func.args:
            args.append(func.args[arg].decl)
        if len(func.declaredexceptions) != 0:
            raise InvalidProgramException(func.node,
                                          'function.throws.exception')
        # create preconditions
        pres = []
        for pre in func.precondition:
            stmt, expr = self.translate_expr(pre)
            if len(stmt) != 0:
                raise InvalidProgramException(pre, 'purity.violated')
            pres.append(expr)
        # create postconditions
        posts = []
        for post in func.postcondition:
            stmt, expr = self.translate_expr(post)
            if len(stmt) != 0:
                raise InvalidProgramException(post, 'purity.violated')
            posts.append(expr)
        # create typeof preconditions
        for arg in func.args:
            if not func.args[arg].clazz.name in PRIMITIVES:
                pres.append(self.get_parameter_typeof(func.args[arg]))
        statements = func.node.body
        bodyindex = self.get_body_start_index(statements)
        # translate body
        body = self.translate_exprs(statements[bodyindex:], func)
        self.currentfunction = oldfunction
        name = func.silname
        if func.clazz is not None:
            name = func.clazz.silname + '_' + name
        return self.viper.Function(name, args, type, pres, posts, body,
                                   self.noposition(), self.noinfo())

    def translate_handler(self, handler: PythonExceptionHandler) -> List[Stmt]:
        """
        Creates a code block representing an exception handler, to be put at
        the end of a Viper method
        """
        label = self.viper.Label(handler.name,
                                 self.to_position(handler.node),
                                 self.noinfo())
        body = []
        for stmt in handler.body:
            body += self.translate_stmt(stmt)
        bodyblock = self.translate_block(body,
                                         self.to_position(handler.node),
                                         self.noinfo())
        gotoend = self.viper.Goto('post_' + handler.tryname,
                                  self.to_position(handler.node),
                                  self.noinfo())
        return [label, bodyblock, gotoend]

    def extract_contract(self, method: PythonMethod, errorvarname: str,
                         isconstructor: bool) -> Tuple[List[Expr], List[Expr]]:
        """
        Extracts the pre and postcondition from a given method
        """
        errorvarref = self.viper.LocalVar(errorvarname, self.viper.Ref,
                                          self.noposition(),
                                          self.noinfo())
        # create preconditions
        pres = []
        for pre in method.precondition:
            stmt, expr = self.translate_expr(pre)
            if len(stmt) != 0:
                raise InvalidProgramException(pre, 'purity.violated')
            pres.append(expr)
        # create postconditions
        posts = []
        noerror = self.viper.EqCmp(errorvarref,
                                   self.viper.NullLit(self.noposition(),
                                                      self.noinfo()),
                                   self.noposition(), self.noinfo())
        error = self.viper.NeCmp(errorvarref,
                                 self.viper.NullLit(self.noposition(),
                                                    self.noinfo()),
                                 self.noposition(), self.noinfo())
        for post in method.postcondition:
            stmt, expr = self.translate_expr(post)
            if len(stmt) != 0:
                raise InvalidProgramException(post, 'purity.violated')
            if len(method.declaredexceptions) > 0:
                expr = self.viper.Implies(noerror, expr,
                                          self.to_position(post),
                                          self.noinfo())
            posts.append(expr)
        # create exceptional postconditions
        errorTypeConds = []
        errortypepos = self.to_position(method.node)
        for exception in method.declaredexceptions:
            oldpos = self.position
            if self.position is None:
                self.position = errortypepos
            hastype = self.varhastype('_err', self.program.classes[exception])
            errorTypeConds.append(hastype)
            self.position = oldpos
            condition = self.viper.And(error, hastype, self.noposition(),
                                       self.noinfo())
            for post in method.declaredexceptions[exception]:
                stmt, expr = self.translate_expr(post)
                if len(stmt) != 0:
                    raise InvalidProgramException(post, 'purity.violated')
                expr = self.viper.Implies(condition, expr,
                                          self.to_position(post),
                                          self.noinfo())
                posts.append(expr)

        errorTypeCond = None
        for type in errorTypeConds:
            if errorTypeCond is None:
                errorTypeCond = type
            else:
                errorTypeCond = self.viper.Or(errorTypeCond, type,
                                              errortypepos,
                                              self.noinfo())
        if errorTypeCond is not None:
            posts.append(self.viper.Implies(error, errorTypeCond,
                                            self.to_position(post),
                                            self.noinfo()))
        # create typeof preconditions
        for arg in method.args:
            if not (method.args[arg].clazz.name in PRIMITIVES
                    or (isconstructor and arg == next(iter(method.args)))):
                pres.append(self.get_parameter_typeof(method.args[arg]))
        return (pres, posts)

    def to_position(self, node):
        """
        Extracts the position from a node.
        If self.position is set to override the actual position, returns that.
        """
        if self.position is not None:
            return self.position
        else:
            return self.viper.to_position(node)

    def noposition(self):
        return self.to_position(None)

    def to_info(self, comments):
        """
        Wraps the given comments into an Info object.
        If self.info is set to override the given info, returns that.
        """
        if self.info is not None:
            return self.info
        if len(comments) > 0:
            return self.viper.SimpleInfo(comments)
        else:
            return self.viper.NoInfo

    def noinfo(self):
        return self.to_info([])

    def create_subtyping_check(self,
                               method: PythonMethod) -> 'silver.ast.Callable':
        """
        Creates a Viper function/method with the contract of the overridden
        function which calls the overriding function, to check behavioural
        subtyping.
        """
        oldfunction = self.currentfunction
        self.currentfunction = method.overrides
        assert self.position is None
        self.position = self.viper.to_position(method.node)
        self.info = self.viper.SimpleInfo(['behavioural.subtyping'])
        if len(method.args) != len(method.overrides.args):
            raise InvalidProgramException(method.node, 'invalid.override')
        for exc in method.declaredexceptions:
            excclass = self.program.classes[exc]
            allowed = False
            for superexc in method.overrides.declaredexceptions:
                superexcclass = self.program.classes[superexc]
                if excclass.issubtype(superexcclass):
                    allowed = True
                    break
            if not allowed:
                raise InvalidProgramException(method.node, 'invalid.override')
                # TODO check if exceptional postconditions imply super postconds
        params = []
        args = []
        type = self.translate_type(method.type)
        mname = method.silname + '_subtyping'
        pres, posts = self.extract_contract(method.overrides, '_err', False)
        if method.clazz:
            mname = method.clazz.silname + '_' + mname
        for arg in method.overrides.args:
            params.append(method.overrides.args[arg].decl)
            args.append(method.overrides.args[arg].ref)
        selfarg = method.overrides.args[next(iter(method.overrides.args))]
        hassubtype = self.varhastype(selfarg.silname, method.clazz)
        calledname = method.clazz.silname + '_' + method.silname
        if method.pure:
            if not method.overrides.pure:
                raise InvalidProgramException(method.node, 'invalid.override')
            pres = pres + [hassubtype]
            formalargs = []
            for arg in method.args:
                formalargs.append(method.args[arg].decl)
            funcapp = self.viper.FuncApp(calledname, args, self.noposition(),
                                         self.noinfo(), type, formalargs)
            self.currentfunction = oldfunction
            result = self.viper.Function(mname, params, type, pres, posts,
                                         funcapp, self.noposition(),
                                         self.noinfo())
            self.position = None
            self.info = None
            return result
        else:
            if method.overrides.pure:
                raise InvalidProgramException(method.node, 'invalid.override')
            results = []
            targets = []
            resultvardecl = self.viper.LocalVarDecl('_res', type,
                                                    self.to_position(
                                                        method.node),
                                                    self.noinfo())
            resultvarref = self.viper.LocalVar('_res', type,
                                               self.to_position(
                                                   method.node),
                                               self.noinfo())
            results.append(resultvardecl)
            targets.append(resultvarref)
            errorvardecl = self.viper.LocalVarDecl('_err', self.viper.Ref,
                                                   self.noposition(),
                                                   self.noinfo())
            errorvarref = self.viper.LocalVar('_err', self.viper.Ref,
                                              self.noposition(),
                                              self.noinfo())
            if len(method.overrides.declaredexceptions) > 0:
                results.append(errorvardecl)
            if len(method.declaredexceptions) > 0:
                targets.append(errorvarref)
            call = self.viper.MethodCall(calledname, args, targets,
                                         self.noposition(),
                                         self.noinfo())
            subtypeassume = self.viper.Inhale(hassubtype, self.noposition(),
                                              self.noinfo())
            body = [subtypeassume, call]
            bodyblock = self.translate_block(body, self.noposition(),
                                             self.noinfo())
            self.currentfunction = oldfunction
            result = self.viper.Method(mname, params, results, pres, posts, [],
                                       bodyblock, self.noposition(),
                                       self.noinfo())
            self.position = None
            self.info = None
            return result

    def translate_method(self, method: PythonMethod) -> 'silver.ast.Method':
        """
        Translates an impure Python function (may or not belong to a class) to
        a Viper method
        """
        oldfunction = self.currentfunction
        self.currentfunction = method
        results = []
        if method.type is not None:
            type = self.translate_type(method.type)
            results.append(self.viper.LocalVarDecl('_res', type,
                                                   self.to_position(
                                                       method.node),
                                                   self.noinfo()))
        errorvardecl = self.viper.LocalVarDecl('_err', self.viper.Ref,
                                               self.noposition(),
                                               self.noinfo())
        errorvarref = self.viper.LocalVar('_err', self.viper.Ref,
                                          self.noposition(),
                                          self.noinfo())
        pres, posts = self.extract_contract(method, '_err', False)
        if len(method.declaredexceptions) > 0:
            results.append(errorvardecl)
        args = []
        for arg in method.args:
            args.append(method.args[arg].decl)

        statements = method.node.body
        bodyindex = self.get_body_start_index(statements)
        # translate body
        body = []
        if len(method.declaredexceptions) > 0:
            body.append(self.viper.LocalVarAssign(errorvarref,
                                                  self.viper.NullLit(
                                                      self.noposition(),
                                                      self.noinfo()),
                                                  self.noposition(),
                                                  self.noinfo()))
        body += flatten(
            [self.translate_stmt(stmt) for stmt in
             method.node.body[bodyindex:]])
        for handler in method.handlers:
            body += self.translate_handler(handler)
        locals = []
        for local in method.locals:
            locals.append(method.locals[local].decl)
        body += [self.viper.Label("__end", self.noposition(),
                                  self.noinfo())]
        bodyblock = self.translate_block(body,
                                         self.to_position(method.node),
                                         self.noinfo())
        self.currentfunction = oldfunction
        name = method.silname
        if method.clazz is not None:
            name = method.clazz.silname + '_' + name
        return self.viper.Method(name, args, results, pres, posts,
                                 locals, bodyblock,
                                 self.to_position(method.node),
                                 self.noinfo())

    def create_constructor(self, clazz: PythonClass) -> 'silver.ast.Method':
        """
        Creates a constructor method for the given class. Either creates a
        default constructor or translates the explicit one in the program.
        """
        method = clazz.get_method('__init__')
        name = method.silname if method is not None else '__init__'
        name = clazz.silname + '_' + name
        position = self.to_position(
            method.node) if method is not None else self.noposition()
        selfvarname = 'self' if method is None else method.args[
            next(iter(method.args))].silname
        args = []
        results = []
        results.append(self.viper.LocalVarDecl(selfvarname, self.viper.Ref,
                                               position,
                                               self.noinfo()))
        selfvar = self.viper.LocalVar(selfvarname, self.viper.Ref,
                                      self.noposition(), self.noinfo())
        locals = []
        body = []
        pres = []
        posts = []
        fields = []
        clz = clazz
        accs = []
        while clz is not None:
            for fieldname in clz.fields:
                field = clz.fields[fieldname]
                if field.inherited is None:
                    fields.append(field.field)
                    if method is None:
                        acc = self.viper.FieldAccess(selfvar, field.field,
                                                     position, self.noinfo())
                        accs.append(self.viper.FieldAccessPredicate(acc,
                                                                    self.viper.FullPerm(
                                                                        position,
                                                                        self.noinfo()),
                                                                    position,
                                                                    self.noinfo()))
            clz = clz.superclass

        body.append(self.viper.NewStmt(selfvar, fields, self.noposition(),
                                       self.noinfo()))
        resulthastype = self.varhastype(selfvarname, clazz)
        body.append(self.viper.Inhale(resulthastype, self.noposition(),
                                      self.noinfo()))
        notnull = self.viper.NeCmp(selfvar,
                                   self.viper.NullLit(self.noposition(),
                                                      self.noinfo()),
                                   self.noposition(),
                                   self.noinfo())
        posts.append(notnull)
        if method is not None:
            oldfunction = self.currentfunction
            self.currentfunction = method
            for arg in method.args:
                if arg == next(iter(method.args)):
                    continue
                args.append(method.args[arg].decl)
            errorvardecl = self.viper.LocalVarDecl('_err', self.viper.Ref,
                                                   self.noposition(),
                                                   self.noinfo())
            if len(method.declaredexceptions) > 0:
                results.append(errorvardecl)
            usrpres, usrposts = self.extract_contract(method, '_err', True)
            pres = pres + usrpres
            posts = posts + usrposts
            statements = method.node.body
            bodyindex = self.get_body_start_index(statements)
            body += flatten(
                [self.translate_stmt(stmt) for stmt in
                 method.node.body[bodyindex:]])
            body.append(self.viper.Goto('__end', self.noposition(),
                                        self.noinfo()))
            for handler in method.handlers:
                body += self.translate_handler(handler)
            for local in method.locals:
                locals.append(method.locals[local].decl)
            self.currentfunction = oldfunction

        body += [self.viper.Label("__end", self.noposition(),
                                  self.noinfo())]
        bodyblock = self.translate_block(body, position, self.noinfo())
        posts.append(resulthastype)
        posts += accs
        return self.viper.Method(name, args, results, pres, posts,
                                 locals, bodyblock,
                                 position,
                                 self.noinfo())

    def create_global_var_function(self,
                                   var: PythonVar) -> 'silver.ast.Function':
        """
        Creates a Viper function representing the given global variable
        """
        type = self.translate_type(var.clazz)
        if type == self.viper.Ref:
            raise UnsupportedException(var.node)
        position = self.to_position(var.node)
        posts = []
        result = self.viper.Result(type, position, self.noinfo())
        stmt, value = self.translate_expr(var.value)
        if len(stmt) != 0:
            raise InvalidProgramException('purity.violated', var.node)
        posts.append(
            self.viper.EqCmp(result, value, position, self.noinfo()))
        return self.viper.Function(var.silname, [], type, [], posts, None,
                                   self.to_position(var.node),
                                   self.noinfo())

    def translate_program(self, program: PythonProgram) -> 'silver.ast.Program':
        """
        Translates a PythonProgram created by the analyzer to a Viper program.
        """
        self.currentclass = None
        self.currentfunction = None
        self.program = program
        domains = []
        fields = []
        functions = []
        predicates = []
        methods = []

        typeof = self.typeof_func()
        issubtype = self.issubtype_func()
        objectfunc = self.create_type_function('object', self.noposition(),
                                               self.noinfo())
        typefuncs = [objectfunc, typeof, issubtype]
        typeaxioms = [self.create_reflexivity_axiom(),
                      self.create_transitivity_axiom()]

        for var in program.global_vars:
            functions.append(
                self.create_global_var_function(program.global_vars[var]))

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
            functions.append(
                self.translate_function(program.functions[function]))
        for method in program.methods:
            methods.append(self.translate_method(program.methods[method]))
        for clazzname in program.classes:
            if clazzname in PRIMITIVES:
                continue
            clazz = program.classes[clazzname]
            oldclass = self.currentclass
            self.currentclass = clazz
            funcs, axioms = self.create_type(clazz)
            typefuncs.append(funcs)
            typeaxioms.append(axioms)
            for funcname in clazz.functions:
                func = clazz.functions[funcname]
                functions.append(self.translate_function(func))
                if func.overrides:
                    functions.append(self.create_subtyping_check(func))
            for methodname in clazz.methods:
                if methodname != '__init__':
                    method = clazz.methods[methodname]
                    methods.append(self.translate_method(method))
                    if method.overrides:
                        methods.append(self.create_subtyping_check(method))
            methods.append(self.create_constructor(clazz))
            self.currentclass = oldclass

        domains.append(
            self.viper.Domain(self.typedomain, typefuncs, typeaxioms, [],
                              self.noposition(), self.noinfo()))

        prog = self.viper.Program(domains, fields, functions, predicates,
                                  methods, self.noposition(),
                                  self.noinfo())
        return prog
