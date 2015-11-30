import mypy.build
import sys
import os


def func_children(func : mypy.nodes.FuncDef, index):
    return (index, [(func.name(), func.body.body)])

def decorator_children(dec : mypy.nodes.Decorator, index):
    return func_children(dec.func, index)


def func_vars(func : mypy.nodes.FuncDef):
    functype = func.type
    if isinstance(functype, mypy.types.FunctionLike):
        functype = functype.ret_type
    return [([func.name()], functype)] + [([func.name(), arg._name], arg.type) for arg in func.args]

def decorator_vars(dec : mypy.nodes.Decorator):
    return func_vars(dec.func)


children_funcs = {mypy.nodes.FuncDef : func_children,
                  mypy.nodes.Decorator : decorator_children}
vars_funcs = {mypy.nodes.FuncDef : func_vars,
              mypy.nodes.Decorator : decorator_vars}


class TypeInfo:
    def __init__(self):
        self.allTypes = {}

    def init(self, filename, mypydir) -> bool:
        try:
            res = mypy.build.build(filename, target=mypy.build.TYPE_CHECK, bin_dir=os.path.dirname(mypydir))
            for df in res.files['__main__'].defs:
                self.traverse(df, 0, [])

            print("alltypes:")
            print(self.allTypes)
            return True
        except mypy.errors.CompileError as e:
            for m in e.messages:
                sys.stderr.write('Mypy error: ' + m + '\n')
            return False

    def traverse(self, node, index, prefix):
        vars_func = vars_funcs.get(node.__class__)
        if vars_func:
            vars = vars_func(node)
            for var in vars:
                (name, type) = var
                fullname = prefix + name
                self.allTypes[tuple(fullname)] = type
        children__func = children_funcs.get(node.__class__)
        if children__func:
            index, children = children__func(node, index)
            for child in children:
                (name, childs) = child
                contextname = name + str(index)
                newprefix = prefix + [contextname]
                for c in childs:
                    self.traverse(c, 0, newprefix)

    def gettype(self, prefix, name):
        result = self.allTypes.get(tuple(prefix + [name]))
        if result is None:
            if not prefix:
                return None
            else:
                return self.gettype(prefix[:len(prefix)-1], name)
        else:
            return result

    def getfunctype(self, prefix):
        return self.allTypes.get(tuple(prefix))

