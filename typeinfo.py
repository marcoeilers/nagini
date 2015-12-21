import mypy.build
import os
import sys

from typing import List, Tuple


def func_children(func: mypy.nodes.FuncDef) -> List[
    Tuple[str, mypy.nodes.Node]]:
    return [(func.name(), func.body.body)]


def decorator_children(dec: mypy.nodes.Decorator) -> List[
    Tuple[str, mypy.nodes.Node]]:
    return func_children(dec.func)


def if_children(ifelse: mypy.nodes.IfStmt) -> List[Tuple[str, mypy.nodes.Node]]:
    return [('', ifelse.body), ('', ifelse.else_body.body)]


def while_children(whl: mypy.nodes.WhileStmt) -> List[
    Tuple[str, mypy.nodes.Node]]:
    return [('', whl.body.body)]


def block_children(block: mypy.nodes.Block) -> List[
    Tuple[str, mypy.nodes.Node]]:
    return [('', block.body)]


def func_vars(func: mypy.nodes.FuncDef) -> List[
    Tuple[List[str], mypy.types.Type]]:
    functype = func.type
    if isinstance(functype, mypy.types.FunctionLike):
        functype = functype.ret_type
    return [([func.name()], functype)] + [([func.name(), arg.name()], arg.type)
                                          for arg in func.args]


def decorator_vars(dec: mypy.nodes.Decorator) -> List[
    Tuple[List[str], mypy.types.Type]]:
    return func_vars(dec.func)


def assignment_vars(ass: mypy.nodes.AssignmentStmt) -> List[
    Tuple[List[str], mypy.types.Type]]:
    return map(lambda var: ([var.name], var.node.type), ass.lvalues)


children_funcs = {mypy.nodes.FuncDef: func_children,
                  mypy.nodes.Decorator: decorator_children,
                  mypy.nodes.IfStmt: if_children,
                  mypy.nodes.WhileStmt: while_children,
                  mypy.nodes.Block: block_children}

vars_funcs = {mypy.nodes.FuncDef: func_vars,
              mypy.nodes.Decorator: decorator_vars,
              mypy.nodes.AssignmentStmt: assignment_vars}


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
            for df in res.files['__main__'].defs:
                self.traverse(df, [])
            return True
        except mypy.errors.CompileError as e:
            for m in e.messages:
                sys.stderr.write('Mypy error: ' + m + '\n')
            return False

    def traverse(self, node: mypy.nodes.Node, prefix: List[str]):
        """
        Traverses the given node and its subnodes and collects all relevant type
        information, divides by prefixes, into self.allTypes
        """
        vars_func = vars_funcs.get(node.__class__)
        if vars_func:
            vars = vars_func(node)
            for var in vars:
                (name, type) = var
                fullname = prefix + name
                self.allTypes[tuple(fullname)] = type
        children_func = children_funcs.get(node.__class__)
        if children_func:
            children = children_func(node)
            for child in children:
                (name, childs) = child
                if not name == '':
                    contextname = name
                    newprefix = prefix + [contextname]
                else:
                    newprefix = prefix
                for c in childs:
                    self.traverse(c, newprefix)

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
            return result

    def getfunctype(self, prefix: List[str]):
        """
        Looks up the type of the function which creates the given context
        """
        result = self.allTypes.get(tuple(prefix))
        if result is None:
            return self.getfunctype(prefix[:len(prefix) - 1])
        else:
            return result
