import os
import sys
import mypy.build

from mypy.build import BuildSource
from py2viper_translation import config
from py2viper_translation.constants import LITERALS
from typing import List


class TypeException(Exception):
    def __init__(self, messages):
        self.messages = messages


class TypeVisitor(mypy.traverser.TraverserVisitor):
    def __init__(self, type_map, path):
        self.prefix = []
        self.all_types = {}
        self.type_map = type_map
        self.path = path

    def visit_member_expr(self, o: mypy.nodes.MemberExpr):
        rectype = self.type_of(o.expr)
        if not isinstance(rectype, mypy.types.AnyType):
            self.set_type([rectype.type.name(), o.name], self.type_of(o))
        super().visit_member_expr(o)

    def visit_try_stmt(self, o: mypy.nodes.TryStmt):
        for var in o.vars:
            if var is not None:
                self.set_type(self.prefix + [var.name], self.type_of(var))
        for block in o.handlers:
            block.accept(self)

    def visit_name_expr(self, o: mypy.nodes.NameExpr):
        if not o.name in LITERALS:
            self.set_type(self.prefix + [o.name], self.type_of(o))

    def visit_func_def(self, o: mypy.nodes.FuncDef):
        oldprefix = self.prefix
        self.prefix = self.prefix + [o.name()]
        functype = self.type_of(o)
        self.set_type(self.prefix, functype)
        for arg in o.arguments:
            self.set_type(self.prefix + [arg.variable.name()],
                          arg.variable.type)
        super().visit_func_def(o)
        self.prefix = oldprefix

    def visit_class_def(self, o: mypy.nodes.ClassDef):
        oldprefix = self.prefix
        self.prefix = self.prefix + [o.name]
        super().visit_class_def(o)
        self.prefix = oldprefix

    def set_type(self, fqn, type):
        if isinstance(type, mypy.types.AnyType):
            return  # just ignore??
        if isinstance(type, mypy.types.Instance):
            type = type.type
        key = tuple(fqn)
        if key in self.all_types:
            if not self.type_equals(self.all_types[key], type):
                if not isinstance(self.all_types[key], mypy.types.AnyType):
                    # Different types for same var? what is happening here?
                    print(type)
                    print(self.all_types[key])
                    raise Exception()
        self.all_types[key] = type

    def type_equals(self, t1, t2):
        if str(t1) == str(t2):
            return True
        if (isinstance(t1, mypy.types.FunctionLike) and
                isinstance(t2, mypy.types.FunctionLike)):
            if self.type_equals(t1.ret_type, t2.ret_type):
                all_eq = True
                for arg1, arg2 in zip(t1.arg_types, t2.arg_types):
                    arg1 = t1.arg_types[i]
                    arg2 = t2.arg_types[i]
                    all_eq = all_eq and self.type_equals(arg1, arg2)
                return all_eq
        return t1 == t2

    def visit_call_expr(self, o: mypy.nodes.CallExpr):
        for a in o.args:
            a.accept(self)

    def type_of(self, node):
        if isinstance(node, mypy.nodes.FuncDef):
            return node.type
        elif isinstance(node, mypy.nodes.CallExpr):
            if node.callee.name == 'Result':
                type = self.all_types[tuple(self.prefix)].ret_type
                return type
        if node in self.type_map:
            result = self.type_map[node]
            return result
        else:
            msg = self.path + ':' + str(node.get_line()) + ': error: '
            msg += 'dead.code'
            raise TypeException([msg])


class TypeInfo:
    """
    Provides type information for all variables and functions in a given
    Python program.
    """

    def __init__(self):
        self.all_types = {}

    def check(self, filename: str) -> bool:
        """
        Typechecks the given file and collects all type information needed for
        the translation to Viper
        """
        try:
            res = mypy.build.build(
                [BuildSource(filename, None, None)],
                target=mypy.build.TYPE_CHECK,
                bin_dir=config.mypy_dir
                )
            visitor = TypeVisitor(res.types, filename)
            # for df in res.files['__main__'].defs:
            # print(df)
            res.files['__main__'].accept(visitor)
            self.all_types.update(visitor.all_types)
            return True
        except mypy.errors.CompileError as e:
            for m in e.messages:
                sys.stderr.write('Mypy error: ' + m + '\n')
            raise TypeException(e.messages)

    def get_type(self, prefix: List[str], name: str):
        """
        Looks up the inferred or annotated type for the given name in the given
        prefix
        """
        result = self.all_types.get(tuple(prefix + [name]))
        if result is None:
            if not prefix:
                return None
            else:
                return self.get_type(prefix[:len(prefix) - 1], name)
        else:
            if isinstance(result, mypy.types.Instance):
                result = result.type
            return result

    def get_func_type(self, prefix: List[str]):
        """
        Looks up the type of the function which creates the given context
        """
        result = self.all_types.get(tuple(prefix))
        if result is None:
            if len(prefix) == 0:
                return None
            else:
                return self.get_func_type(prefix[:len(prefix) - 1])
        else:
            if isinstance(result, mypy.types.FunctionLike):
                result = result.ret_type
            return result
