import ast
import string
from nagini_translation.lib.context import Context
from nagini_translation.lib.program_nodes import (
    PythonMethod,
    PythonModule,
    PythonType
)
from nagini_translation.lib.resolver import get_target as do_get_target
from nagini_translation.lib.resolver import get_type as do_get_type
from typing import Optional


class VF_expr:
    pass
class VF_PyObj_t(VF_expr):
    pass
class VF_PyObj_v(VF_expr):
    pass
class VF_PyLong_v(VF_PyObj_v):
    def __init__(self, value:int):
        self.value = value
    def __str__(self):
        return "PyLong_v("+str(self.value)+")"
class VF_PyFloat_v(VF_PyObj_v):
    def __init__(self, value:float):
        self.value = value
    def __str__(self):
        return "PyFloat_v("+str(self.value)+")"
class VF_PyUnicode_v(VF_PyObj_v):
    def __init__(self, value:str):
        self.value = value
    def __str__(self):
        return "PyUnicode_v(\""+self.value+"\")"
class VF_PyClass():
    def __init__(self, name:str, superclass:"VF_PyClass"=None):
        self.name = name
        self.superclass = superclass
    def __init__(self):
        self.name = "object"
        self.superclass = None
    def __str__(self):
        if(self.superclass is not None):
            return "PyClass(\""+self.name+"\", "+str(self.superclass)+")"
        else:
            return "ObjectType"
            
class VF_PyClassInstance_v(VF_PyObj_v):
    def __init__(self, cls:VF_PyClass):
        self.cls = cls
    def __str__(self):
        return "PyClassInstance_v("+str(self.cls)+")"


#    PyClassInstance_v(PyClass) |
#    PyType_v(PyObj_Type) |
#    PyExc_v(PyExc_Raised_Val) |
#    PyTuple_v(list< pair<PyObject *, PyObj_Type> >) |
#    None_v;
class VF_pair(VF_expr):
    def __init__(self, e1:VF_expr, e2:VF_expr):
        self.e1 = e1
        self.e2 = e2
    def __str__(self):
        return "pair("+str(self.e1)+", "+str(self.e2)+")"
class VF_fact:
    pass
class VF_fact_pred(VF_fact):#a fact built using a predicate
    def __init__(self, args: [VF_expr]):
        self.args = args
class VF_fact_eq(VF_fact):#a fact built using an equality
    def __init__(self, e1:VF_expr, e2:VF_expr):
        self.e1 = e1
        self.e2 = e2
class VF_statement():
    def __init__(self, f:list[VF_fact]):
        self.f = f
    def __str__(self)->string:
        return " &*&\n".join(map(str, self.f))
class NativeSpecExtractor:
    def pytype__to__PyObj_t(self, p: PythonType):
        #TODO: fix the implementation for user-defined python classes later
        return {
            'int': 'PyLong_t',
            'mycoolclass': 'PyClassInstance_v("mycoolclass", ObjectType)'
        }[p.name]
    def setup(self, f: PythonMethod, ctx: Context) -> string:
        print(self.get_type(f.node.args.args[0].annotation,ctx))
        for value in f.node.args.args:
            #print(value)
            thetype=self.get_type(value.annotation, ctx)
            print(value, thetype.name)
        pytuple_entries= ", \n\t".join(list(map(lambda v: "pair(?arg_"+v.arg+"_ptr, "+self.pytype__to__PyObj_t(self.get_type(v.annotation, ctx))+")",
                       f.node.args.args)))
        main_tuple="pyobj_hasval(PyTuple_v(\n\t"+pytuple_entries+"\n))"

        print(main_tuple)


    def __init__(self, f: PythonMethod, ctx: Context):
        print("Hello")
        print(self.get_type(f.node.body[0].targets[0], ctx))
        print(self.get_target(f.node.body[0].targets[0], ctx))
        print(f.node.args.args[0])
        print(self.get_type(f.node.args.args[0].annotation, ctx))
        # self.get_target(f.node.body[0].targets[0], ctx)
        self.setup(f, ctx)
        pass

    def extract(self) -> None:
        pass


    def get_target(self, node: ast.AST, ctx: Context) -> PythonModule:
        container = ctx.actual_function if ctx.actual_function else ctx.module
        containers = [ctx]
        if ctx.current_class:
            containers.append(ctx.current_class)
        if isinstance(container, PythonMethod):
            containers.append(container)
            containers.extend(container.module.get_included_modules())
        else:
            # Assume module
            containers.extend(container.get_included_modules(()))
        result = do_get_target(node, containers, container)
        return result

    def get_type(self, node: ast.AST, ctx: Context) -> Optional[PythonType]:
        """
        Returns the type of the expression represented by node as a PythonType,
        or None if the type is void.
        """
        container = ctx.actual_function if ctx.actual_function else ctx.module
        containers = [ctx]
        if ctx.current_class:
            containers.append(ctx.current_class)
        if isinstance(container, PythonMethod):
            containers.append(container)
            containers.extend(container.module.get_included_modules())
        else:
            # Assume module
            containers.extend(container.get_included_modules())
        return do_get_type(node, containers, container)
