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
            'mycoolclass': vfpy.PyObj_t("PyClassInstance_v("+str(vfpy.PyClass("mycoolclass", None))+")")
        }[p.name]

    def pyvar__to__PyObj_v(self, p: PythonVar) -> tuple[vfpy.PyObj_v, object]:
        if p.type.name == "int":
            thevar = vf.VFVal(vf.Pattern(p.name+"_val"))
            self.py2vf_ctx[p.name+"_val"] = thevar
            return (vfpy.PyLong(thevar.definition), thevar)
        elif p.type.name == "mycoolclass":
            thevar = vf.VFVal(vf.Pattern(p.name+"_val"))
            return (vfpy.PyClassInstance(vfpy.PyClass("mycoolclass", None)), None)

    def setup(self, f: PythonMethod, ctx: Context) -> list[vf.Fact]:
        self.py2vf_ctx["args"] = vf.VFVal(vf.FromArgs("args"))
        tuple_args = []
        for key, value in f.args.items():
            # vfpy.pyobj_hasval(py2vf_context["ptr_" + key],)
            self.py2vf_ctx[key + "_ptr"] = vf.VFVal(vf.Pattern(key+"_ptr"))
            tuple_args.append(
                vf.Pair(self.py2vf_ctx[key+"_ptr"].definition, self.pytype__to__PyObj_t(value.type)))
        facts = [vfpy.pyobj_hasval(
            self.py2vf_ctx["args"], vfpy.PyTuple(tuple_args))]
        for key, value in f.args.items():
            p, v = self.pyvar__to__PyObj_v(value)
            if (v is not None):
                self.py2vf_ctx[key+"_val"] = v
            facts.append(vfpy.pyobj_hasval(self.py2vf_ctx[key+"_ptr"], p))
        print(vf.FactConjunction(facts))
        return

    def __init__(self, f: PythonMethod, ctx: Context):
        self.py2vf_ctx = py2vf_context()
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
