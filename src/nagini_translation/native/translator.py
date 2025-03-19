
from functools import reduce
from fractions import Fraction
from nagini_translation.lib.context import Context
from nagini_translation.native.py2vf_ctx import py2vf_context, ValueAccess, PtrAccess, ValAccess, TupleSubscriptAccess, AttrAccess
from nagini_translation.lib.program_nodes import PythonMethod, PythonType, PythonVar
import nagini_translation.native.vf.vf as vf
import nagini_translation.native.vf.pymodules as vfpy
from nagini_translation.lib.resolver import get_type as do_get_type
from typing import Optional, Type
import ast

class Translator:
    def __init__(self):
        self.predicates = dict()
        self.classes = dict()

    def translate(self, node: ast.AST, ctx: Context, py2vf_ctx: py2vf_context) -> vf.Fact:
        if (self.is_pure(node, ctx)):
            return vf.BooleanFact(self.translate_generic_expr(node, ctx, py2vf_ctx, ValAccess()))
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
                # TODO: check if these assertions are at least somehow useful?
                assert (isinstance(node.args[1], ast.BinOp))
                assert (isinstance(node.args[1].left, ast.Constant))
                assert (isinstance(node.args[1].right, ast.Constant))
                frac = Fraction(node.args[1].left.value,
                                node.args[1].right.value)
                # TODO: finish translating this
            if isinstance(node.args[0], ast.Attribute):
                return vf.FactConjunction([
                    vfpy.PyObj_HasAttr(self.translate_generic_expr(node.args[0].value, ctx, py2vf_ctx, PtrAccess()),
                                          node.args[0].attr,
                                          py2vf_ctx.getExpr(node.args[0].value.id, AttrAccess(node.args[0].attr, PtrAccess())),
                                          frac=frac),
                    self.create_hasval_fact(node.args[0].value.id,
                                            self.get_type(node.args[0], ctx),
                                            ctx,
                                            py2vf_ctx,
                                            lambda x: AttrAccess(node.args[0].attr, x)),
                ])
            else:
                raise NotImplementedError(
                    "Acc is not implemented for this content" + str(node.args[0]))
        elif (node.func.id == "list_pred"):
            raise NotImplementedError("list_pred is not implemented")
        else:
            funcid = node.func.id
            # TODO: check if each of these variables is to be used as ref or as val
            return self.predicates[funcid](*map(lambda x: self.translate_generic_expr(x, ctx, py2vf_ctx, ValAccess()), node.args))

    def translate_IfExp_fact(self, node: ast.IfExp, ctx: Context, py2vf_ctx: py2vf_context) -> vf.Fact:
        # the condition must be pure
        # but either branches could be pure or a fact (just one needs be a fact)
        return vf.TernaryFact(self.translate_generic_expr(node.test, ctx, py2vf_ctx, ValueAccess()),
                              self.translate(
                                  node.body, ctx, py2vf_context(py2vf_ctx, prefix=py2vf_ctx.getprefix())),
                              self.translate(node.orelse, ctx, py2vf_context(py2vf_ctx, prefix=py2vf_ctx.getprefix())))

    def translate_BoolOp_fact(self, node: ast.BoolOp, ctx: Context, py2vf_ctx: py2vf_context) -> vf.Fact:
        assert (type(node.op).__name__ == "And")
        return vf.FactConjunction(map(lambda x: self.translate(x, ctx, py2vf_ctx), node.values))

    def translate_generic_expr(self, node: ast.AST, ctx: Context, py2vf_ctx: py2vf_context, v: ValueAccess) -> vf.Expr:
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
            "Tuple": self.translate_Tuple_expr,
            "Subscript": self.translate_Subscript_expr
        }
        return switch_dict[type(node).__name__](node, ctx,  py2vf_ctx, v)

    def translate_Tuple_expr(self, node: ast.Tuple, ctx: Context, py2vf_ctx: py2vf_context, v: ValueAccess) -> vf.Expr:
        if (type(v) == TupleSubscriptAccess):
            # TODO: handle the case where the index is not a constant
            return self.translate_generic_expr(node.elts[v.index], ctx, py2vf_ctx, v.value)
        else:
            raise NotImplementedError("Tuple expression not implemented")

    def translate_Subscript_expr(self, node: ast.Subscript, ctx: Context, py2vf_ctx: py2vf_context, v: ValueAccess) -> vf.Expr:
        return self.translate_generic_expr(node.value, ctx, py2vf_ctx, TupleSubscriptAccess(node.slice.value, v))

    def translate_BoolOp_expr(self, node: ast.BoolOp, ctx: Context, py2vf_ctx: py2vf_context, v: ValueAccess) -> vf.Expr:
        dict = {
            "And": vf.BoolAnd,
            "Or": vf.BoolOr
        }
        operator = dict[type(node.op).__name__]
        return reduce(
            lambda x, y: vf.BinOp[vf.Bool](
                x, self.translate_generic_expr(y, ctx, py2vf_ctx, ValAccess()), operator),
            node.values[1:],
            self.translate_generic_expr(node.values[0], ctx, py2vf_ctx, ValAccess()))

    def translate_Attribute_expr(self, node: ast.Attribute, ctx: Context, py2vf_ctx: py2vf_context, v: ValueAccess) -> vf.Expr:
        return self.translate_generic_expr(node.value, ctx, py2vf_ctx, AttrAccess(node.attr, v))

    def translate_IfExp_expr(self, node: ast.IfExp, ctx: Context, py2vf_ctx: py2vf_context, v: ValueAccess) -> vf.Expr:
        # TODO: create a new py2vf_context for the branches
        return vf.TernaryOp(self.translate_generic_expr(node.test, ctx, py2vf_context(py2vf_ctx, prefix=py2vf_ctx.getprefix()), ValAccess()),
                            self.translate_generic_expr(
                                node.body, ctx, py2vf_context(py2vf_ctx, prefix=py2vf_ctx.getprefix()), v),
                            self.translate_generic_expr(node.orelse, ctx, py2vf_ctx, v))

    def translate_BinOp_expr(self, node: ast.BinOp, ctx: Context, py2vf_ctx: py2vf_context,  v: ValueAccess) -> vf.Expr:
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
            self.translate_generic_expr(
                node.left, ctx, py2vf_ctx, ValAccess()),
            self.translate_generic_expr(
                node.right, ctx, py2vf_ctx, ValAccess()),
            operator)

    def translate_Constant_expr(self, node: ast.Constant, ctx: Context, py2vf_ctx: py2vf_context,  v: ValueAccess) -> vf.Expr:
        # TODO: handle immediate values of other types here
        dict = {
            "int": vf.Int,
            "float": vf.Float,
            "bool": vf.Bool
        }
        return dict[type(node.value).__name__](node.value)

    def translate_Name_expr(self, node: ast.Name, ctx: Context, py2vf_ctx: py2vf_context,  v: ValueAccess) -> vf.Expr:
        return py2vf_ctx.getExpr(node.id, v, True)

    def translate_Compare_expr(self, node: ast.Compare, ctx: Context, py2vf_ctx: py2vf_context,  v: ValueAccess) -> vf.Expr:
        operandtype = self.get_type(node.left, ctx).name
        # TODO: any other type fitting in there?
        ptracc = PtrAccess()
        valacc = ValAccess()
        dict = {
            "Eq": (vf.Eq, valacc),
            "NotEq": (vf.NotEq, valacc),
            "Lt": (vf.Lt, valacc),
            "LtE": (vf.LtE, valacc),
            "Gt": (vf.Gt, valacc),
            "GtE": (vf.GtE, valacc),
            "Is": (vf.Eq, ptracc),
        }
        operator, acctype = dict[type(node.ops[0]).__name__]
        if (operator == vf.Eq and self.get_type(node.left, ctx) != self.get_type(node.comparators[0], ctx)):
            return vf.ImmLiteral(vf.Bool(False))
        if (operandtype in ["int", "float", "bool", "string"]):
            return vf.BinOp[vf.Bool](
                self.translate_generic_expr(
                    node.left, ctx, py2vf_ctx, acctype),
                self.translate_generic_expr(
                    node.comparators[0], ctx, py2vf_ctx, acctype),
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
                    return self.translate_generic_expr(ast.BoolOp(ast.And(), [
                        ast.Compare(left=ast.Subscript(value=node.left, slice=ast.Constant(value=i), ctx=ast.Load()),
                                    ops=[ast.Eq()],
                                    comparators=[ast.Subscript(
                                        value=node.comparators[0], slice=ast.Constant(value=i), ctx=ast.Load())],
                                    ) for i in range(len(opd_left_types))
                    ]), ctx, py2vf_ctx, v)
            elif (compname == "NotEq"):
                if (opd_left_types != opd_right_types):
                    return vf.Bool(True)
                else:
                    return self.translate_generic_expr(ast.BoolOp(ast.Or(), [
                        ast.Compare(left=ast.Subscript(value=node.left, slice=ast.Constant(value=i), ctx=ast.Load()),
                                    ops=[ast.NotEq()],
                                    comparators=[ast.Subscript(
                                        value=node.comparators[0], slice=ast.Constant(value=i), ctx=ast.Load())],
                                    ) for i in range(len(opd_left_types))
                    ]), ctx, py2vf_ctx, v)

    def create_hasval_fact(self, pyobjname: str, t: PythonType, ctx: Context, py2vf_ctx: py2vf_context, path=lambda x: x, names=[]) -> vf.Fact:
        if (t.name not in ["tuple"]):
            access = path(ValAccess())
            cntnt = {
                "int": vfpy.PyLong,
                "list": lambda x: vfpy.PyClass_List(),
            }.get(t.name, lambda x: vfpy.PyClassInstance(self.classes[t.module.sil_name+t.name]))
            pyobjval = vf.ImmInductive(cntnt(py2vf_ctx.getExpr(pyobjname if len(names)==0 else names[0], access, useprefix=len(names)==0)))
            return vfpy.PyObj_HasVal(py2vf_ctx.getExpr(pyobjname,path(PtrAccess())), pyobjval)
        elif (t.name == "tuple"):
            tupleEls = []
            tupleElNames = [py2vf_ctx.getExpr(names[i], PtrAccess(), useprefix=False) if i < len(names)
                            else py2vf_ctx.getExpr(pyobjname, path(TupleSubscriptAccess(i, PtrAccess())))for i in range(len(t.type_args))]
            for i in range(len(t.type_args)):
                tupleEls.append(vf.Pair[vfpy.PyObjPtr, vfpy.PyObj_t](
                    tupleElNames[i],
                    vf.ImmInductive(self.pytype__to__PyObj_t(t.type_args[i]))))
            pyobjval = vf.ImmInductive(
                vfpy.PyTuple(vf.List.from_list(tupleEls)))
            return vf.FactConjunction([vfpy.PyObj_HasVal(py2vf_ctx.getExpr(pyobjname,path(PtrAccess())), pyobjval)]+[
                self.create_hasval_fact(
                    names[i] if i < len(names) else pyobjname,
                    t.type_args[i],
                    ctx,
                    py2vf_ctx,
                    (lambda x: x) if i < len(names) else
                    (lambda x: path(TupleSubscriptAccess(i, x))),
                    names=[names[i]] if i < len(names) else []
                ) for i in range(len(t.type_args))
            ])
        else:
            print("NADA"+t.name)
            # raise NotImplementedError("Type not implemented")

    def pytype__to__PyObj_t(self, p: PythonType) -> vfpy.PyObj_t:
        if (p.name == 'tuple'):
            return vfpy.PyTuple_t(vf.List.from_list(list(map(lambda x: vf.ImmInductive(self.pytype__to__PyObj_t(x)), p.type_args))))
        return {
            'int': vfpy.PyLong(0).PyObj_t(),
            # TODO: this is just for testing, remove this and implement cleanly later
        }.get(p.name, vfpy.PyClass_t(self.classes.get(p.module.sil_name+p.name, "FAILED PYTYPE TRANSLATION")))

    def is_pure(self, node: ast.AST, ctx: Context) -> bool:
        # check there is an occurence of Acc or any predicate in the node (then unpure, otherwise pure)
        if (isinstance(node, ast.Call)):
            # predicates are stored in ctx.module.predicates
            return not (node.func.id in ctx.module.predicates or node.func.id in ["Acc", "list_pred"])
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
