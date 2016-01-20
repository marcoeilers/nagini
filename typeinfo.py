import mypy.build
import os
import sys

from typing import List, Tuple


ChildNodes = List[Tuple[str, mypy.nodes.Node]]
Vars = List[Tuple[List[str], mypy.types.Type]]

def class_children(clazz: mypy.nodes.ClassDef) -> ChildNodes:
    return [(clazz.name, clazz.defs.body)]

def func_children(func: mypy.nodes.FuncDef) -> ChildNodes:
    return [(func.name(), func.body.body)]


def decorator_children(dec: mypy.nodes.Decorator) -> ChildNodes:
    return func_children(dec.func)


def if_children(ifelse: mypy.nodes.IfStmt) -> ChildNodes:
    return [('', ifelse.body), ('', ifelse.else_body.body)]


def while_children(whl: mypy.nodes.WhileStmt) -> ChildNodes:
    return [('', whl.body.body)]


def block_children(block: mypy.nodes.Block) -> ChildNodes:
    return [('', block.body)]


def func_vars(func: mypy.nodes.FuncDef, prefix) -> Vars:
    functype = func.type
    if isinstance(functype, mypy.types.FunctionLike):
        functype = functype.ret_type
    return [(prefix + [func.name()], functype)] + [([func.name(), arg.name()], arg.type)
                                          for arg in func.args]


def decorator_vars(dec: mypy.nodes.Decorator, prefix) -> Vars:
    return func_vars(dec.func, prefix)


def assignment_vars(ass: mypy.nodes.AssignmentStmt, prefix) -> Vars:
    result = []
    for target in ass.lvalues:
        if isinstance(target, mypy.nodes.MemberExpr):
            result.append(([target.expr.type.name, target.name], target.node.type))
        elif isinstance(target, mypy.nodes.NameExpr):
            result.append((prefix + [target.name], target.node.type))
    return result

children_funcs = {mypy.nodes.FuncDef: func_children,
                  mypy.nodes.Decorator: decorator_children,
                  mypy.nodes.IfStmt: if_children,
                  mypy.nodes.WhileStmt: while_children,
                  mypy.nodes.Block: block_children,
                  mypy.nodes.ClassDef: class_children}

vars_funcs = {mypy.nodes.FuncDef: func_vars,
              mypy.nodes.Decorator: decorator_vars,
              mypy.nodes.AssignmentStmt: assignment_vars}

class TypeVisitor(mypy.traverser.TraverserVisitor):
    def __init__(self, typeMap):
        self.prefix = []
        self.allTypes = {}
        self.typeMap = typeMap

    def visit_member_expr(self, o: mypy.nodes.MemberExpr):
        self.setType([self.typeOf(o.expr).type.name(), o.name], self.typeOf(o))
        super().visit_member_expr(o)

    def visit_name_expr(self, o: mypy.nodes.NameExpr):
        self.setType(self.prefix + [o.name], self.typeOf(o))

    def visit_func_def(self, o: mypy.nodes.FuncDef):
        oldprefix = self.prefix
        self.prefix = self.prefix + [o.name()]
        functype = self.typeOf(o)
        # if isinstance(functype, mypy.types.FunctionLike):
        #     functype = functype.ret_type
        self.setType(self.prefix, functype)
        for arg in o.args:
            self.setType(self.prefix + [arg.name()], arg.type)
        super().visit_func_def(o)
        self.prefix = oldprefix

    def visit_class_def(self, o: mypy.nodes.ClassDef):
        oldprefix = self.prefix
        self.prefix = self.prefix + [o.name]
        super().visit_class_def(o)
        self.prefix = oldprefix

    def setType(self, fqn, type):
        key = tuple(fqn)
        if key in self.allTypes:
            if self.allTypes[key] != type:
                raise Exception()
        self.allTypes[key] = type

    def visit_call_expr(self, o: mypy.nodes.CallExpr):
        for a in o.args:
            a.accept(self)

    def typeOf(self, node):
        if isinstance(node, mypy.nodes.FuncDef):
            return node.type
        return self.typeMap[node]


class TypeInfo:
    """
    Provides type information for all variables and functions in a given
    Python program.
    """

    def __init__(self):
        self.allTypes = {}

    def check(self, filename: str, mypydir: str) -> bool:
        """
        Typechecks the given file and collects all type information needed for
        the translation to Viper
        """
        try:
            res = mypy.build.build(filename, target=mypy.build.TYPE_CHECK,
                                   bin_dir=os.path.dirname(mypydir))
            visitor = TypeVisitor(res.types)
            for df in res.files['__main__'].defs:
                print(df)
            #     self.traverse(df, [])
            res.files['__main__'].accept(visitor)
            self.allTypes = visitor.allTypes
            print(self.allTypes)
            return True
        except mypy.errors.CompileError as e:
            for m in e.messages:
                sys.stderr.write('Mypy error: ' + m + '\n')
            return False

    def gettype(self, prefix: List[str], name: str):
        """
        Looks up the inferred or annotated type for the given name in the given
        prefix
        """
        result = self.allTypes.get(tuple(prefix + [name]))
        if result is None:
            if not prefix:
                return None
            else:
                return self.gettype(prefix[:len(prefix) - 1], name)
        else:
            if isinstance(result, mypy.types.Instance):
                result = result.type
            print("gettype")
            print(result)
            print(self)
            return result

    def getfunctype(self, prefix: List[str]):
        """
        Looks up the type of the function which creates the given context
        """
        result = self.allTypes.get(tuple(prefix))
        if result is None:
            if len(prefix) == 0:
                return None
            else:
                return self.getfunctype(prefix[:len(prefix) - 1])
        else:
            if isinstance(result, mypy.types.FunctionLike):
                result = result.ret_type
            return result
