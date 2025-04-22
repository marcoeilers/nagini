import ast
import nagini_translation.native.vf.vf as vf
import nagini_translation.native.vf.pymodules as vfpy
import nagini_translation.native.vf.nag as vfnag
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
from nagini_translation.native.exprify import Exprifier


class NativeSpecExtractor:
    def signature(self, py2vf_ctx: py2vf_context, ctx: Context, p: ast.AST) -> Tuple[Type, Type]:
        def f(x, y): 
            py2vf_ctx.setExpr(
            ast.Name(x, ast.Load(), lineno=0, col_offset=0), y)
            return py2vf_ctx.getExpr(
            ast.Name(x, ast.Load(), lineno=0, col_offset=0), y)
        # create a named value for each argument
        
        def translate_argtype(x:str, a: AccessType):
            if isinstance(a, PtrAccess):
                return "PyObject*"
            if isinstance(a, ValAccess):
                types = {
                    "int": "int",
                    "float": "float",
                    "bool": "bool",
                    "str": "list<char>",
                }
                t=self.get_type(ast.Name(x, ast.Load(), lineno=0, col_offset=0), ctx)
                return types.get(t.name, "PyClass")
        funargs = []
        arg_accesses = []
        for(k, v) in p.args.items():
            translated_arg_access = []
            if k.startswith("VALUEONLY_") == False:
                translated_arg_access.append(PtrAccess())
            translated_arg_access.append(ValAccess())
            arg_ast_name = ast.Name(k, ast.Load(), lineno=0, col_offset=0)
            for y in translated_arg_access:
                py2vf_ctx.getExpr(arg_ast_name, y)
                funargs.append((translate_argtype(k, y) + " "+ str(py2vf_ctx.getExpr(arg_ast_name, y))))
            arg_accesses.append(translated_arg_access)
        return funargs, arg_accesses
    def env(self, modules: List[PythonModule]) -> str:
        # Class System Translation
        ctx = Context()
        res = "fixpoint PyClass PyClass_ObjectType(){\n\treturn ObjectType;\n}\n"
        for m in modules[1:]:
            for key, value in m.classes.items():
                vfname = m.sil_name+key
                self.translator.classes[vfname] = lambda x, classname=vfname: vfpy.PyClass(classname, x)
                super_typevars = value.superclass.cls.type_vars.keys() if hasattr(value.superclass, "cls") else []
                res += "fixpoint PyClass PyClass_"+vfname + \
                    "("+", ".join([("PyObj_Type "+x) for x in value.type_vars.keys()])+"){\n\treturn PyClass(\""+\
                        vfname+"\", "+\
                        (
                            "PyClass_ObjectType, nil" if (value.superclass.name == "object") else
                            "Exception, nil" if(value.superclass.name == "Exception") else 
                            "PyClass_"+((value.superclass.module.sil_name+value.superclass.name+"("+", ".join([x for x in super_typevars])+")")+", "+\
                                    str(vf.List.from_list([x for x in value.type_vars.keys() if x not in super_typevars])))
                            ) +\
                    ");\n}\n"

        def make_init_nagpureFPcall(key):
            return lambda self, *args: vfnag.NaginiPredicateFact.__init__(self, key, *args)
        for m in modules[1:]:
            ctx.module = m
            for k, f in m.functions.items():
                ctx.current_function = f
                if (any([self.translator.is_predless(p[0], ctx) == False for p in f.precondition])):
                    res += "\n//WARNING: Pure function "+f.name + \
                        " has a predicate in its precondition. => Not translated\n\n"
                else:
                    py2vf_ctx = py2vf_context()
                    predargs = self.signature(py2vf_ctx, ctx, f)[0]
                    exprifiedfunction = Exprifier().exprifyBody(
                        f.node.body, ast.Constant(value=None))
                    purefunctiontypes = [
                        "int", "float", "bool"
                    ]
                    if (f.result.type.name in purefunctiontypes):
                        # TODO the function info here
                        self.translator.functions[f.name] = type(k, (vfnag.NaginiPureFPCall,), {
                                                                 "__init__": make_init_nagpureFPcall("PURE_"+k)})
                        res += "fixpoint "+f.result.type.name+" PURE_" + \
                            f.name+"("+', '.join(predargs)+"){\n\t return "
                        res += str(self.translator.translate_generic_expr(
                            exprifiedfunction, ctx, py2vf_ctx, ValAccess()))
                        res += ";\n}\n\n"
                    else:
                        self.translator.functions[f.name] = None
                        res += "//WARNING: Function "+f.name+" has a non-C-native return type" + \
                            f.result.type.name+". => Not translated\n\n"

        # TODO: precise whether such or such argument is to be translated as ptr or val
        # Predicate Translation

        def make_init_nagpredfact(key):
            return lambda self, *args: vfnag.NaginiPredicateFact.__init__(self, key, *args)

        for m in modules:
            ctx.module = m
            for k, p in m.predicates.items():
                ctx.current_function = p
                py2vf_ctx = py2vf_context()
                self.translator.predicates[k] = type(k, (vfpy.NaginiPredicateFact,), {
                                                     "__init__": make_init_nagpredfact("PRED_"+k)})
                def ptrandval(x, y): return py2vf_ctx.getExpr(
                    ast.Name(x, ast.Load(), lineno=0, col_offset=0), y)
                # create a named value for each argument
                for y in p.args.items():
                    ptrandval(y[0], PtrAccess())
                    ptrandval(y[0], ValAccess())
                def retrieve_argtype(x:str):
                    types = {
                        "int": "int",
                        "float": "float",
                        "bool": "bool",
                        "str": "list<char>",
                    }
                    t=self.get_type(ast.Name(x, ast.Load(), lineno=0, col_offset=0), ctx)
                    return types.get(t.name, "PyClass")
                funargs = self.signature(py2vf_ctx, ctx, p)[0]
                res += "predicate PRED_"+p.name+"("+', '.join(funargs)+") = "+str(
                    self.translator.translate(p.node.body[0].value, ctx, py2vf_ctx))+";\n"
        # TODO: finish translating fixpoint functions

        return res + "/*--END OF ENV--*/\n"

    def setup(self, f: PythonMethod, ctx: Context, py2vf_ctx: py2vf_context) -> list[vf.Fact]:
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
        print("requires PyExc(none, none) &*&")
        print(vf.FactConjunction(
            setupfacts +
            [self.translator.translate(p[0], ctx, py2vf_ctx_precond)
             for p in f.precondition]
        ), end=";\n")
        print()
        print("ensures PyExc(none, none) &*&")
        py2vf_ctx_postcond = py2vf_context(
            parent=py2vf_ctx_setup, prefix="", old=py2vf_ctx_precond)
        resultcall = ast.Call(ast.Name("Result", ast.Load()), [], [])
        py2vf_ctx_postcond.setExpr(
            resultcall, PtrAccess(), vf.NamedValue("result"))
        result_hasvalfact=self.translator.create_hasval_fact(resultcall, f.result.type if f.result!=None else type(None), ctx, py2vf_ctx_postcond)
        py2vf_ctx_postcond.setprefix("NEW_")
        print(vf.FactConjunction(
            self.setup(f, ctx, py2vf_ctx_setup) +
            # TODO: this does not handle "None" return type yet
            [result_hasvalfact]
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
