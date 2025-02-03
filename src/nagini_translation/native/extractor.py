import ast
import nagini_translation.native.vf.standard as vf
import nagini_translation.native.vf.pymodules as vf
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

    def setup(self, f: PythonMethod, ctx: Context) -> list[vf.fact]:
        for key, value in f.args.items():
            print(key, value)

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
