import ast

from typing import Any, TypeVar, List, Tuple, Optional

from py2viper_contracts.contracts import (
    CONTRACT_FUNCS,
    CONTRACT_WRAPPER_FUNCS
    )
from py2viper_translation.analyzer import (
    PythonVar,
    PythonMethod,
    PythonClass,
    PythonField,
    PythonProgram,
    PythonExceptionHandler
    )
from py2viper_translation.constants import PRIMITIVES
from py2viper_translation.jvmaccess import JVM
from py2viper_translation.typeinfo import TypeInfo
from py2viper_translation.viper_ast import ViperAST
from py2viper_translation.util import flatten, UnsupportedException


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
        self.current_class = None
        self.current_function = None
        self.program = None

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
            if stmts:
                raise InvalidProgramException(node, 'purity.violated')
            results.insert(0, expr)
        result = None
        for let_or_expr in results:
            if result is None:
                if isinstance(let_or_expr, LetWrapper):
                    raise InvalidProgramException(function.node,
                                                  'function.return.missing')
                result = let_or_expr
            else:
                if not isinstance(let_or_expr, LetWrapper):
                    raise InvalidProgramException(function.node,
                                                  'function.dead.code')
                result = self.viper.Let(let_or_expr.vardecl, let_or_expr.expr,
                                        result,
                                        self.to_position(let_or_expr.node),
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
            left_stmt, left = self.translate_expr(node.left)
            right_stmt, right = self.translate_expr(node.right)
            if left_stmt or right_stmt:
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
        target = self.current_function.get_variable(node.targets[0].id).decl
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
            if stmt:
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

    def translate_result(self, node: ast.Call) -> StmtAndExpr:
        assert len(node.args) == 0
        type = self.current_function.type
        if not self.current_function.pure:
            return (
                [], self.viper.LocalVar('_res', self.translate_type(type),
                                        self.noposition(),
                                        self.noinfo()))
        else:
            return ([], self.viper.Result(self.translate_type(type),
                                          self.to_position(node),
                                          self.noinfo()))

    def translate_acc(self, node: ast.Call) -> StmtAndExpr:
        stmt, fieldacc = self.translate_expr(node.args[0])
        if stmt:
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
        return [], pred

    def translate_implies(self, node: ast.Call) -> StmtAndExpr:
        assert len(node.args) == 2
        cond_stmt, cond = self.translate_expr(node.args[0])
        then_stmt, then = self.translate_expr(node.args[1])
        implication = self.viper.Implies(cond, then,
                                         self.to_position(node),
                                         self.noinfo())
        return (cond_stmt + then_stmt, implication)

    def translate_old(self, node: ast.Call) -> StmtAndExpr:
        assert len(node.args) == 1
        stmt, exp = self.translate_expr(node.args[0])
        res = self.viper.Old(exp, self.to_position(node), self.noinfo())
        return (stmt, res)

    def translate_contractfunc_call(self, node: ast.Call) -> StmtAndExpr:
        """
        Translates calls to contract functions like Result() and Acc()
        """
        if self.get_func_name(node) == "Result":
            return self.translate_result(node)
        elif self.get_func_name(node) == 'Acc':
            return self.translate_acc(node)
        elif self.get_func_name(node) == 'Implies':
            return self.translate_implies(node)
        elif self.get_func_name(node) == 'Old':
            return self.translate_old(node)
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
            cls = self.program.classes[node.args[1].id]
            return (stmt, self.hastype(obj, cls))
        args = []
        formal_args = []
        arg_stmts = []
        for arg in node.args:
            arg_stmt, arg_expr = self.translate_expr(arg)
            arg_stmts = arg_stmts + arg_stmt
            args.append(arg_expr)
        name = self.get_func_name(node)
        if name in self.program.classes:
            # this is a constructor call
            target_class = self.program.classes[name]
            targets = []
            result_var = self.current_function.create_variable(name + '_res',
                                                               target_class,
                                                               self)
            targets.append(result_var.ref)
            target = target_class.get_method('__init__')
            if target is not None:
                if target.declared_exceptions:
                    errorvar = self.current_function.create_variable(
                        target.name + '_err',
                        self.program.classes['Exception'], self)
                    targets.append(errorvar.ref)
            call = [self.viper.MethodCall(target_class.sil_name + '___init__',
                                          args, targets,
                                          self.to_position(node),
                                          self.noinfo())]
            if target is not None and target.declared_exceptions:
                call = call + self.create_exception_catchers(errorvar,
                    self.current_function.handlers, node)
            return (arg_stmts + call, result_var.ref)
        if isinstance(node.func, ast.Attribute):
            # method called on an object
            rec_stmt, receiver = self.translate_expr(node.func.value)
            receiver_class = self.get_type(node.func.value)
            target = receiver_class.get_func_or_method(node.func.attr)
            receiver_class = target.cls
            arg_stmts = rec_stmt + arg_stmts
            args = [receiver] + args
        else:
            # global function/method called
            receiver_class = None
            target = self.program.get_func_or_method(name)
        for arg in target.args:
            formal_args.append(target.args[arg].decl)
        target_name = target.sil_name
        if receiver_class is not None:
            target_name = receiver_class.sil_name + '_' + target_name
        if target.pure:
            type = self.translate_type(target.type)
            return (arg_stmts, self.viper.FuncApp(target_name, args,
                                                  self.to_position(
                                                      node),
                                                  self.noinfo(),
                                                  type,
                                                  formal_args))
        else:
            targets = []
            result_var = None
            if self.current_function is None:
                if self.current_class is None:
                    # global variable
                    raise InvalidProgramException(node, 'purity.violated')
                else:
                    # static field
                    raise UnsupportedException(node)
            if target.type is not None:
                result_var = self.current_function.create_variable(
                    target.name + '_res', target.type, self)
                targets.append(result_var.ref)
            if target.declared_exceptions:
                errorvar = self.current_function.create_variable(
                    target.name + '_err',
                    self.program.classes['Exception'], self)
                targets.append(errorvar.ref)
            call = [self.viper.MethodCall(target_name, args, targets,
                                          self.to_position(node),
                                          self.noinfo())]
            if target.declared_exceptions:
                call = call + self.create_exception_catchers(errorvar,
                    self.current_function.handlers, node)
            return (arg_stmts + call,
                    result_var.ref if result_var else None)

    def create_exception_catchers(self, var: PythonVar,
                                  handlers: List[PythonExceptionHandler],
                                  call: ast.Call) -> List[Stmt]:
        """
        Creates the code for catching an exception, i.e. redirecting control
        flow to the handlers or giving the exception to the caller function
        """
        cases = []
        position = self.to_position(call)
        err_var = self.viper.LocalVar('_err', self.viper.Ref,
                                      self.noposition(),
                                      self.noinfo())
        if self.current_function.declared_exceptions:
            assignerror = self.viper.LocalVarAssign(err_var, var.ref, position,
                                                    self.noinfo())
            gotoend = self.viper.Goto('__end', position,
                                      self.noinfo())
            uncaught_option = self.translate_block([assignerror, gotoend],
                                                   position,
                                                   self.noinfo())
        else:
            uncaught_option = self.viper.Exhale(
                self.viper.FalseLit(position, self.noinfo()), position,
                self.noinfo())
        for handler in handlers:
            if self.contains_stmt(handler.region, call):
                condition = self.var_has_type(var.sil_name, handler.exception)
                goto = self.viper.Goto(handler.name,
                                       self.to_position(handler.node),
                                       self.noinfo())
                cases.insert(0, (condition, goto))
        result = None
        for cond, goto in cases:
            if result is None:
                result = self.viper.If(cond, goto,
                                       uncaught_option,
                                       self.to_position(handler.node),
                                       self.noinfo())
            else:
                result = self.viper.If(cond, goto, result,
                                       self.to_position(handler.node),
                                       self.noinfo())
        if result is None:
            error_case = uncaught_option
        else:
            error_case = result
        errnotnull = self.viper.NeCmp(var.ref,
                                      self.viper.NullLit(self.noposition(),
                                                         self.noinfo()),
                                      position, self.noinfo())
        emptyblock = self.translate_block([], self.noposition(),
                                          self.noinfo())
        errcheck = self.viper.If(errnotnull, error_case, emptyblock,
                                 position,
                                 self.noinfo())
        return [errcheck]

    def contains_stmt(self, container: Any, contained: ast.AST) -> bool:
        """
        Checks if 'contained' is a part of the partial AST
        whose root is 'container'.
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
            type = self.translate_type(var.type)
            func_app = self.viper.FuncApp(var.sil_name, [],
                                         self.to_position(node),
                                         self.noinfo(), type, [])
            return [], func_app
        else:
            return [], self.current_function.get_variable(node.id).ref

    def translate_Attribute(self, node: ast.Attribute) -> StmtAndExpr:
        stmt, receiver = self.translate_expr(node.value)
        rec_type = self.get_type(node.value)
        result = rec_type.get_field(node.attr)
        while result.inherited is not None:
            result = result.inherited
        if result.is_mangled():
            if result.cls is not self.current_class:
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
            return self.current_function.get_variable(node.id).type
        elif isinstance(node, ast.Call):

            if isinstance(node.func, ast.Name):
                if node.func.id in CONTRACT_FUNCS:
                    if node.func.id == 'Result':
                        return self.current_function.type
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
        cond_stmt, cond = self.translate_expr(node.test)
        then_stmt, then = self.translate_expr(node.body)
        else_stmt, else_ = self.translate_expr(node.orelse)
        if then_stmt or else_stmt:
            then_block = self.translate_block(then_stmt, position,
                                              self.noinfo())
            else_block = self.translate_block(else_stmt, position,
                                              self.noinfo())
            if_stmt = self.viper.If(cond, then_block, else_block, position,
                                    self.noinfo())
            bodystmt = [if_stmt]
        else:
            bodystmt = []
        cond_exp = self.viper.CondExp(cond, then, else_,
                                      self.to_position(node),
                                      self.noinfo())
        return cond_stmt + bodystmt, cond_exp

    def translate_BinOp(self, node: ast.BinOp) -> StmtAndExpr:
        left_stmt, left = self.translate_expr(node.left)
        right_stmt, right = self.translate_expr(node.right)
        stmt = left_stmt + right_stmt
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
        left_stmt, left = self.translate_expr(node.left)
        right_stmt, right = self.translate_expr(node.comparators[0])
        stmts = left_stmt + right_stmt
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
            return ([],
                    self.viper.NullLit(self.to_position(node), self.noinfo()))
        else:
            raise UnsupportedException(node)

    def translate_BoolOp(self, node: ast.BoolOp) -> StmtAndExpr:
        if len(node.values) != 2:
            raise UnsupportedException(node)
        position = self.to_position(node)
        left_stmt, left = self.translate_expr(node.values[0])
        right_stmt, right = self.translate_expr(node.values[1])
        if left_stmt or right_stmt:
            cond = left
            if isinstance(node.op, ast.Or):
                cond = self.viper.Not(cond, position, self.noinfo())
            then_block = self.translate_block(right_stmt, position,
                                              self.noinfo())
            else_block = self.translate_block([], position, self.noinfo())
            if_stmt = self.viper.If(cond, then_block, else_block, position,
                                   self.noinfo())
            stmt = left_stmt + [if_stmt]
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
        lhs_stmt, lhs = self.translate_expr(node.target)
        if lhs_stmt:
            raise InvalidProgramException(node, 'purity.violated')
        rhs_stmt, rhs = self.translate_expr(node.value)
        if isinstance(node.op, ast.Add):
            newval = self.viper.Add(lhs, rhs,
                                    self.to_position(node),
                                    self.noinfo())
        elif isinstance(node.op, ast.Sub):
            newval = self.viper.Sub(lhs, rhs,
                                    self.to_position(node),
                                    self.noinfo())
        elif isinstance(node.op, ast.Mult):
            newval = self.viper.Mul(lhs, rhs,
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
        return rhs_stmt + [assign]

    def translate_stmt_Try(self, node: ast.Try) -> List[Stmt]:
        body = flatten([self.translate_stmt(stmt) for stmt in node.body])
        end_label = self.viper.Label('post_' + node.sil_name,
                                     self.to_position(node),
                                     self.noinfo())
        return body + [end_label]

    def translate_stmt_Raise(self, node: ast.Raise) -> List[Stmt]:
        var = self.current_function.create_variable('raise',
                                                   self.get_type(node.exc),
                                                   self)
        stmt, exception = self.translate_expr(node.exc)
        assignment = self.viper.LocalVarAssign(var.ref, exception,
                                               self.to_position(node),
                                               self.noinfo())
        catchers = self.create_exception_catchers(var,
            self.current_function.handlers, node)
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
            if not stmt:
                raise InvalidProgramException(node, 'no.effect')
            return stmt

    def translate_stmt_Expr(self, node: ast.Expr) -> List[Stmt]:
        if isinstance(node.value, ast.Call):
            return self.translate_stmt(node.value)
        else:
            raise UnsupportedException(node)

    def translate_stmt_If(self, node: ast.If) -> List[Stmt]:
        cond_stmt, cond = self.translate_expr(node.test)
        then_body = flatten([self.translate_stmt(stmt) for stmt in node.body])
        then_block = self.translate_block(then_body, self.to_position(node),
                                          self.noinfo())
        else_body = flatten([self.translate_stmt(stmt) for stmt in node.orelse])
        else_block = self.translate_block(
            else_body,
            self.to_position(node), self.noinfo())
        return cond_stmt + [self.viper.If(cond, then_block, else_block,
                                          self.to_position(node),
                                          self.noinfo())]

    def translate_stmt_Assign(self, node: ast.Assign) -> List[Stmt]:
        if len(node.targets) != 1:
            raise UnsupportedException(node)
        target = node.targets[0]
        lhs_stmt, var = self.translate_expr(target)
        if isinstance(target, ast.Name):
            assignment = self.viper.LocalVarAssign
        else:
            assignment = self.viper.FieldAssign
        rhs_stmt, rhs = self.translate_expr(node.value)
        assign = assignment(var,
                            rhs, self.to_position(node),
                            self.noinfo())
        return lhs_stmt + rhs_stmt + [assign]

    def translate_stmt_While(self, node: ast.While) -> List[Stmt]:
        cond_stmt, cond = self.translate_expr(node.test)
        if cond_stmt:
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
        type = self.current_function.type
        rhs_stmt, rhs = self.translate_expr(node.value)
        assign = self.viper.LocalVarAssign(
            self.viper.LocalVar('_res', self.translate_type(type),
                                self.noposition(), self.noinfo()),
            rhs, self.to_position(node),
            self.noinfo())
        jmp_to_end = self.viper.Goto("__end", self.to_position(node),
                                     self.noinfo())
        return rhs_stmt + [assign, jmp_to_end]

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
        return (len(func.decorator_list) == 1
                and func.decorator_list[0].id == 'Predicate')

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

    def create_type(self, cls: PythonClass) -> Tuple['silver.ast.DomainFunc',
                                                     'silver.ast.DomainAxiom']:
        """
        Creates the type domain function and subtype axiom for this class
        """

        supertype = 'object' if not cls.superclass else cls.superclass.sil_name
        position = self.to_position(cls.node)
        info = self.noinfo()
        return (self.create_type_function(cls.sil_name, position, info),
                self.create_subtype_axiom(cls.sil_name, supertype, position,
                                          info))

    def create_type_function(self, name: str, position: 'silver.ast.Position',
                             info: 'silver.ast.Info') -> 'silver.ast.DomainFunc':
        return self.viper.DomainFunc(name, [], self.typetype(), True, position,
                                     info, self.typedomain)

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
        type_var = self.viper.LocalVar('class', self.typetype(), position, info)
        type_func = self.viper.DomainFuncApp(type, [], {}, self.typetype(), [],
                                             position, info, self.typedomain)
        supertype_func = self.viper.DomainFuncApp(supertype, [], {},
                                                  self.typetype(), [], position,
                                                  info, self.typedomain)
        body = self.viper.DomainFuncApp('issubtype',
                                        [type_func, supertype_func], {},
                                        self.viper.Bool, [type_var, type_var],
                                        position, info, self.typedomain)
        return self.viper.DomainAxiom('subtype_' + type, body, position, info, 
                                      self.typedomain)

    def create_transitivity_axiom(self) -> 'silver.ast.DomainAxiom':
        """
        Creates the transitivity axiom for the PyType domain
        """
        arg_sub = self.viper.LocalVarDecl('sub', self.typetype(),
                                          self.noposition(),
                                          self.noinfo())
        var_sub = self.viper.LocalVar('sub', self.typetype(),
                                      self.noposition(), self.noinfo())
        arg_middle = self.viper.LocalVarDecl('middle', self.typetype(),
                                             self.noposition(),
                                             self.noinfo())
        var_middle = self.viper.LocalVar('middle', self.typetype(),
                                         self.noposition(),
                                         self.noinfo())
        arg_super = self.viper.LocalVarDecl('super', self.typetype(),
                                            self.noposition(),
                                            self.noinfo())
        var_super = self.viper.LocalVar('super', self.typetype(),
                                        self.noposition(), self.noinfo())

        sub_middle = self.viper.DomainFuncApp('issubtype',
                                              [var_sub, var_middle], {},
                                              self.viper.Bool,
                                              [var_sub, var_middle],
                                              self.noposition(),
                                              self.noinfo(), self.typedomain)
        middle_super = self.viper.DomainFuncApp('issubtype',
                                                [var_middle, var_super], {},
                                                self.viper.Bool,
                                                [var_middle, var_super],
                                                self.noposition(),
                                                self.noinfo(), self.typedomain)
        sub_super = self.viper.DomainFuncApp('issubtype', [var_sub, var_super],
                                             {}, self.viper.Bool,
                                             [var_sub, var_super],
                                             self.noposition(),
                                             self.noinfo(), self.typedomain)
        implication = self.viper.Implies(
            self.viper.And(sub_middle, middle_super, self.noposition(),
                           self.noinfo()), sub_super, self.noposition(),
            self.noinfo())
        trigger = self.viper.Trigger([sub_middle, middle_super],
                                     self.noposition(), self.noinfo())
        body = self.viper.Forall([arg_sub, arg_middle, arg_super], [trigger],
                                 implication, self.noposition(),
                                 self.noinfo())
        return self.viper.DomainAxiom('issubtype_transitivity', body,
                                      self.noposition(), self.noinfo(), 
                                      self.typedomain)

    def create_reflexivity_axiom(self) -> 'silver.ast.DomainAxiom':
        """
        Creates the reflexivity axiom for the PyType domain
        """
        arg = self.viper.LocalVarDecl('type', self.typetype(),
                                      self.noposition(), self.noinfo())
        var = self.viper.LocalVar('type', self.typetype(),
                                  self.noposition(), self.noinfo())
        reflexive_subtype = self.viper.DomainFuncApp('issubtype', [var, var],
                                                     {}, self.viper.Bool,
                                                     [var, var],
                                                     self.noposition(),
                                                     self.noinfo(), 
                                                     self.typedomain)
        trigger_exp = reflexive_subtype
        trigger = self.viper.Trigger([trigger_exp], self.noposition(),
                                     self.noinfo())
        body = self.viper.Forall([arg], [trigger], reflexive_subtype,
                                 self.noposition(), self.noinfo())
        return self.viper.DomainAxiom('issubtype_reflexivity', body,
                                      self.noposition(), self.noinfo(), 
                                      self.typedomain)

    def typeof_func(self) -> 'silver.ast.DomainFunc':
        """
        Creates the typeof domain function
        """
        obj_var = self.viper.LocalVarDecl('obj', self.viper.Ref,
                                          self.noposition(),
                                          self.noinfo())
        return self.viper.DomainFunc('typeof', [obj_var],
                                     self.typetype(), False,
                                     self.noposition(), self.noinfo(), 
                                     self.typedomain)

    def issubtype_func(self) -> 'silver.ast.DomainFunc':
        """
        Creates the issubtype domain function
        """
        sub_var = self.viper.LocalVarDecl('sub', self.typetype(),
                                          self.noposition(),
                                          self.noinfo())
        super_var = self.viper.LocalVarDecl('super', self.typetype(),
                                            self.noposition(),
                                            self.noinfo())
        return self.viper.DomainFunc('issubtype', [sub_var, super_var],
                                     self.viper.Bool, False,
                                     self.noposition(), self.noinfo(), 
                                     self.typedomain)

    def var_has_type(self, name: str,
                   type: PythonClass) -> 'silver.ast.DomainFuncApp':
        """
        Creates an expression checking if the var with the given name
        is of the given type
        """
        obj_var = self.viper.LocalVar(name, self.viper.Ref,
                                     self.noposition(),
                                     self.noinfo())
        return self.hastype(obj_var, type)

    def hastype(self, lhs: Expr, type: PythonClass):
        """
        Creates an expression checking if the given lhs expression
        is of the given type
        """
        type_func = self.viper.DomainFuncApp('typeof', [lhs], {},
                                             self.typetype(), [lhs],
                                             self.noposition(),
                                             self.noinfo(), self.typedomain)
        supertype_func = self.viper.DomainFuncApp(type.sil_name, [], {},
                                                  self.typetype(), [],
                                                  self.noposition(),
                                                  self.noinfo(), 
                                                  self.typedomain)
        var_sub = self.viper.LocalVar('sub', self.typetype(),
                                      self.noposition(), self.noinfo())
        var_super = self.viper.LocalVar('super', self.typetype(),
                                        self.noposition(), self.noinfo())
        subtype_func = self.viper.DomainFuncApp('issubtype',
                                                [type_func, supertype_func], {},
                                                self.viper.Bool,
                                                [var_sub, var_super],
                                                self.noposition(),
                                                self.noinfo(), self.typedomain)
        return subtype_func

    def translate_pythonvar_decl(self,
                                 var: PythonVar) -> 'silver.ast.LocalVarDecl':
        """
        Creates a variable declaration for the given PythonVar.
        To be called during the processing phase by the Analyzer.
        """
        return self.viper.LocalVarDecl(var.sil_name,
                                       self.translate_type(var.type),
                                       self.noposition(), self.noinfo())

    def translate_pythonvar_ref(self, var: PythonVar) -> Expr:
        """
        Creates a variable reference for the given PythonVar.
        To be called during the processing phase by the Analyzer.
        """
        return self.viper.LocalVar(var.sil_name,
                                   self.translate_type(var.type),
                                   self.noposition(), self.noinfo())

    def translate_type(self, cls: PythonClass) -> 'silver.ast.Type':
        """
        Translates the given type to the corresponding Viper type (Int, Ref, ..)
        """
        if 'builtins.' + cls.name in self.builtins:
            return self.builtins['builtins.' + cls.name]
        else:
            return self.viper.Ref

    def get_parameter_typeof(self,
                             param: PythonVar) -> 'silver.ast.DomainFuncApp':
        return self.var_has_type(param.sil_name, param.type)

    def translate_field(self, field: PythonField) -> 'silver.ast.Field':
        return self.viper.Field(field.cls.sil_name + '_' + field.sil_name,
                                self.translate_type(field.type),
                                self.to_position(field.node),
                                self.noinfo())

    def get_body_start_index(self, statements: List[ast.AST]) -> int:
        """
        Returns the index of the first statement that is not a method contract
        """
        body_index = 0
        while self.is_pre(statements[body_index]):
            body_index += 1
        while self.is_post(statements[body_index]):
            body_index += 1
        while self.is_exception_decl(statements[body_index]):
            body_index += 1
        return body_index

    def translate_function(self, func: PythonMethod) -> 'silver.ast.Function':
        """
        Translates a pure Python function (may or not belong to a class) to a
        Viper function
        """
        old_function = self.current_function
        self.current_function = func
        type = self.translate_type(func.type)
        args = []
        for arg in func.args:
            args.append(func.args[arg].decl)
        if func.declared_exceptions:
            raise InvalidProgramException(func.node,
                                          'function.throws.exception')
        # create preconditions
        pres = []
        for pre in func.precondition:
            stmt, expr = self.translate_expr(pre)
            if stmt:
                raise InvalidProgramException(pre, 'purity.violated')
            pres.append(expr)
        # create postconditions
        posts = []
        for post in func.postcondition:
            stmt, expr = self.translate_expr(post)
            if stmt:
                raise InvalidProgramException(post, 'purity.violated')
            posts.append(expr)
        # create typeof preconditions
        for arg in func.args:
            if not func.args[arg].type.name in PRIMITIVES:
                pres.append(self.get_parameter_typeof(func.args[arg]))
        statements = func.node.body
        body_index = self.get_body_start_index(statements)
        # translate body
        body = self.translate_exprs(statements[body_index:], func)
        self.current_function = old_function
        name = func.sil_name
        if func.cls is not None:
            name = func.cls.sil_name + '_' + name
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
        body_block = self.translate_block(body,
                                          self.to_position(handler.node),
                                          self.noinfo())
        goto_end = self.viper.Goto('post_' + handler.tryname,
                                   self.to_position(handler.node),
                                   self.noinfo())
        return [label, body_block, goto_end]

    def extract_contract(self, method: PythonMethod, errorvarname: str,
                         isconstructor: bool) -> Tuple[List[Expr], List[Expr]]:
        """
        Extracts the pre and postcondition from a given method
        """
        error_var_ref = self.viper.LocalVar(errorvarname, self.viper.Ref,
                                            self.noposition(),
                                            self.noinfo())
        # create preconditions
        pres = []
        for pre in method.precondition:
            stmt, expr = self.translate_expr(pre)
            if stmt:
                raise InvalidProgramException(pre, 'purity.violated')
            pres.append(expr)
        # create postconditions
        posts = []
        noerror = self.viper.EqCmp(error_var_ref,
                                   self.viper.NullLit(self.noposition(),
                                                      self.noinfo()),
                                   self.noposition(), self.noinfo())
        error = self.viper.NeCmp(error_var_ref,
                                 self.viper.NullLit(self.noposition(),
                                                    self.noinfo()),
                                 self.noposition(), self.noinfo())
        for post in method.postcondition:
            stmt, expr = self.translate_expr(post)
            if stmt:
                raise InvalidProgramException(post, 'purity.violated')
            if method.declared_exceptions:
                expr = self.viper.Implies(noerror, expr,
                                          self.to_position(post),
                                          self.noinfo())
            posts.append(expr)
        # create exceptional postconditions
        error_type_conds = []
        error_type_pos = self.to_position(method.node)
        for exception in method.declared_exceptions:
            oldpos = self.position
            if self.position is None:
                self.position = error_type_pos
            has_type = self.var_has_type('_err',
                                         self.program.classes[exception])
            error_type_conds.append(has_type)
            self.position = oldpos
            condition = self.viper.And(error, has_type, self.noposition(),
                                       self.noinfo())
            for post in method.declared_exceptions[exception]:
                stmt, expr = self.translate_expr(post)
                if stmt:
                    raise InvalidProgramException(post, 'purity.violated')
                expr = self.viper.Implies(condition, expr,
                                          self.to_position(post),
                                          self.noinfo())
                posts.append(expr)

        error_type_cond = None
        for type in error_type_conds:
            if error_type_cond is None:
                error_type_cond = type
            else:
                error_type_cond = self.viper.Or(error_type_cond, type,
                                                error_type_pos,
                                                self.noinfo())
        if error_type_cond is not None:
            posts.append(self.viper.Implies(error, error_type_cond,
                                            self.to_position(post),
                                            self.noinfo()))
        # create typeof preconditions
        for arg in method.args:
            if not (method.args[arg].type.name in PRIMITIVES
                    or (isconstructor and arg == next(iter(method.args)))):
                pres.append(self.get_parameter_typeof(method.args[arg]))
        return pres, posts

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
        if comments:
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
        old_function = self.current_function
        self.current_function = method.overrides
        assert self.position is None
        self.position = self.viper.to_position(method.node)
        self.info = self.viper.SimpleInfo(['behavioural.subtyping'])
        self._check_override_validity(method)
        params = []
        args = []
        type = self.translate_type(method.type)
        mname = method.sil_name + '_subtyping'
        pres, posts = self.extract_contract(method.overrides, '_err', False)
        if method.cls:
            mname = method.cls.sil_name + '_' + mname
        for arg in method.overrides.args:
            params.append(method.overrides.args[arg].decl)
            args.append(method.overrides.args[arg].ref)
        self_arg = method.overrides.args[next(iter(method.overrides.args))]
        has_subtype = self.var_has_type(self_arg.sil_name, method.cls)
        called_name = method.cls.sil_name + '_' + method.sil_name
        if method.pure:
            pres = pres + [has_subtype]
            formal_args = []
            for arg in method.args:
                formal_args.append(method.args[arg].decl)
            func_app = self.viper.FuncApp(called_name, args, self.noposition(),
                                          self.noinfo(), type, formal_args)
            self.current_function = old_function
            result = self.viper.Function(mname, params, type, pres, posts,
                                         func_app, self.noposition(),
                                         self.noinfo())
            self.position = None
            self.info = None
            return result
        else:
            results, targets, body = self._create_subtyping_check_body_impure(
                method, has_subtype, called_name, args)
            self.current_function = old_function
            result = self.viper.Method(mname, params, results, pres, posts, [],
                                       body, self.noposition(),
                                       self.noinfo())
            self.position = None
            self.info = None
            return result

    def _check_override_validity(self, method: PythonMethod) -> None:
        if len(method.args) != len(method.overrides.args):
            raise InvalidProgramException(method.node, 'invalid.override')
        for exc in method.declared_exceptions:
            exc_class = self.program.classes[exc]
            allowed = False
            for superexc in method.overrides.declared_exceptions:
                superexcclass = self.program.classes[superexc]
                if exc_class.issubtype(superexcclass):
                    allowed = True
                    break
            if not allowed:
                raise InvalidProgramException(method.node, 'invalid.override')
                # TODO check if exceptional postconditions imply super postconds
        if method.pure:
            if not method.overrides.pure:
                raise InvalidProgramException(method.node, 'invalid.override')
        else:
            if method.overrides.pure:
                raise InvalidProgramException(method.node, 'invalid.override')

    def _create_subtyping_check_body_impure(self, method: PythonMethod,
            has_subtype: Expr, calledname: str, args: List[Expr]) -> \
            Tuple[List['ast.LocalVarDecl'], List['ast.LocalVar'], Stmt]:
        type = self.translate_type(method.type)
        results = []
        targets = []
        result_var_decl = self.viper.LocalVarDecl('_res', type,
                                                  self.to_position(method.node),
                                                  self.noinfo())
        result_var_ref = self.viper.LocalVar('_res', type,
                                             self.to_position(
                                                method.node),
                                             self.noinfo())
        results.append(result_var_decl)
        targets.append(result_var_ref)
        error_var_decl = self.viper.LocalVarDecl('_err', self.viper.Ref,
                                                 self.noposition(),
                                                 self.noinfo())
        error_var_ref = self.viper.LocalVar('_err', self.viper.Ref,
                                            self.noposition(),
                                            self.noinfo())
        if method.overrides.declared_exceptions:
            results.append(error_var_decl)
        if method.declared_exceptions:
            targets.append(error_var_ref)
        call = self.viper.MethodCall(calledname, args, targets,
                                     self.noposition(),
                                     self.noinfo())
        subtype_assume = self.viper.Inhale(has_subtype, self.noposition(),
                                           self.noinfo())
        body = [subtype_assume, call]
        body_block = self.translate_block(body, self.noposition(),
                                          self.noinfo())
        return results, targets, body_block

    def translate_method(self, method: PythonMethod) -> 'silver.ast.Method':
        """
        Translates an impure Python function (may or not belong to a class) to
        a Viper method
        """
        old_function = self.current_function
        self.current_function = method
        results = []
        if method.type is not None:
            type = self.translate_type(method.type)
            results.append(self.viper.LocalVarDecl('_res', type,
                                                   self.to_position(
                                                       method.node),
                                                   self.noinfo()))
        error_var_decl = self.viper.LocalVarDecl('_err', self.viper.Ref,
                                                 self.noposition(),
                                                 self.noinfo())
        error_var_ref = self.viper.LocalVar('_err', self.viper.Ref,
                                            self.noposition(),
                                            self.noinfo())
        pres, posts = self.extract_contract(method, '_err', False)
        if method.declared_exceptions:
            results.append(error_var_decl)
        args = []
        for arg in method.args:
            args.append(method.args[arg].decl)

        statements = method.node.body
        body_index = self.get_body_start_index(statements)
        # translate body
        body = []
        if method.declared_exceptions:
            body.append(self.viper.LocalVarAssign(error_var_ref,
                self.viper.NullLit(self.noposition(), self.noinfo()),
                self.noposition(), self.noinfo()))
        body += flatten(
            [self.translate_stmt(stmt) for stmt in
             method.node.body[body_index:]])
        body.append(self.viper.Goto('__end', self.noposition(),
                                    self.noinfo()))
        for handler in method.handlers:
            body += self.translate_handler(handler)
        locals = []
        for local in method.locals:
            locals.append(method.locals[local].decl)
        body += [self.viper.Label("__end", self.noposition(),
                                  self.noinfo())]
        body_block = self.translate_block(body,
                                         self.to_position(method.node),
                                         self.noinfo())
        self.current_function = old_function
        name = method.sil_name
        if method.cls is not None:
            name = method.cls.sil_name + '_' + name
        return self.viper.Method(name, args, results, pres, posts,
                                 locals, body_block,
                                 self.to_position(method.node),
                                 self.noinfo())

    def _get_all_fields(self, cls: PythonClass, selfvar: 'silver.ast.LocalVar',
            position: 'silver.ast.Position') \
            -> Tuple['silver.ast.Field', 'silver.ast.FieldAccessPredicate']:
        accs = []
        fields = []
        while cls is not None:
            for fieldname in cls.fields:
                field = cls.fields[fieldname]
                if field.inherited is None:
                    fields.append(field.field)
                    acc = self.viper.FieldAccess(selfvar, field.field,
                                                 position, self.noinfo())
                    perm = self.viper.FullPerm(position, self.noinfo())
                    pred = self.viper.FieldAccessPredicate(acc,
                                                           perm,
                                                           position,
                                                           self.noinfo())
                    accs.append(pred)
            cls = cls.superclass
        return fields, accs

    def create_constructor(self, cls: PythonClass) -> 'silver.ast.Method':
        """
        Creates a constructor method for the given class. Either creates a
        default constructor or translates the explicit one in the program.
        """
        method = cls.get_method('__init__')
        name = method.sil_name if method is not None else '__init__'
        name = cls.sil_name + '_' + name
        if method:
            position = self.to_position(method.node)
        else:
            position = self.noposition()
        selfvarname = 'self' if method is None else method.args[
            next(iter(method.args))].sil_name
        args = []
        results = [self.viper.LocalVarDecl(selfvarname, self.viper.Ref,
                                           position, self.noinfo())]
        self_var = self.viper.LocalVar(selfvarname, self.viper.Ref,
                                       self.noposition(), self.noinfo())
        locals = []
        body = []
        pres = []
        posts = []
        fields, accs = self._get_all_fields(cls, self_var, position)
        if method:
            accs = []

        body.append(self.viper.NewStmt(self_var, fields, self.noposition(),
                                       self.noinfo()))
        result_has_type = self.var_has_type(selfvarname, cls)
        body.append(self.viper.Inhale(result_has_type, self.noposition(),
                                      self.noinfo()))
        notnull = self.viper.NeCmp(self_var,
                                   self.viper.NullLit(self.noposition(),
                                                      self.noinfo()),
                                   self.noposition(),
                                   self.noinfo())
        posts.append(notnull)
        if method is not None:
            old_function = self.current_function
            self.current_function = method
            for arg in method.args:
                if arg == next(iter(method.args)):
                    continue
                args.append(method.args[arg].decl)
            error_var_decl = self.viper.LocalVarDecl('_err', self.viper.Ref,
                                                     self.noposition(),
                                                     self.noinfo())
            if method.declared_exceptions:
                results.append(error_var_decl)
            user_pres, user_posts = self.extract_contract(method, '_err', True)
            pres = pres + user_pres
            posts = posts + user_posts
            statements = method.node.body
            body_index = self.get_body_start_index(statements)
            body += flatten(
                [self.translate_stmt(stmt) for stmt in
                 method.node.body[body_index:]])
            body.append(self.viper.Goto('__end', self.noposition(),
                                        self.noinfo()))
            for handler in method.handlers:
                body += self.translate_handler(handler)
            for local in method.locals:
                locals.append(method.locals[local].decl)
            self.current_function = old_function

        body += [self.viper.Label("__end", self.noposition(),
                                  self.noinfo())]
        body_block = self.translate_block(body, position, self.noinfo())
        posts.append(result_has_type)
        posts += accs
        return self.viper.Method(name, args, results, pres, posts,
                                 locals, body_block,
                                 position,
                                 self.noinfo())

    def create_global_var_function(self,
                                   var: PythonVar) -> 'silver.ast.Function':
        """
        Creates a Viper function representing the given global variable
        """
        type = self.translate_type(var.type)
        if type == self.viper.Ref:
            raise UnsupportedException(var.node)
        position = self.to_position(var.node)
        posts = []
        result = self.viper.Result(type, position, self.noinfo())
        stmt, value = self.translate_expr(var.value)
        if stmt:
            raise InvalidProgramException('purity.violated', var.node)
        posts.append(
            self.viper.EqCmp(result, value, position, self.noinfo()))
        return self.viper.Function(var.sil_name, [], type, [], posts, None,
                                   self.to_position(var.node),
                                   self.noinfo())

    def translate_program(self, program: PythonProgram) -> 'silver.ast.Program':
        """
        Translates a PythonProgram created by the analyzer to a Viper program.
        """
        self.current_class = None
        self.current_function = None
        self.program = program
        fields = []
        functions = []
        predicates = []
        methods = []

        typeof = self.typeof_func()
        issubtype = self.issubtype_func()
        object_func = self.create_type_function('object', self.noposition(),
                                                self.noinfo())
        type_funcs = [object_func, typeof, issubtype]
        type_axioms = [self.create_reflexivity_axiom(),
                       self.create_transitivity_axiom()]

        for var in program.global_vars:
            functions.append(
                self.create_global_var_function(program.global_vars[var]))

        for class_name in program.classes:
            if class_name in PRIMITIVES:
                continue
            cls = program.classes[class_name]
            for fieldname in cls.fields:
                field = cls.fields[fieldname]
                if field.inherited is None:
                    silfield = self.translate_field(field)
                    field.field = silfield
                    fields.append(silfield)

        for function in program.functions:
            functions.append(
                self.translate_function(program.functions[function]))
        for method in program.methods:
            methods.append(self.translate_method(program.methods[method]))
        for class_name in program.classes:
            if class_name in PRIMITIVES:
                continue
            cls = program.classes[class_name]
            old_class = self.current_class
            self.current_class = cls
            funcs, axioms = self.create_type(cls)
            type_funcs.append(funcs)
            type_axioms.append(axioms)
            for func_name in cls.functions:
                func = cls.functions[func_name]
                functions.append(self.translate_function(func))
                if func.overrides:
                    functions.append(self.create_subtyping_check(func))
            for method_name in cls.methods:
                if method_name != '__init__':
                    method = cls.methods[method_name]
                    methods.append(self.translate_method(method))
                    if method.overrides:
                        methods.append(self.create_subtyping_check(method))
            methods.append(self.create_constructor(cls))
            self.current_class = old_class

        domains = [self.viper.Domain(self.typedomain, type_funcs, type_axioms,
                                     [], self.noposition(), self.noinfo())]

        prog = self.viper.Program(domains, fields, functions, predicates,
                                  methods, self.noposition(),
                                  self.noinfo())
        return prog
