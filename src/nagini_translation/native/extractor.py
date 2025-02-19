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
from typing import Optional, Type
from functools import reduce


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
            # raise KeyError(key)
            return None

    def __setitem__(self, key: str, value: vf.Value):
        self.context[key] = value


class Translator():
    def translate(self, node: ast.AST, ctx: Context, py2vf_ctx: py2vf_context) -> vf.Fact:
        if (self.is_pure(node, ctx)):
            return vf.BooleanFact(self.translate_generic_expr(node, ctx, py2vf_ctx))
        else:
            return self.translate_generic_fact(node, ctx, py2vf_ctx)

    def translate_generic_fact(self, node: ast.AST, ctx: Context, py2vf_ctx: py2vf_context) -> vf.Fact:
        # if(self.is_pure(node, ctx)):
        #    return vf.BooleanFact(self.translate_generic_expr(node, ctx, py2vf_ctx))
        switch_dict = {
            "Call": self.translate_Call_fact,
            "IfExp": self.translate_IfExp_fact,
            "BoolOp": self.translate_BoolOp_fact,
        }
        return switch_dict[type(node).__name__](node, ctx, py2vf_ctx)

    def translate_Call_fact(self, node: ast.Call, ctx: Context, py2vf_ctx: py2vf_context) -> vf.Fact:
        pass

    def translate_IfExp_fact(self, node: ast.IfExp, ctx: Context, py2vf_ctx: py2vf_context) -> vf.Fact:
        #the condition must be pure
        #but either branches could be pure or a fact (just one needs be a fact)
        return vf.TernaryFact(self.translate_generic_expr(node.test, ctx, py2vf_ctx),
                              self.translate(node.body, ctx, py2vf_ctx),
                              self.translate(node.orelse, ctx, py2vf_ctx))

    def translate_BoolOp_fact(self, node: ast.BoolOp, ctx: Context, py2vf_ctx: py2vf_context) -> vf.Fact:
        if (type(node).__name__ == "And"):
            return vf.FactConjunction(map(lambda x: self.translate(x, ctx, py2vf_ctx), node.values))
        else:
            raise NotImplementedError

    def translate_generic_expr(self, node: ast.AST, ctx: Context, py2vf_ctx: py2vf_context, isreference: bool = False) -> vf.Expr:
        switch_dict = {
            # "ast.Call": self.translate_Call,
            # "ast.UnaryOp": self.translate_UnaryOp,
            "IfExp": self.translate_IfExp_expr,
            "BoolOp": self.translate_BoolOp_expr,
            "BinOp": self.translate_BinOp_expr,
            "Compare": self.translate_Compare_expr,
            "Constant": self.translate_Constant_expr,
            "Name": self.translate_Name_expr
        }
        return switch_dict[type(node).__name__](node, ctx,  py2vf_ctx, isreference)

    def translate_BoolOp_expr(self, node: ast.BoolOp, ctx: Context, py2vf_ctx: py2vf_context, isreference: bool = False) -> vf.Expr:
        dict = {
            "And": vf.BoolAnd,
            "Or": vf.BoolOr
        }
        operator = dict[type(node.op).__name__]
        return reduce(
            lambda x, y: vf.BinOp[vf.Bool](
                x, self.translate_generic_expr(y, ctx, py2vf_ctx, False), operator),
            node.values[1:],
            self.translate_generic_expr(node.values[0], ctx, py2vf_ctx, False))

    def translate_IfExp_expr(self, node: ast.IfExp, ctx: Context, py2vf_ctx: py2vf_context, isreference: bool = False) -> vf.Expr:
        return vf.TernaryOp(self.translate_generic_expr(node.test, ctx, py2vf_ctx, False),
                            self.translate_generic_expr(
                                node.body, ctx, py2vf_ctx, isreference),
                            self.translate_generic_expr(node.orelse, ctx, py2vf_ctx, isreference))

    def translate_BinOp_expr(self, node: ast.BinOp, ctx: Context, py2vf_ctx: py2vf_context, isreference: bool = False) -> vf.Expr:
        dict = {
            "Add": vf.Add,
            "Sub": vf.Sub,
            "Mult": vf.Mul,
            "Div": vf.Div,
            "Mod": vf.Mod,
            # TODO"Pow": vf.Pow,
            "LShift": vf.LShift,
            "RShift": vf.RShift,
            "BitOr": vf.BitOr,
            "BitXor": vf.BitXor,
            "BitAnd": vf.BitAnd,
            "FloorDiv": vf.Div
        }
        operator = dict[type(node.op).__name__]
        return vf.BinOp[vf.Int](
            self.translate_generic_expr(node.left, ctx, py2vf_ctx, False),
            self.translate_generic_expr(node.right, ctx, py2vf_ctx, False),
            operator)

    def translate_Constant_expr(self, node: ast.Constant, ctx: Context, py2vf_ctx: py2vf_context, isreference: bool = False) -> vf.Expr:
        # TODO: handle immediate values of other types here
        dict = {
            "int": vf.Int,
            "float": vf.Float,
            "bool": vf.Bool
        }
        return dict[type(node.value).__name__](node.value)

    def translate_Name_expr(self, node: ast.Name, ctx: Context, py2vf_ctx: py2vf_context, isreference: bool = False) -> vf.Expr:
        if isreference:
            return vf.NameUseExpr[vfpy.PyObjPtr](py2vf_ctx[node.id + "_ptr"])
        else:
            # TODO: refine the type here
            return vf.NameUseExpr[vfpy.PyObj_v](py2vf_ctx[node.id + "_val"])

    def translate_Compare_expr(self, node: ast.Compare, ctx: Context, py2vf_ctx: py2vf_context, isreference: bool = False) -> vf.Expr:
        dict = {
            "Eq": (vf.Eq, False),
            "NotEq": (vf.NotEq, False),
            "Lt": (vf.Lt, False),
            "LtE": (vf.LtE, False),
            "Gt": (vf.Gt, False),
            "GtE": (vf.GtE, False),
            "Is": (vf.Eq, True),
        }
        operator, asref = dict[type(node.ops[0]).__name__]
        return vf.BinOp[vf.Bool](
            self.translate_generic_expr(node.left, ctx, py2vf_ctx, asref),
            self.translate_generic_expr(
                node.comparators[0], ctx, py2vf_ctx, asref),
            operator)

    def pytype__to__PyObj_v(self, p: PythonType) -> Type[vfpy.PyObj_v]:
        return {
            'int': vfpy.PyLong,
            # no other parent than ObjectType
            'mycoolclass': vfpy.PyClassInstance
        }[p.name]

    def pytype__to__PyObj_t(self, p: PythonType) -> vfpy.PyObj_t:
        return {
            'int': vfpy.PyLong(0).PyObj_t(),
            # no other parent than ObjectType
            'mycoolclass': vfpy.PyClass_t(vfpy.PyClass("mycoolclass", None))
        }[p.name]

    def is_mutable_arg(self, node: PythonVar) -> bool:
        switch_dict = {
            "int": False,
            "mycoolclass": True
        }
        return switch_dict[node.type.name]

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
    def setup(self, f: PythonMethod, ctx: Context, py2vf_ctx: py2vf_context) -> list[vf.Fact]:
        py2vf_ctx["args"] = vf.NamedValue("args")
        tuple_args = []
        arg_predicates = []
        for key, value in f.args.items():
            # now manually translate the arguments from PY to VF

            py2vf_ctx[key +
                      "_ptr"] = vf.NamedValue[vfpy.PyObjPtr](key + "_ptr")
            cur_arg_def = vf.NameDefExpr[vfpy.PyObjPtr](
                py2vf_ctx[key + "_ptr"])
            # translate argument to pointers
            py2vf_ctx[key + "_ptr"].setDef(cur_arg_def)
            tuple_args.append(
                vf.Pair[vfpy.PyObjPtr, vfpy.PyObj_t](
                    cur_arg_def,
                    vf.ImmInductive[vfpy.PyObj_t](
                        self.translator.pytype__to__PyObj_t(value.type))
                ))
            # translate pointers to values
            py2vf_ctx[key + "_val"] = vf.NamedValue[vfpy.PyObj_v](key + "_val")
            pyobj_content = vf.ImmInductive(self.translator.pytype__to__PyObj_v(
                value.type)(vf.NameDefExpr[vfpy.PyObj_v](py2vf_ctx[key + "_val"])))
            arg_predicates.append(
                vfpy.PyObj_HasVal(
                    vf.NameUseExpr[vfpy.PyObjPtr](py2vf_ctx[key + "_ptr"]),
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
        # self.get_type(f.node.body[0].targets[0], ctx)
        # self.get_target(f.node.body[0].targets[0], ctx)
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
