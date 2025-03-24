import ast
import nagini_translation.native.vf.vf as vf
import nagini_translation.native.vf.pymodules as vfpy
from nagini_translation.native.py2vf_ctx import py2vf_context
from nagini_translation.native.translator import *
from nagini_translation.lib.context import Context
from nagini_translation.lib.program_nodes import (
    PythonMethod,
    PythonModule,
    PythonType)
from nagini_translation.lib.resolver import get_target as do_get_target
from nagini_translation.lib.resolver import get_type as do_get_type
from typing import Optional, Type, Tuple, List
from itertools import chain


class NativeSpecExtractor:
    def env(self, modules: List[PythonModule]) -> str:
        # Class System Translation
        res = "fixpoint PyClass PyClass_ObjectType(){\n\treturn ObjectType;\n}\n"
        for m in modules[1:]:
            for key, value in m.classes.items():
                vfname = m.sil_name+key
                self.translator.classes[vfname] = vfpy.PyClass(vfname)
                res += "fixpoint PyClass PyClass_"+vfname + \
                    "(){\n\treturn PyClass(\""+vfname+"\", PyClass_"+("ObjectType" if (value.superclass.name == "object") else value.superclass.name) +\
                    ");\n}\n"
        # TODO: precise whether such or such argument is to be translated as ptr or val
        # Predicate Translation

        def make_init(key):
            return lambda self, *args: vf.NaginiPredicateFact.__init__(self, key, *args)
        for key, value in m.predicates.items():
            self.translator.predicates[key] = type(
                key, (vf.NaginiPredicateFact,), {"__init__": make_init(key)})
        for m in modules:
            for p in m.predicates.values():
                ctx = Context()
                ctx.module = m
                ctx.current_function = p
                py2vf_ctx = py2vf_context()
                def somefun(x, y): return py2vf_ctx.getExpr(
                    ast.Name(x, ast.Load(), lineno=0, col_offset=0), y)
                #create a named value for each argument
                for y in p.args.items():
                    somefun(y[0], PtrAccess())
                    somefun(y[0], ValAccess())
                predargs = map(str, list(chain.from_iterable(
                    [(somefun(y[0], PtrAccess()), somefun(y[0], ValAccess())) for y in p.args.items()])))
                res += "predicate PRED_"+p.name+"("+', '.join(predargs)+") = "+str(self.translator.translate(p.node.body[0].value, ctx, py2vf_ctx))+";\n"
                pass
                # res += self.translator.translate(p, Context(m), py2vf_context())
        # TODO: finish translating fixpoint functions

        return res + "/*--END OF ENV--*/\n"

    def setup(self, f: PythonMethod, ctx: Context, py2vf_ctx: py2vf_context) -> list[vf.Fact]:
        # TODO: note that the setup must be simply reused as is for the postcond (just ensure name defs are removed)
        py2vf_ctx["args"+repr(PtrAccess())] = vf.NamedValue("args")
        return [self.translator.create_hasval_fact(ast.Name(
            "args", ast.Load(), lineno=0, col_offset=0),
            self.get_type(ast.Tuple(list(map(
                lambda x: ast.Name(
                    x[0], ast.Load(), lineno=0, col_offset=0),
                f.args.items()))), ctx),
            ctx, py2vf_ctx, names=list(map(lambda x: ast.Name(
                x[0], ast.Load(), lineno=0, col_offset=0), f.args.items())))]

    def extract(self, f: PythonMethod, ctx: Context):
        py2vf_ctx_setup = py2vf_context(prefix="")
        setupfacts = self.setup(f, ctx, py2vf_ctx_setup)
        py2vf_ctx_precond = py2vf_context(parent=py2vf_ctx_setup, prefix="")
        print("requires ", end="")
        print(vf.FactConjunction(
            setupfacts +
            [self.translator.translate(p[0], ctx, py2vf_ctx_precond)
             for p in f.precondition]
        ), end=";\n")
        print()
        print("ensures ", end="")
        py2vf_ctx_postcond = py2vf_context(
            parent=py2vf_ctx_setup, prefix="NEW_", old=py2vf_ctx_precond)
        resultcall = ast.Call(ast.Name("Result", ast.Load()), [], [])
        py2vf_ctx_setup.setExpr(
            resultcall, PtrAccess(), vf.NamedValue("result"))
        print(vf.FactConjunction(
            self.setup(f, ctx, py2vf_ctx_setup) +
            # TODO: this does not handle "None" return type yet
            [self.translator.create_hasval_fact(
                resultcall, f.result.type, ctx, py2vf_ctx_setup)]
            + [self.translator.translate(p[0], ctx, py2vf_ctx_postcond)
               for p in f.postcondition]
        ), end=";\n")
        print("/*----*/")
        pass

    def __init__(self, all_modules: List[PythonModule]) -> None:
        self.translator = Translator()
        self.all_modules = all_modules
        theenv = self.env(self.all_modules)
        print(theenv)
        # generate global stuff, e.g. iterate over all classes from all modules.

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
