import ast
import nagini_translation.native.vf.standard as vf
import nagini_translation.native.vf.pymodules as vfpy
from nagini_translation.lib.program_nodes import PythonVar
from nagini_translation.lib.context import Context
from nagini_translation.lib.program_nodes import (
    PythonMethod,
    PythonModule,
    PythonType
)
from nagini_translation.lib.resolver import get_target as do_get_target
from nagini_translation.lib.resolver import get_type as do_get_type
from typing import Optional


class py2vf_context:
    def __init__(self):
        self.context = dict()
        self.parent = None

    def __init__(self, p: "py2vf_context" = None):
        self.context = dict()
        self.parent = p

    def __getitem__(self, key: str):
        if key in self.context:
            return self.context[key]
        elif self.parent:
            return self.parent[key]
        else:
            raise KeyError(key)

    def __setitem__(self, key: str, value: vf.VFVal):
        self.context[key] = value


class NativeSpecExtractor:
    def pytype__to__PyObj_t(self, p: PythonType) -> vfpy.PyObj_t:
        return {
            'int': vfpy.PyObj_t("PyLong_t"),
            # no other parent than ObjectType
            'mycoolclass': vfpy.PyClass_t(vfpy.PyClass("mycoolclass"))
        }[p.name]

    def setup(self, f: PythonMethod, ctx: Context) -> list[vf.Fact]:
        py2vf_ctx = py2vf_context()
        facts = []
        py2vf_ctx["args"] = vf.VFVal(vf.FromArgs("args"))
        tuple_args = []
        facts.append(vfpy.pyobj_hasval(py2vf_ctx["args"], vfpy.PyTuple([])))
        for key, value in f.args.items():
            # vfpy.pyobj_hasval(py2vf_context["ptr_" + key],)
            py2vf_ctx[key + "_ptr"] = vf.VFVal(vf.Pattern(key))
            theval = py2vf_ctx[key+"_ptr"]
            tuple_args.append(
                vf.Pair(theval.definition, self.pytype__to__PyObj_t(value.type)))

        map(lambda a: vf.Pair(vf.VFVal(vf.Pattern(a[0])),
                                  self.pytype__to__PyObj_t(a[1].type)), f.args.items())
        facts[0].obj.items = tuple_args
        print(vf.FactConjunction(facts))
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
