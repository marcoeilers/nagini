
from functools import reduce
from fractions import Fraction
from nagini_translation.lib.context import Context
from nagini_translation.native.py2vf_ctx import py2vf_context, ValueAccess, PtrAccess, ValAccess, TupleSubscriptAccess, AttrAccess, CtntAccess
from nagini_translation.lib.program_nodes import PythonMethod, PythonType, PythonVar
import nagini_translation.native.vf.vf as vf
import nagini_translation.native.vf.pymodules as vfpy

from nagini_translation.lib.resolver import get_type as do_get_type
from typing import Optional, Type
from itertools import chain
import ast


class Translator:
    def __init__(self):
        self.predicates = dict()
        self.functions = dict()
        self.classes = dict()

    def translate(self, node: ast.AST, ctx: Context, py2vf_ctx: py2vf_context) -> vf.Fact:
        if (self.is_predless(node, ctx)):
            return vf.BooleanFact(self.translate_generic_expr(node, ctx, py2vf_ctx, ValAccess()))
        else:
            return self.translate_generic_fact(node, ctx, py2vf_ctx)

    def translate_generic_fact(self, node: ast.AST, ctx: Context, py2vf_ctx: py2vf_context) -> vf.Fact:
        # if(self.is_predless(node, ctx)):
        #    return vf.BooleanFact(self.translate_generic_expr(node, ctx, py2vf_ctx))
        switch_dict = {
            ast.Call: self.translate_Call_fact,
            ast.IfExp: self.translate_IfExp_fact,
            ast.BoolOp: self.translate_BoolOp_fact,
        }
        return switch_dict[type(node)](node, ctx, py2vf_ctx)

    def getWrapperStr(self, t: type) -> str:
        if (t.name == "int"):
            return "PyLong_wrap"
        elif (t.name == "float"):
            return "PyFloat_wrap"
        elif (t.name == "bool"):
            return "PyBool_wrap"
        else:
            return "PyClassInstance_wrap"

    def indexify_forall(self, node: ast.Call, ctx: Context, py2vf_ctx: py2vf_context) -> ast.Call:
        class TransformName(ast.NodeTransformer):
                        def visit_Name(self, vnode):
                            if vnode.id == node.args[1].args.args[0].arg:
                                return ast.Subscript(
                                    value=node.args[0],
                                    slice=ast.Name(id="_i", ctx=ast.Load()),
                                    ctx=ast.Load()
                                )
                            else:
                                return vnode
        rewrittenbody = TransformName().visit(node.args[1].body)
        rewritten = ast.Call(
            func=ast.Name(id="Forall", ctx=ast.Load()),
            args=[
                ast.Name(id="int",
                         ctx=ast.Load(),
                         lineno=node.lineno,
                         ),
                ast.Lambda(
                    args=ast.arguments(
                        posonlyargs=[],
                        kwonlyargs=[],
                        defaults=[],
                        args=[ast.arg(arg="_i", annotation=None)]),
                    body=ast.Call(
                        func=ast.Name(
                            id="Implies", ctx=ast.Load()),
                        args=[
                            ast.BoolOp(op=ast.And(),
                                       values=[
                                ast.Compare(left=ast.Name(id="_i", ctx=ast.Load()),
                                            ops=[ast.GtE()],
                                            comparators=[
                                    ast.Constant(value=0)]
                                ),
                                ast.Compare(left=ast.Name(id="_i", ctx=ast.Load()), ops=[ast.LtE()], comparators=[
                                    ast.Call(func=ast.Name(id="len", ctx=ast.Load()), args=[node.args[0]], keywords=[])])
                            ]
                            ),
                            rewrittenbody
                        ],
                        keywords=[],
                    )
                )
            ],
            keywords=[],
        )
        return rewritten
        # print(ast.unparse(rewrittenbody))
        # print(ast.unparse(rewritten))
        
    def translate_Call_fact(self, node: ast.Call, ctx: Context, py2vf_ctx: py2vf_context) -> vf.Fact:
        if (node.func.id == "Acc"):
            frac = 1
            if len(node.args) == 2:
                if (isinstance(node.args[1], ast.BinOp)) and (isinstance(node.args[1].left, ast.Constant)) and (isinstance(node.args[1].right, ast.Constant)):
                    frac = Fraction(node.args[1].left.value,
                                    node.args[1].right.value)
                else:
                    raise NotImplementedError(
                        "Acc with non-constant fraction not implemented")
            if isinstance(node.args[0], ast.Attribute):
                return vf.FactConjunction([
                    vfpy.PyObj_HasAttr(self.translate_generic_expr(node.args[0].value, ctx, py2vf_ctx, PtrAccess()),
                                          node.args[0].attr,
                                          py2vf_ctx.getExpr(
                                              node.args[0].value,
                                              AttrAccess(
                                                  node.args[0].attr, PtrAccess())
                    ),
                        frac=frac),
                    self.create_hasval_fact(node.args[0].value,
                                            self.get_type(node.args[0], ctx),
                                            ctx,
                                            py2vf_ctx,
                                            lambda x: AttrAccess(node.args[0].attr, x), frac=frac)
                ])
            elif isinstance(node.args[0], ast.Call):
                if (node.args[0].func.id == "list_pred"):
                    node = node.args[0]
                    return vf.FactConjunction([vfpy.PyObj_HasContent(
                        self.translate_generic_expr(
                            node.args[0], ctx, py2vf_ctx, PtrAccess()),
                        py2vf_ctx.getExpr(
                            node.args[0], CtntAccess(PtrAccess())),
                        frac=frac
                    ),
                        vfpy.ForallPredFact(
                        py2vf_ctx.getExpr(node.args[0], CtntAccess("")),
                        vf.NameUseExpr("pyobj_hasval"),
                        vfpy.ListForallCond_True(),
                        self.getWrapperStr(self.get_type(
                            node.args[0], ctx).type_args[0]),
                        frac=frac),
                        vf.BooleanFact(vf.BinOp[vf.Bool](
                            "map(fst, " +
                            str(py2vf_ctx.getExpr(
                                node.args[0], CtntAccess("")))+")",
                            py2vf_ctx.getExpr(
                                node.args[0], CtntAccess(PtrAccess())),
                            vf.Eq
                        )),
                        vf.BooleanFact(vf.BinOp[vf.Bool](
                            vf.Some("map(snd, " +
                                    str(py2vf_ctx.getExpr(node.args[0], CtntAccess("")))+")"),
                            vf.Some(py2vf_ctx.getExpr(
                                node.args[0], CtntAccess(ValAccess()))),
                            vf.Eq
                        ))
                    ])
                else:
                    raise NotImplementedError(
                        "Acc is not implemented for this content" + str(node.args[0]))
            else:
                raise NotImplementedError(
                    "Acc is not implemented for this content" + str(node.args[0]))
        elif (node.func.id == "list_pred"):
            rewritten = ast.Call(func=ast.Name(
                id="Acc", ctx=ast.Load()), args=[node], keywords=[])
            return self.translate_generic_fact(rewritten, ctx, py2vf_ctx)
        elif (node.func.id == "MaySet"):
            return vfpy.PyObj_MaySet(
                self.translate_generic_expr(
                    node.args[0], ctx, py2vf_ctx, PtrAccess()),
                node.args[1].value,
                vf.Wildcard[vfpy.PyObjPtr](),
                frac=Fraction(1)
            )
        elif (node.func.id == "MayCreate"):
            return vfpy.PyObj_MayCreate(
                self.translate_generic_expr(
                    node.args[0], ctx, py2vf_ctx, PtrAccess()),
                node.args[1].value,
                frac=Fraction(1))
        elif (node.func.id == "Implies"):
            return vf.FactConjunction([
                self.translate_generic_expr(node.args[0], ctx, py2vf_ctx),
                self.translate_generic_fact(node.args[1], ctx, py2vf_ctx)
            ])

        elif (node.func.id == "Forall"):
            # this handles the cases exactly equal to Forall(int, lambda i: P(i) )
            if (isinstance(node.args[1], ast.Lambda) and
               isinstance(node.args[1].body, ast.Call) and
               isinstance(node.args[1].body.func, ast.Name)):
                # this handles the case exactly equal to P(i) = Implies(i >= 0 and i < len(l), PRED(i))
                if (node.args[1].body.func.id == "Implies" and
                   isinstance(node.args[0], ast.Name) and
                   node.args[0].id == "int"):
                    #TODO: ensure that we properly translate the condition
                    #TODO: clean all this by declaring local variables
                    # this handles the case exactly equal to PRED(i) = Acc(l[i].attr)
                    if (node.args[1].body.args[1].func.id == "Acc"):
                        acc_call = node.args[1].body.args[1]
                        acc_content = acc_call.args[0]
                        acc_frac = Fraction(1)
                        if len(node.args[1].body.args[1].args) == 2:
                            acc_frac = Fraction(
                                acc_call.args[1].left.value, acc_call.args[1].right.value)
                        if (isinstance(acc_content, ast.Attribute)
                            and isinstance(acc_content.value, ast.Subscript)
                                and isinstance(acc_content.value.value, ast.Name)):
                            ptr2ptr_access = CtntAccess(AttrAccess(
                                acc_content.attr, "_attrptr2ptr"))
                            attr_ptrlist = CtntAccess(AttrAccess(
                                acc_content.attr, PtrAccess()))
                            attr_vallist = CtntAccess(AttrAccess(
                                acc_content.attr, ValAccess()))
                            ptr2val_access = CtntAccess(AttrAccess(
                                acc_content.attr, ""))
                            return vf.FactConjunction([
                                # first fact: hasattr
                                vfpy.ForallPredFact(py2vf_ctx.getExpr(acc_content.value.value, ptr2ptr_access),
                                                    vf.NameUseExpr(
                                                        "pyobj_hasattr"),
                                                    vfpy.ListForallCond_True(),
                                                    self.getWrapperStr(
                                    self.get_type(acc_content, ctx)),
                                    frac=acc_frac
                                ),
                                # set equivalences: fst is the ptr list from list_pred
                                vf.BooleanFact(vf.BinOp[vf.Bool](
                                    "map(fst, " + str(py2vf_ctx.getExpr(
                                        acc_content.value.value, ptr2ptr_access)) + ")",
                                    py2vf_ctx.getExpr(
                                        acc_content.value.value, CtntAccess(PtrAccess())),
                                    # AttrAccess(acc_content.attr, CtntAccess(""))),
                                    vf.Eq
                                )),
                                vfpy.ForallPredFact(
                                    py2vf_ctx.getExpr(
                                        acc_content.value.value, ptr2val_access),
                                    vf.NameUseExpr("pyobj_hasval"),
                                    vfpy.ListForallCond_True(),
                                    self.getWrapperStr(self.get_type(
                                        acc_content.value.value, ctx).type_args[0]),
                                    frac=acc_frac),
                                vf.BooleanFact(vf.BinOp[vf.Bool](
                                    vf.Some("map(snd, " +
                                            str(
                                                py2vf_ctx.getExpr(
                                                    acc_content.value.value, ptr2ptr_access)
                                            )
                                            + ")"),
                                    vf.Some(py2vf_ctx.getExpr(
                                        acc_content.value.value, attr_ptrlist)),
                                    vf.Eq
                                )),
                                vf.BooleanFact(vf.BinOp[vf.Bool](
                                    "map(fst, " +
                                    str(
                                        py2vf_ctx.getExpr(
                                            acc_content.value.value, ptr2val_access)
                                    )
                                    + ")",
                                    py2vf_ctx.getExpr(
                                        acc_content.value.value, attr_ptrlist),
                                    vf.Eq
                                )),
                                #
                                vf.BooleanFact(vf.BinOp[vf.Bool](
                                    vf.Some("map(snd, " +
                                            str(
                                                py2vf_ctx.getExpr(
                                                    acc_content.value.value, ptr2val_access)
                                            )
                                            + ")"),
                                    vf.Some(py2vf_ctx.getExpr(
                                        acc_content.value.value, attr_vallist)),
                                    vf.Eq
                                )),

                            ])
                    else:
                        raise NotImplementedError(
                            "Forall is not implemented for this content")
                elif (self.get_type(node.args[0], ctx).name == "list" and
                      isinstance(node.args[0], ast.Name)):
                    rewritten = self.indexify_forall(node, ctx, py2vf_ctx)                    
                    return self.translate(rewritten, ctx, py2vf_ctx)
                    # translate into an indexed forall
                else:
                    raise NotImplementedError(
                        "Forall is not implemented for this content")
            else:
                raise NotImplementedError(
                    "Forall is not implemented for this content")
        # TODO: remove this?
        elif (node.func.id == "Old"):
            return self.translate(node.args[0], ctx, py2vf_ctx.old)
        else:
            funcid = node.func.id
            # raise NotImplementedError("Call to function not implemented")
            # TODO: check if each of these variables is to be used as ref or as val
            def f(x, y): return self.translate_generic_expr(
                x, ctx, py2vf_ctx, y)

            return self.predicates[funcid](*list(chain.from_iterable([(f(y, PtrAccess()), f(y, ValAccess())) for y in node.args])))

    def translate_IfExp_fact(self, node: ast.IfExp, ctx: Context, py2vf_ctx: py2vf_context) -> vf.Fact:
        # the condition must be pure
        # but either branches could be pure or a fact (just one needs be a fact)
        return vf.TernaryFact(self.translate_generic_expr(node.test, ctx, py2vf_ctx, ValAccess()),
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
            ast.IfExp: self.translate_IfExp_expr,
            ast.BoolOp: self.translate_BoolOp_expr,
            ast.BinOp: self.translate_BinOp_expr,
            ast.Compare: self.translate_Compare_expr,
            ast.Constant: self.translate_Constant_expr,
            ast.Name: self.translate_Name_expr,
            ast.Attribute: self.translate_Attribute_expr,
            ast.Tuple: self.translate_Tuple_expr,
            ast.Subscript: self.translate_Subscript_expr,
            ast.Call: self.translate_Call_expr,
        }
        return switch_dict[type(node)](node, ctx,  py2vf_ctx, v)

    def translate_Call_expr(self, node: ast.Call, ctx: Context, py2vf_ctx: py2vf_context, v: ValueAccess) -> vf.Expr:
        if (node.func.id == "Old"):
            return self.translate_generic_expr(node.args[0], ctx, py2vf_ctx.old, v)
        elif (node.func.id == "Result"):
            return py2vf_ctx.getExpr(node, v)
        elif (node.func.id == "Implies"):
            return vf.TernaryOp(
                self.translate_generic_expr(node.args[0], ctx, py2vf_context(
                    py2vf_ctx, prefix=py2vf_ctx.getprefix()), ValAccess()),
                self.translate_generic_expr(node.args[1], ctx, py2vf_context(
                    py2vf_ctx, prefix=py2vf_ctx.getprefix()), v),
                vf.Bool(True))
        elif (node.func.id == "len"):
            return vf.FPCall("length", self.translate_generic_expr(node.args[0], ctx, py2vf_ctx, CtntAccess(v)))
        else:
            funcid = node.func.id
            if (self.functions.get(funcid) != None):
                def f(x, y): return self.translate_generic_expr(
                    x, ctx, py2vf_ctx, y)
                return self.functions[funcid](*list(chain.from_iterable([(f(y, PtrAccess()), f(y, ValAccess())) for y in node.args])))
            else:
                raise NotImplementedError(
                    "Call to function "+funcid+" not implemented: the function was not translated")

    def translate_Tuple_expr(self, node: ast.Tuple, ctx: Context, py2vf_ctx: py2vf_context, v: ValueAccess) -> vf.Expr:
        if (type(v) == TupleSubscriptAccess):
            # handle the case where the index is not a constant? a priori, not implemented yet in Nagini, so no
            return self.translate_generic_expr(node.elts[v.index], ctx, py2vf_ctx, v.value)
        else:
            raise NotImplementedError("Tuple expression not implemented")

    def translate_Subscript_expr(self, node: ast.Subscript, ctx: Context, py2vf_ctx: py2vf_context, v: ValueAccess) -> vf.Expr:
        if (self.get_type(node.value, ctx).name == "tuple"):
            return self.translate_generic_expr(node.value, ctx, py2vf_ctx, TupleSubscriptAccess(node.slice.value, v))
        else:
            idxExpr = self.translate_generic_expr(
                node.slice, ctx, py2vf_ctx, ValAccess())
            list_ctnt_ = self.translate_generic_expr(
                node.value, ctx, py2vf_ctx, CtntAccess(v))
            return vf.FPCall("nth", idxExpr, list_ctnt_)

    def translate_BoolOp_expr(self, node: ast.BoolOp, ctx: Context, py2vf_ctx: py2vf_context, v: ValueAccess) -> vf.Expr:
        dict = {
            ast.And: vf.BoolAnd,
            ast.Or: vf.BoolOr
        }
        operator = dict[type(node.op)]
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
            ast.Add: vf.Add,
            ast.Sub: vf.Sub,
            ast.Mult: vf.Mul,
            ast.Div: vf.Div,
            ast.Mod: vf.Mod,
            # TODO"Pow": vf.Pow,
            ast.LShift: vf.LShift,
            ast.RShift: vf.RShift,
            ast.BitOr: vf.BitOr,
            ast.BitXor: vf.BitXor,
            ast.BitAnd: vf.BitAnd,
            ast.FloorDiv: vf.Div
        }
        operator = dict[type(node.op)]
        return vf.BinOp[vf.Int](
            self.translate_generic_expr(
                node.left, ctx, py2vf_ctx, ValAccess()),
            self.translate_generic_expr(
                node.right, ctx, py2vf_ctx, ValAccess()),
            operator)

    def translate_Constant_expr(self, node: ast.Constant, ctx: Context, py2vf_ctx: py2vf_context,  v: ValueAccess) -> vf.Expr:
        dict = {
            "int": vf.Int,
            "float": vf.Float,
            "bool": vf.Bool
            # TODO: add string
            # TODO: use class names instead of strings
        }
        return dict[type(node.value).__name__](node.value)

    def translate_Name_expr(self, node: ast.Name, ctx: Context, py2vf_ctx: py2vf_context,  v: ValueAccess) -> vf.Expr:
        return py2vf_ctx.getExpr(node, v, True)

    def translate_Compare_expr(self, node: ast.Compare, ctx: Context, py2vf_ctx: py2vf_context,  v: ValueAccess) -> vf.Expr:
        operandtype = self.get_type(node.left, ctx).name
        # TODO: any other type fitting in there?
        ptracc = PtrAccess()
        valacc = ValAccess()
        dict = {
            ast.Eq: (vf.Eq, valacc),
            ast.NotEq: (vf.NotEq, valacc),
            ast.Lt: (vf.Lt, valacc),
            ast.LtE: (vf.LtE, valacc),
            ast.Gt: (vf.Gt, valacc),
            ast.GtE: (vf.GtE, valacc),
            ast.Is: (vf.Eq, ptracc),
        }
        operator, acctype = dict[type(node.ops[0])]
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
            compname = type(node.ops[0]).__name__
            opd_left_types = self.get_type(node.left, ctx).type_args
            opd_right_types = self.get_type(node.comparators[0], ctx).type_args
            if (compname == "Eq"):
                if (opd_left_types != opd_right_types):
                    return vf.Bool(False)
                else:
                    res = ast.BoolOp(ast.And(), [
                        ast.Compare(left=ast.Subscript(value=node.left, slice=ast.Constant(value=i), ctx=ast.Load()),
                                    ops=[ast.Eq()],
                                    comparators=[ast.Subscript(
                                        value=node.comparators[0], slice=ast.Constant(value=i), ctx=ast.Load())],
                                    ) for i in range(len(opd_left_types))
                    ])
                    return self.translate_generic_expr(res, ctx, py2vf_ctx, v)
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
            else:
                raise NotImplementedError(
                    "Tuple comparison "+compname+" not implemented")
        else:
            raise NotImplementedError(
                "Comparison for type "+operandtype+" not implemented")

    def create_hasval_fact(self, target: ast.expr, t: PythonType, ctx: Context, py2vf_ctx: py2vf_context, path=lambda x: x, names=[], frac=Fraction(1)) -> vf.Fact:
        if (t.name not in ["tuple"]):
            access = path(ValAccess())
            pyobj_method = {
                "int": vfpy.PyLong,
                # "bool": vfpy.PyBool,
                "list": lambda x: vfpy.PyClass_List(),
            }.get(t.name, lambda x: vfpy.PyClassInstance(self.classes[t.module.sil_name+t.name]))
            pyobjval = vf.ImmInductive(
                pyobj_method(py2vf_ctx.getExpr(target, access)))
            return vfpy.PyObj_HasVal(
                py2vf_ctx.getExpr(target, path(PtrAccess())),
                pyobjval,
                frac=frac)
        elif (t.name == "tuple"):
            tupleEls = []
            tupleElNames = [py2vf_ctx.getExpr(names[i], PtrAccess()) if i < len(names)
                            else py2vf_ctx.getExpr(target, path(TupleSubscriptAccess(i, PtrAccess())))for i in range(len(t.type_args))]
            for i in range(len(t.type_args)):
                tupleEls.append(vf.Pair[vfpy.PyObjPtr, vfpy.PyObj_t](
                    tupleElNames[i],
                    vf.ImmInductive(self.pytype__to__PyObj_t(t.type_args[i]))))
            pyobjval = vf.ImmInductive(
                vfpy.PyTuple(vf.List.from_list(tupleEls)))
            return vf.FactConjunction([vfpy.PyObj_HasVal(py2vf_ctx.getExpr(target, path(PtrAccess())), pyobjval)]+[
                self.create_hasval_fact(
                    names[i] if i < len(names) else target,
                    t.type_args[i],
                    ctx,
                    py2vf_ctx,
                    (lambda x: x) if i < len(names) else
                    (lambda x: path(TupleSubscriptAccess(i, x))),
                ) for i in range(len(t.type_args))
            ])
        else:
            print("NADA "+t.name)
            # raise NotImplementedError("Type not implemented")

    def pytype__to__PyObj_t(self, p: PythonType) -> vfpy.PyObj_t:
        if (p.name == 'tuple'):
            return vfpy.PyTuple_t(vf.List.from_list(list(map(lambda x: vf.ImmInductive(self.pytype__to__PyObj_t(x)), p.type_args))))
        return {
            'int': vfpy.PyLong(0).PyObj_t(),
            # TODO: this is just for testing, remove this and implement cleanly later
        }.get(p.name, vfpy.PyClass_t(self.classes.get(p.module.sil_name+p.name, "FAILED PYTYPE TRANSLATION")))

    def is_predless(self, node: ast.AST, ctx: Context) -> bool:
        # check there is an occurence of Acc or any predicate in the node (then unpure, otherwise pure)
        if (isinstance(node, ast.Call)):
            # predicates are stored in ctx.module.predicates
            if (node.func.id == "Implies"):
                return self.is_predless(node.args[1], ctx)
            if (node.func.id == "Forall"):
                return self.is_predless(node.args[1].body, ctx)
            return not (node.func.id in ctx.module.predicates or node.func.id in ["Acc", "list_pred", "MaySet", "MayCreate"])
        elif (isinstance(node, ast.UnaryOp)):
            return self.is_predless(node.operand, ctx)
        elif (isinstance(node, ast.IfExp)):
            return self.is_predless(node.body, ctx) and self.is_predless(node.orelse, ctx)
        elif (isinstance(node, ast.BoolOp)):
            return all([self.is_predless(x, ctx) for x in node.values])
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
