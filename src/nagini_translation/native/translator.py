
from functools import reduce
from fractions import Fraction
from nagini_translation.lib.context import Context
from nagini_translation.native.py2vf_ctx import py2vf_context
from nagini_translation.lib.program_nodes import PythonMethod, PythonType, PythonVar
import nagini_translation.native.vf.vf as vf
import nagini_translation.native.vf.pymodules as vfpy
from nagini_translation.lib.resolver import get_type as do_get_type
from typing import Optional, Type
import ast

class Translator():
    def __init__(self):
        self.predicates = dict()

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
        if (node.func.id == "Acc"):
            frac = 1
            if len(node.args) == 2:
                assert (isinstance(node.args[1], ast.BinOp))
                assert (isinstance(node.args[1].left, ast.Constant))
                assert (isinstance(node.args[1].right, ast.Constant))
                frac = Fraction(node.args[1].left.value,
                                node.args[1].right.value)
            if isinstance(node.args[0], ast.Attribute):
                attrVFName = node.args[0].value.id + "_DOT_"+node.args[0].attr
                py2vf_ctx[attrVFName + "__ptr"] = vf.NamedValue[vfpy.PyObjPtr](
                    attrVFName + "__ptr")
                return vf.FactConjunction([
                    vfpy.PyObj_HasAttr(self.translate_generic_expr(node.args[0].value, ctx, py2vf_ctx, True),
                                          node.args[0].attr,
                                          vf.NameDefExpr(
                                              py2vf_ctx[attrVFName + "__ptr"])),
                    self.create_hasval_fact(attrVFName, self.get_type(
                        node.args[0], ctx), ctx, py2vf_ctx)
                    # ,vfpy.PyObj_HasVal(py2vf_ctx[attrVFName + "__ptr"],vf.ImmInductive(vfpy.PyObj_t("ZUUUUUT")))
                ])
            else:
                pass
            # raise NotImplementedError("Acc is not implemented")
        else:
            funcid = node.func.id
            # TODO: check if each of these variables is to be used as ref or as val
            return self.predicates[funcid](*map(lambda x: self.translate_generic_expr(x, ctx, py2vf_ctx), node.args))

    def translate_IfExp_fact(self, node: ast.IfExp, ctx: Context, py2vf_ctx: py2vf_context) -> vf.Fact:
        # the condition must be pure
        # but either branches could be pure or a fact (just one needs be a fact)
        return vf.TernaryFact(self.translate_generic_expr(node.test, ctx, py2vf_ctx),
                              self.translate(node.body, ctx, py2vf_ctx),
                              self.translate(node.orelse, ctx, py2vf_ctx))

    def translate_BoolOp_fact(self, node: ast.BoolOp, ctx: Context, py2vf_ctx: py2vf_context) -> vf.Fact:
        assert (type(node.op).__name__ == "And")
        return vf.FactConjunction(map(lambda x: self.translate(x, ctx, py2vf_ctx), node.values))

    def translate_Tuple_expr(self, node: ast.Tuple, ctx: Context, py2vf_ctx: py2vf_context, isreference: bool = False) -> vf.Expr:
        return "{immediate tuple string}"

    def translate_generic_expr(self, node: ast.AST, ctx: Context, py2vf_ctx: py2vf_context, isreference: bool = False) -> vf.Expr:
        switch_dict = {
            # "ast.Call": self.translate_Call,
            # "ast.UnaryOp": self.translate_UnaryOp,
            "IfExp": self.translate_IfExp_expr,
            "BoolOp": self.translate_BoolOp_expr,
            "BinOp": self.translate_BinOp_expr,
            "Compare": self.translate_Compare_expr,
            "Constant": self.translate_Constant_expr,
            "Name": self.translate_Name_expr,
            "Attribute": self.translate_Attribute_expr,
            "Tuple": self.translate_Tuple_expr
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

    def translate_Attribute_expr(self, node: ast.Attribute, ctx: Context, py2vf_ctx: py2vf_context, isreference: bool = False) -> vf.Expr:
        if isreference:
            return vf.NameUseExpr[vfpy.PyObjPtr](py2vf_ctx[node.value.id + "." + node.attr + "__ptr"])
        else:
            return vf.NameUseExpr[vfpy.PyObj_v](py2vf_ctx[node.value.id + "." + node.attr + "__val"])

    def translate_IfExp_expr(self, node: ast.IfExp, ctx: Context, py2vf_ctx: py2vf_context, isreference: bool = False) -> vf.Expr:
        # TODO: create a new py2vf_context for the branches
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
        # TODO: handle mutable-case of these binops (like list+list)
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
            return vf.NameUseExpr[vfpy.PyObjPtr](py2vf_ctx[node.id + "__ptr"])
        else:
            # TODO: refine the type here
            return vf.NameUseExpr[vfpy.PyObj_v](py2vf_ctx[node.id + "__val"])

    def translate_Compare_expr(self, node: ast.Compare, ctx: Context, py2vf_ctx: py2vf_context, isreference: bool = False) -> vf.Expr:
        operandtype = self.get_type(node.left, ctx).name
        # TODO: any other type fitting in there?
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
        if (operandtype in ["int", "float", "bool", "string"]):
            return vf.BinOp[vf.Bool](
                self.translate_generic_expr(node.left, ctx, py2vf_ctx, asref),
                self.translate_generic_expr(
                    node.comparators[0], ctx, py2vf_ctx, asref),
                operator)
        elif operandtype == "tuple":
            # TODO: handle tuple comparison? eq, neq, lex>, lex<, lex>=, lex<=. For lex, shorter is considered smaller
            compname = type(node.ops[0]).__name__
            opd_left_types = self.get_type(node.left, ctx).type_args
            opd_right_types = self.get_type(node.comparators[0], ctx).type_args
            if (compname == "Eq"):
                if (opd_left_types != opd_right_types):
                    return vf.Bool(False)
                else:
                    return
                    return vf.FactConjunction(map(lambda x, y: self.translate_Compare_expr(ast.Compare(
                        left=x, ops=[node.ops[0]], comparators=[y]), ctx, py2vf_ctx, asref), zip(node.left.elts, node.comparators[0].elts)))
    def pytype__to__PyObj_v(self, p: PythonType) -> Type[vfpy.PyObj_v]:
        return {
            'int': vfpy.PyLong,
            'tuple': vfpy.PyTuple,
            # TODO: this is just for testing, remove this and implement cleanly later
            'mycoolclass': vfpy.PyClassInstance,
            'mytupledclass': vfpy.PyClassInstance
        }[p.name]

    def create_hasval_fact(self, pyobjname: str, t: PythonType, ctx: Context, py2vf_ctx: py2vf_context) -> vf.Fact:
        if (t.name == "int"):
            py2vf_ctx[pyobjname+"__val"] = vf.NamedValue(pyobjname+"__val")
            pyobjval = vf.ImmInductive(vfpy.PyLong(vf.NameUseExpr(
                py2vf_ctx[pyobjname+"__val"])))
        elif (t.name == "tuple"):
            tupleEls = []
            for i in range(len(t.type_args)):
                tupleElName = pyobjname+"_AT"+str(i)
                py2vf_ctx[tupleElName+"__ptr"] = vf.NamedValue[vfpy.PyObjPtr](
                    tupleElName+"__ptr")
                tupleEls.append(vf.Pair[vfpy.PyObjPtr, vfpy.PyObj_t](
                    vf.NameDefExpr[vfpy.PyObjPtr](
                        py2vf_ctx[tupleElName+"__ptr"]),
                    vf.ImmInductive(self.pytype__to__PyObj_t(t.type_args[i]))))
            pyobjval = vf.ImmInductive(
                vfpy.PyTuple(vf.List.from_list(tupleEls)))
        else:
            raise NotImplementedError("Type not implemented")
            return

        return vfpy.PyObj_HasVal(py2vf_ctx[pyobjname+"__ptr"], pyobjval)

    def pytype__to__PyObj_t(self, p: PythonType) -> vfpy.PyObj_t:
        if (p.name == 'tuple'):
            return vfpy.PyTuple_t(vf.List.from_list(map(lambda x: vf.ImmInductive(self.pytype__to__PyObj_t(x)), p.type_args))),
        return {
            'int': vfpy.PyLong(0).PyObj_t(),
            # TODO: this is just for testing, remove this and implement cleanly later
            'mycoolclass': vfpy.PyClass_t(vfpy.PyClass("mycoolclass", None)),
            'mytupledclass': vfpy.PyClass_t(vfpy.PyClass("mytupledclass", None))
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
