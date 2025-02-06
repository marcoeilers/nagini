import ast
import nagini_translation.native.vf.standard as vf
import nagini_translation.native.vf.pymodules as vfpy
from build.lib.nagini_translation.lib.program_nodes import PythonVar
from nagini_translation.lib.context import Context
from nagini_translation.lib.program_nodes import (
    PythonMethod,
    PythonModule,
    PythonType
)
from nagini_translation.lib.resolver import get_target as do_get_target
from nagini_translation.lib.resolver import get_type as do_get_type
from typing import Optional


class NativeSpecExtractor:
    def pytype__to__PyObj_t(self, p: PythonType):
        return {
            'int': 'PyLong_t',
            'mycoolclass': 'PyClassInstance_v("mycoolclass", ObjectType)'
        }[p.name]

    def py_to_vf(self, p: PythonVar):
        if p.type.name == 'int':
            #if the var name is in the VFcontext, simply recover the corresponding val name
            #otherwise create val_pattern (which must be initialized at the beginning of the VFcontext's scope)
                #exception to initializing at the beginning of the VFcontext's scope is if the var is a function argument
            vf_val=vf.val_pattern(p.name)
            return vfpy.PyLong(vf_val)
        # here list any other immutable native type that could comme in
        else:
            return vfpy.PyClassInstance(vfpy.PyClass(p.type.name))

    def setup(self, f: PythonMethod, ctx: Context) -> list[vf.fact]:
        tuple_entries = 
        hasval_sequence = vf.fact_conjunction(list(map(lambda a: vfpy.PyObj_HasVal(
            vf.val_pattern("ptr"+a[0]), self.py_to_vf(a[1])), f.args.items())))
        print()
        # for key, value in f.args.items():
        #    print(key, value)

        pytuple_entries = ", \n\t".join(list(
            map(lambda a: "(?arg_"+a[0]+"_ptr"+","+self.pytype__to__PyObj_t(a[1].type)+")", f.args.items())))
        return

    def __init__(self, f: PythonMethod, ctx: Context):
        # self.get_type(f.node.body[0].targets[0], ctx)
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
