import ast
import nagini_translation.native.vf.vf as vf
import nagini_translation.native.vf.pymodules as vfpy
from nagini_translation.lib.context import Context
from nagini_translation.lib.program_nodes import (
    PythonMethod,
    PythonModule,
    PythonType,
    PythonVar
)
from nagini_translation.lib.resolver import get_target as do_get_target
from nagini_translation.lib.resolver import get_type as do_get_type
from typing import Optional


class py2vf_context:
    def __init__(self, p: "py2vf_context" = None):
        self.context = dict()
        self.parent = p
        self.setup = []

    def __getitem__(self, key: str):
        if key in self.context:
            return self.context[key]
        elif self.parent:
            return self.parent[key]
        else:
            return None

    def __setitem__(self, key: str, value: vf.Value):
        self.context[key] = value


class Translator():
    def is_mutable_arg(self, node: PythonVar) -> bool:
        switch_dict = {
            "int": False,
            "mycoolclass": True
        }
        return switch_dict[node.type.name]

    def translate_generic(self, node: ast.AST, ctx: Context, isreference: bool) -> vf.Fact:
        raise NotImplementedError()

    def is_pure(self, node: ast.AST, ctx: Context) -> bool:
        # check there is an occurence of Acc or any predicate in the node (then unpure, otherwise pure)
        if (isinstance(node, ast.Call)):
            # predicates are stored in ctx.module.predicates
            return not (node.func.id in ctx.module.predicates or node.func.id == "Acc")
        elif (isinstance(node, ast.UnaryOp)):
            return self.is_pure(node.operand, ctx)
        elif (isinstance(node, ast.IfExp)):
            return self.is_pure(node.body, ctx) and self.is_pure(node.orelse, ctx)
        elif (isinstance(node, ast.BoolOp)):
            return all([self.is_pure(x, ctx) for x in node.values])
        else:
            # BinOp, Compare, Constant, Name
            return True


class NativeSpecExtractor:
    def pytype__to__PyObj_t(self, p: PythonType) -> vfpy.PyObj_t:
        return {
            'int': vfpy.PyObj_t("PyLong_t"),
            # no other parent than ObjectType
            'mycoolclass': vfpy.PyClass_t(vfpy.PyClass("mycoolclass", None))
        }[p.name]

    def setup(self, f: PythonMethod, ctx: Context, py2vf_ctx: py2vf_context) -> list[vf.Fact]:
        args_val = vf.NamedValue("args")
        py2vf_ctx["args"] = args_val 
        tuple_args = []
        for key, value in f.args.items():
            # now manually translate the arguments from PY to VF

            py2vf_ctx[key +
                      "_ptr"] = vf.NamedValue(key + "_ptr")
            cur_arg_def = vf.NameDefExpr[vfpy.PyObjPtr](
                py2vf_ctx[key + "_ptr"])
            py2vf_ctx[key + "_ptr"].setDef(cur_arg_def)
            tuple_args.append(
                vf.Pair[vfpy.PyObjPtr, vfpy.PyObj_v](
                    cur_arg_def,
                    vf.ImmInductive[vfpy.PyObj_t](
                        self.pytype__to__PyObj_t(value.type))

                )
            )
        firstpredfact = vfpy.PyObj_HasVal(
            vf.NameUseExpr[vfpy.PyObjPtr](py2vf_ctx["args"]),
            vf.ImmInductive(vfpy.PyTuple(vf.List.from_list(tuple_args)))
        )
        print(firstpredfact)
        return

    def precond(self, f: PythonMethod, ctx: Context, py2vf_ctx: py2vf_context) -> list[vf.Fact]:
        # only keep the preconditions: calls to Require

        for p, q in f.precondition:
            # print(self.translator.translate_generic(p.value.args[0], ctx))
            # print(list(map(str,p.values)))
            # print(self.translator.is_pure(p, ctx))
            print(self.translator.translate_generic(p, ctx, False))
            pass
        # print(f.node.body.value.func.id)
        return []

    def __init__(self, f: PythonMethod, ctx: Context):
        py2vf_ctx = py2vf_context()
        self.translator = Translator()
        # self.get_type(f.node.body[0].targets[0], ctx)
        # self.get_target(f.node.body[0].targets[0], ctx)
        self.setup(f, ctx, py2vf_ctx)
        # self.precond(f, ctx, py2vf_ctx)
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
