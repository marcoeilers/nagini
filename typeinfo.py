import mypy.build
import os
import sys

from typing import List

class TypeException(Exception):
    def __init__(self, messages):
        self.messages = messages

class TypeVisitor(mypy.traverser.TraverserVisitor):
    def __init__(self, typeMap, path):
        self.prefix = []
        self.allTypes = {}
        self.typeMap = typeMap
        self.path = path

    def visit_member_expr(self, o: mypy.nodes.MemberExpr):
        print("visit member")
        print(o.name)
        print('type of whole thing')

        self.set_type([self.typeOf(o.expr).type.name(), o.name], self.typeOf(o))
        super().visit_member_expr(o)

    def visit_try_stmt(self, o: mypy.nodes.TryStmt):
        for var in o.vars:
            if var is not None:
                self.set_type(self.prefix + [var.name], self.typeOf(var))
        for block in o.handlers:
            block.accept(self)

    def visit_name_expr(self, o: mypy.nodes.NameExpr):
        self.set_type(self.prefix + [o.name], self.typeOf(o))

    def visit_func_def(self, o: mypy.nodes.FuncDef):
        oldprefix = self.prefix
        self.prefix = self.prefix + [o.name()]
        functype = self.typeOf(o)
        self.set_type(self.prefix, functype)
        for arg in o.args:
            self.set_type(self.prefix + [arg.name()], arg.type)
        super().visit_func_def(o)
        self.prefix = oldprefix

    def visit_class_def(self, o: mypy.nodes.ClassDef):
        oldprefix = self.prefix
        self.prefix = self.prefix + [o.name]
        super().visit_class_def(o)
        self.prefix = oldprefix

    def set_type(self, fqn, type):
        if isinstance(type, mypy.types.AnyType):
            return # just ignore??
        key = tuple(fqn)
        if key in self.allTypes:
            if self.allTypes[key] != type:
                if not isinstance(self.allTypes[key], mypy.types.AnyType):
                    # Different types for same var? what is happening here?
                    print(key)
                    print(type)
                    print(self.allTypes[key])
                    raise Exception()
        self.allTypes[key] = type

    def visit_call_expr(self, o: mypy.nodes.CallExpr):
        for a in o.args:
            a.accept(self)

    def typeOf(self, node):
        print("typeof")
        print(node)
        if isinstance(node, mypy.nodes.FuncDef):
            return node.type
        elif isinstance(node, mypy.nodes.CallExpr):
            if node.callee.name == 'Result':
                type = self.allTypes[tuple(self.prefix)].ret_type
                return type
        if node in self.typeMap:
            return self.typeMap[node]
        else:
            msg = 'File "' + self.path + '", line ' + str(node.get_line()) + ' :'
            msg += 'dead.code'
            raise TypeException([msg])


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
            visitor = TypeVisitor(res.types, filename)
            # for df in res.files['__main__'].defs:
            # print(df)
            res.files['__main__'].accept(visitor)
            self.allTypes = visitor.allTypes
            print(self.allTypes)
            return True
        except mypy.errors.CompileError as e:
            for m in e.messages:
                sys.stderr.write('Mypy error: ' + m + '\n')
            raise TypeException(e.messages)

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
