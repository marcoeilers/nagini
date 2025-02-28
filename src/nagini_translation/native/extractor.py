import ast
import nagini_translation.native.vf.vf as vf
import nagini_translation.native.vf.pymodules as vfpy
from nagini_translation.native.py2vf_ctx import py2vf_context
from nagini_translation.native.translator import *
from nagini_translation.lib.context import Context
from nagini_translation.lib.program_nodes import (
    PythonMethod,
    PythonModule,
    PythonType,
    PythonVar
)
from nagini_translation.lib.resolver import get_target as do_get_target
from nagini_translation.lib.resolver import get_type as do_get_type
from typing import Optional, Type



class NativeSpecExtractor:
    def env(self, m: PythonModule, ctx: Context) -> str:
        # res = ""
        # for key, value in m.classes.items():
        #    res += "fixpoint PyClass"
        # setup predicates in the translator
        # TODO: precise whether such or such argument is to be translated as ptr or val
        def make_init(key):
            return lambda self, *args: vf.NaginiPredicateFact.__init__(self, key, *args)
        for key, value in m.predicates.items():
            self.translator.predicates[key] = type(
                key, (vf.NaginiPredicateFact,), {"__init__": make_init(key)})
        pass

    def setup(self, f: PythonMethod, ctx: Context, py2vf_ctx: py2vf_context) -> list[vf.Fact]:
        py2vf_ctx["args"] = vf.NamedValue("args")
        tuple_args = []
        arg_predicates = []
        for key, value in f.args.items():
            # now manually translate the arguments from PY to VF

            py2vf_ctx[key +
                      repr(PtrAccess())] = vf.NamedValue[vfpy.PyObjPtr](key + str(PtrAccess()))
            cur_arg_def = vf.NameDefExpr[vfpy.PyObjPtr](
                py2vf_ctx[key + repr(PtrAccess())])
            # translate argument to pointers
            py2vf_ctx[key +repr(PtrAccess())].setDef(cur_arg_def)
            tuple_args.append(
                vf.Pair[vfpy.PyObjPtr, vfpy.PyObj_t](
                    cur_arg_def,
                    vf.ImmInductive[vfpy.PyObj_t](
                        self.translator.pytype__to__PyObj_t(value.type))
                ))
            # translate pointers to values
            py2vf_ctx[key +
                      repr(ValAccess())] = vf.NamedValue[vfpy.PyObj_v](key + str(ValAccess()))
            pyobj_content = vf.ImmInductive(self.translator.pytype__to__PyObj_v(
                value.type)(vf.NameDefExpr[vfpy.PyObj_v](py2vf_ctx[key + repr(ValAccess())])))
            arg_predicates.append(
                vfpy.PyObj_HasVal(
                    vf.NameUseExpr[vfpy.PyObjPtr](py2vf_ctx[key + repr(PtrAccess())]),
                    pyobj_content
                ))
        firstpredfact = vfpy.PyObj_HasVal(
            vf.NameUseExpr[vfpy.PyObjPtr](py2vf_ctx["args"]),
            vf.ImmInductive(vfpy.PyTuple(vf.List.from_list(tuple_args)))
        )
        return [firstpredfact]+arg_predicates

    def precond(self, f: PythonMethod, ctx: Context, py2vf_ctx: py2vf_context) -> list[vf.Fact]:
        precondfacts = []
        for p, q in f.precondition:
            precondfacts.append(self.translator.translate(p, ctx, py2vf_ctx))
        return precondfacts

    def __init__(self, f: PythonMethod, ctx: Context):
        py2vf_ctx = py2vf_context()
        self.translator = Translator()
        somearg = list(f.args.items())[0][1].type
        #print(somearg)
        #tupletype = self.get_type(
        #    f.precondition[0][0].values[1].comparators[0], ctx)
        #print(tupletype)
        #print(self.get_type(
        #    f.precondition[0][0].values[1].comparators[0], ctx).type_args)
        # CONCLUSION: get_type can be used to retrieve the type of an expression in a precond, WOohoo!
        # self.get_type(f.node.body[0].targets[0], ctx)
        # self.get_target(f.node.body[0].targets[0], ctx)
        print(self.env(ctx.module, ctx))
        print(vf.FactConjunction(self.setup(f, ctx, py2vf_ctx) +
              self.precond(f, ctx, py2vf_ctx)))
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
