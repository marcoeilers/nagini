
from functools import reduce
from fractions import Fraction
from nagini_translation.lib.context import Context
from nagini_translation.native.py2vf_ctx import py2vf_context, AccessType, PtrAccess, ValAccess, TupleSbscAccess, AttrAccess, CtntAccess
from nagini_translation.lib.program_nodes import PythonMethod, PythonType, PythonVar, PythonModule, PythonClass
import nagini_translation.native.vf.vf as vf
import nagini_translation.native.vf.pymodules as vfpy
from nagini_translation.lib.resolver import get_target as do_get_target
from nagini_translation.lib.resolver import get_type as do_get_type
from typing import Callable, Optional, Type
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

    def translate_forall_condition(self, node: ast.Expr, name: ast.Name, ctx: Context, py2vf_ctx: py2vf_context) -> vfpy.ListForallCond:
        if (isinstance(node, ast.Compare)):
            the_cmp = {ast.GtE: vfpy.ListForallCond_Gte,
                       ast.LtE: vfpy.ListForallCond_Lte,
                       ast.Gt: vfpy.ListForallCond_Gt,
                       ast.Lt: vfpy.ListForallCond_Lt,
                       }[type(node.ops[0])]
            # ensure that only two elements are compared
            if (len(node.comparators) != 1):
                raise NotImplementedError(
                    "Forall condition comparing more than 2 elements not implemented")
            if (isinstance(node.left, ast.Name) and node.left.id == name):
                return the_cmp(
                    self.translate_generic_expr(node.comparators[0], ctx, py2vf_ctx, ValAccess()))
            elif (isinstance(node.comparators[0], ast.Name) and node.comparators[0].id == name):
                return the_cmp(
                    self.translate_generic_expr(node.left, ctx, py2vf_ctx, ValAccess()))
            else:
                raise NotImplementedError("Forall condition comparing "+str(
                    node.left)+" and "+str(node.comparators[0])+" not implemented")
        if (isinstance(node, ast.BoolOp)):
            if (isinstance(node.op, ast.And)):
                return vfpy.ListForallCond_And(
                    self.translate_forall_condition(
                        node.values[0], name, ctx, py2vf_ctx),
                    self.translate_forall_condition(node.values[1], name, ctx, py2vf_ctx))
            elif (isinstance(node.op, ast.Or)):
                return vfpy.ListForallCond_Or(
                    self.translate_forall_condition(
                        node.values[0], name, ctx, py2vf_ctx),
                    self.translate_forall_condition(node.values[1], name, ctx, py2vf_ctx))
        if (isinstance(node, ast.UnaryOp)):
            if (isinstance(node.op, ast.Not)):
                return vfpy.ListForallCond_Neg(
                    self.translate_forall_condition(node.operand, name, ctx, py2vf_ctx))

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
                            vf.NameUseExpr(self.pytype__to__hasvalpredname(
                                self.get_type(node.args[0], ctx).type_args[0])),
                            vf.ImmInductive(vfpy.ListForallCond_True()),
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
            return vf.TernaryFact(
                self.translate_generic_expr(
                    node.args[0], ctx, py2vf_ctx, ValAccess()),
                self.translate(node.args[1], ctx, py2vf_context(
                    py2vf_ctx, prefix=py2vf_ctx.getprefix(), old=py2vf_ctx.old)),
                vf.BooleanFact(vf.ImmLiteral(vf.Bool(True))))

        elif (node.func.id == "Forall"):
            # this handles the cases exactly equal to Forall(int, lambda i: P(i) )
            thelambda = node.args[1]
            if (isinstance(thelambda, ast.Lambda) and
               isinstance(thelambda.body, ast.Call) and
               isinstance(thelambda.body.func, ast.Name)):
                # this handles the case exactly equal to P(i) = Implies(i >= 0 and i < len(l), PRED(i))
                if (thelambda.body.func.id == "Implies" and
                   isinstance(node.args[0], ast.Name) and
                   node.args[0].id == "int"):
                    implies = thelambda.body
                    forallpred_inductive_condition = self.translate_forall_condition(
                        implies.args[0], thelambda.args.args[0].arg, ctx, py2vf_ctx)
                    # TODO: ensure that we properly translate the condition
                    # TODO: clean all this by declaring local variables
                    # this handles the case exactly equal to PRED(i) = Acc(l[i].attr)
                    if (implies.args[1].func.id == "Acc"):
                        acc_call = implies.args[1]
                        acc_content = acc_call.args[0]
                        acc_frac = Fraction(1)
                        if len(thelambda.body.args[1].args) == 2:
                            acc_frac = Fraction(
                                acc_call.args[1].left.value, acc_call.args[1].right.value)
                        if (isinstance(acc_content, ast.Attribute)
                            and isinstance(acc_content.value, ast.Subscript)
                            and isinstance(acc_content.value.value, ast.Name)
                            and isinstance(acc_content.value.slice, ast.Name)
                                and acc_content.value.slice.id == thelambda.args.args[0].arg):
                            ptr2ptr_access = CtntAccess(
                                AttrAccess(acc_content.attr, "_attrptr2ptr"))
                            attr_ptrlist = CtntAccess(
                                AttrAccess(acc_content.attr, PtrAccess()))
                            attr_vallist = CtntAccess(
                                AttrAccess(acc_content.attr, ValAccess()))
                            ptr2val_access = CtntAccess(
                                AttrAccess(acc_content.attr, ""))
                            return vf.FactConjunction([
                                # first fact: hasattr
                                vfpy.ForallPredFact(py2vf_ctx.getExpr(acc_content.value.value, ptr2ptr_access),
                                                    vf.NameUseExpr(
                                                        "attr_binary_pred(hasAttr(\""+str(acc_content.attr)+"\"))"),
                                                    # vf.NameUseExpr(self.pytype__to__hasvalpredname(self.get_type(acc_content.value.value, ctx).type_args[0])),
                                                    # vf.ImmInductive(vfpy.ListForallCond_True()),
                                                    forallpred_inductive_condition,
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
                                    # self.get_type(acc_content.value.value, ctx).type_args[0]
                                    vf.NameUseExpr(self.pytype__to__hasvalpredname(self.get_type(
                                        acc_content.value.value, ctx).type_args[0])),
                                    vf.ImmInductive(
                                        vfpy.ListForallCond_True()),
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
                                    "map(fst, " + str(py2vf_ctx.getExpr(
                                        acc_content.value.value, ptr2val_access)) + ")",
                                    py2vf_ctx.getExpr(
                                        acc_content.value.value, attr_ptrlist),
                                    vf.Eq
                                )),
                                #
                                # "MISSING: something stating which attr is",
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
            old_interm = py2vf_context(
                py2vf_ctx.old, old=py2vf_ctx.old, prefix=py2vf_ctx.getprefix())
            return self.translate(node.args[0], ctx, old_interm)
        else:
            funcid = node.func.id
            # raise NotImplementedError("Call to function not implemented")
            # TODO: check if each of these variables is to be used as ref or as val
            def f(x, y): return self.translate_generic_expr(
                x, ctx, py2vf_ctx, y)
            if (funcid in self.predicates):

                translated_arg_list = []
                for enum, arg in enumerate(node.args):
                    for accesstype in self.predicates[funcid][1][enum]:
                        translated_arg_list.append(f(arg, accesstype))
                return self.predicates[funcid][0](*translated_arg_list)
            else:
                raise NotImplementedError(
                    "Call to predicate "+funcid+" not translated: the predicate was not translated or does not exist")

    def translate_IfExp_fact(self, node: ast.IfExp, ctx: Context, py2vf_ctx: py2vf_context) -> vf.Fact:
        # the condition must be pure
        # but either branches could be pure or a fact (just one needs be a fact)
        return vf.TernaryFact(self.translate_generic_expr(node.test, ctx, py2vf_ctx, ValAccess()),
                              self.translate(node.body, ctx, py2vf_context(
                                  py2vf_ctx, prefix=py2vf_ctx.getprefix(), old=py2vf_ctx.old)),
                              self.translate(node.orelse, ctx, py2vf_context(py2vf_ctx, prefix=py2vf_ctx.getprefix(), old=py2vf_ctx.old)))

    def translate_BoolOp_fact(self, node: ast.BoolOp, ctx: Context, py2vf_ctx: py2vf_context) -> vf.Fact:
        assert (type(node.op).__name__ == "And")
        return vf.FactConjunction(map(lambda x: self.translate(x, ctx, py2vf_ctx), node.values))

    def translate_generic_expr(self, node: ast.AST, ctx: Context, py2vf_ctx: py2vf_context, v: AccessType) -> vf.Expr:
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

    def translate_Call_expr(self, node: ast.Call, ctx: Context, py2vf_ctx: py2vf_context, v: AccessType) -> vf.Expr:
        if (node.func.id == "Old"):
            old_interm = py2vf_context(
                py2vf_ctx.old, old=py2vf_ctx.old, prefix=py2vf_ctx.getprefix())
            return self.translate_generic_expr(node.args[0], ctx, old_interm, v)
        elif (node.func.id == "Result"):
            return py2vf_ctx.getExpr(node, v)
        elif (node.func.id == "Forall"):
            thelambda = node.args[1]
            if (isinstance(thelambda, ast.Lambda) and
               isinstance(thelambda.body, ast.Call) and
               isinstance(thelambda.body.func, ast.Name)):
                forallcontext = py2vf_context(py2vf_ctx)
                lambda_arg_astName = ast.Name(thelambda.args.args[0].arg)
                forallcontext.getExpr(lambda_arg_astName, ValAccess())
                lambdavar = PythonVar(thelambda.args.args[0].arg, self.get_target(thelambda.args.args[0], ctx), PythonClass(node.args[0].id, None, None))
                ctx.set_alias(thelambda.args.args[0].arg, lambdavar)
                return "forall_(int "+str(forallcontext.getExpr(lambda_arg_astName, ValAccess()))+"; "+str(self.translate_generic_expr(thelambda.body, ctx, forallcontext, ValAccess()))+")"
        elif (node.func.id == "Implies"):
            return vf.TernaryOp(
                self.translate_generic_expr(
                    node.args[0], ctx, py2vf_ctx, ValAccess()),
                self.translate_generic_expr(node.args[1], ctx, py2vf_context(
                    py2vf_ctx, prefix=py2vf_ctx.getprefix(), old=py2vf_ctx.old), v),
                vf.Bool(True))
        elif (node.func.id == "len"):
            return vf.FPCall("length", self.translate_generic_expr(node.args[0], ctx, py2vf_ctx, CtntAccess(v)))
        elif (node.func.id == "IsInstance"):
            return vf.FPCall("isinstance",
                             self.translate_generic_expr(
                                 node.args[0], ctx, py2vf_ctx, ValAccess()),
                             self.translate_generic_expr(node.args[1], ctx, py2vf_ctx, ValAccess()))
        else:
            if (isinstance(v, ValAccess)):
                funcid = node.func.id
                if (self.functions[funcid] != None):
                    translated_arg_list = []
                    for enum, arg in enumerate(node.args):
                        for accesstype in self.functions[funcid][1][enum]:
                            translated_arg_list.append(
                                self.translate_generic_expr(arg, ctx, py2vf_ctx, accesstype))
                    return self.functions[funcid][0](*translated_arg_list)
                else:
                    raise NotImplementedError(
                        "Call to function "+funcid+" not implemented: the function was not translated")
            else:
                raise NotImplementedError(
                    "Pure functions cannot be translated in this context: "+str(node.func.id)+" in "+repr(v)+".\n Only value-semantics is supported")

    def translate_Tuple_expr(self, node: ast.Tuple, ctx: Context, py2vf_ctx: py2vf_context, v: AccessType) -> vf.Expr:
        if (type(v) == TupleSbscAccess):
            # handle the case where the index is not a constant? a priori, not implemented yet in Nagini, so no
            return self.translate_generic_expr(node.elts[v.index], ctx, py2vf_ctx, v.value)
        else:
            raise NotImplementedError("Tuple expression not implemented")

    def translate_Subscript_expr(self, node: ast.Subscript, ctx: Context, py2vf_ctx: py2vf_context, v: AccessType) -> vf.Expr:
        if (self.get_type(node.value, ctx).name == "tuple"):
            return self.translate_generic_expr(node.value, ctx, py2vf_ctx, TupleSbscAccess(node.slice.value, v))
        else:
            idxExpr = self.translate_generic_expr(
                node.slice, ctx, py2vf_ctx, ValAccess())
            list_ctnt_ = self.translate_generic_expr(
                node.value, ctx, py2vf_ctx, CtntAccess(v))
            return vf.FPCall("nth", idxExpr, list_ctnt_)

    def translate_BoolOp_expr(self, node: ast.BoolOp, ctx: Context, py2vf_ctx: py2vf_context, v: AccessType) -> vf.Expr:
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

    def translate_Attribute_expr(self, node: ast.Attribute, ctx: Context, py2vf_ctx: py2vf_context, v: AccessType) -> vf.Expr:
        return self.translate_generic_expr(node.value, ctx, py2vf_ctx, AttrAccess(node.attr, v))

    def translate_IfExp_expr(self, node: ast.IfExp, ctx: Context, py2vf_ctx: py2vf_context, v: AccessType) -> vf.Expr:
        # TODO: create a new py2vf_context for the branches
        return vf.TernaryOp(self.translate_generic_expr(node.test, ctx, py2vf_ctx, ValAccess()),
                            self.translate_generic_expr(node.body, ctx, py2vf_context(
                                py2vf_ctx, prefix=py2vf_ctx.getprefix(), old=py2vf_ctx.old), v),
                            self.translate_generic_expr(node.orelse, ctx, py2vf_context(py2vf_ctx, prefix=py2vf_ctx.getprefix(), old=py2vf_ctx.old), v))

    def translate_BinOp_expr(self, node: ast.BinOp, ctx: Context, py2vf_ctx: py2vf_context,  v: AccessType) -> vf.Expr:
        if(isinstance(v, ValAccess)==False):
            raise NotImplementedError(
                "BinOp expression cannot be translated in this context: "+str(node)+" in "+repr(v)+".\n Only value-semantics is supported")
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

    def translate_Constant_expr(self, node: ast.Constant, ctx: Context, py2vf_ctx: py2vf_context,  v: AccessType) -> vf.Expr:
        if (isinstance(v, ValAccess)):
            dict = {
                "int": vf.Int,
                "float": vf.Float,
                "bool": vf.Bool,
                "string": vf.String
                
                # TODO: use class names instead of strings
            }
            return vf.ImmLiteral(dict[type(node.value).__name__](node.value))
        else:
            raise NotImplementedError("Constant expression cannot be translated in this context: "+str(
                node.value)+" in "+repr(v)+".\n Only value-semantics is supported")

    def translate_Name_expr(self, node: ast.Name, ctx: Context, py2vf_ctx: py2vf_context,  v: AccessType) -> vf.Expr:
        return py2vf_ctx.getExpr(node, v, True)

    def translate_Compare_expr(self, node: ast.Compare, ctx: Context, py2vf_ctx: py2vf_context,  v: AccessType) -> vf.Expr:
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
            ast.IsNot: (vf.NotEq, ptracc),
        }
        operator, acctype = dict[type(node.ops[0])]
        # TODO. review and fix this line
        if (operator == vf.Eq and self.get_type(node.left, ctx) != self.get_type(node.comparators[0], ctx)):
            return vf.ImmLiteral(vf.Bool(False))
        operandtype = self.get_type(node.left, ctx).name
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
        # maybe one day simply this using gethasvalpred?
        if (t == type(None)):
            return vfpy.PyObj_HasVal(
                py2vf_ctx.getExpr(target, path(PtrAccess())),
                vf.ImmInductive(vfpy.PyNone()),
                frac=frac)
        if (t.name not in ["tuple"]):
            access = path(ValAccess())
            pyobj_method = {
                "int": vfpy.PyLong,
                "float": vfpy.PyFloat,
                "bool": vfpy.PyBool,
                "string": vfpy.PyUnicode,
                "list": lambda x: vfpy.PyList(self.pytype__to__PyObj_t(t.type_args[0])),
            }.get(t.name, lambda x: vfpy.PyClassInstance(self.pytype__to__PyClass(t)))
            pyobjval = vf.ImmInductive(
                pyobj_method(py2vf_ctx.getExpr(target, access)))
            return vfpy.PyObj_HasVal(
                py2vf_ctx.getExpr(target, path(PtrAccess())),
                pyobjval,
                frac=frac)
        elif (t.name == "tuple"):
            tupleEls = []
            tupleElNames = [py2vf_ctx.getExpr(names[i], PtrAccess()) if i < len(names)
                            else py2vf_ctx.getExpr(target, path(TupleSbscAccess(i, PtrAccess())))for i in range(len(t.type_args))]
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
                    (lambda x: path(TupleSbscAccess(i, x))),
                ) for i in range(len(t.type_args))
            ])
        else:
            print("NADA "+t.name)
            # raise NotImplementedError("Type not implemented")

    def pytype__to__PyClass(self, p: PythonType) -> vfpy.PyClass:
        if self.classes.get(p.module.sil_name+p.name) == None:
            raise NotImplementedError("Type "+p.name+" not implemented")
        else:
            return self.classes[p.module.sil_name+p.name](map(self.pytype__to__PyObj_t, p.type_args if hasattr(p, 'type_args') else []))

    def pytype__to__PyObj_v(self, p: PythonType) -> Callable[[PythonType], vfpy.PyObj_v]:
        if (p == type(None)):
            return lambda x: vfpy.PyNone()
        else:
            if (p.name == 'tuple'):
                return vfpy.PyTuple
            if (p.name == 'int'):
                return vfpy.PyLong
            elif (p.name == 'float'):
                return vfpy.PyFloat
            elif (p.name == 'bool'):
                return vfpy.PyBool
            elif (p.name == 'string'):
                return vfpy.PyUnicode
            elif (p.name == "list"):
                return lambda x: vfpy.PyList(self.pytype__to__PyObj_t(p.type_args[0])(x))
            else:
                return lambda x: vfpy.PyClassInstance(self.pytype__to__PyClass(p))

    def pytype__to__PyObj_t(self, p: PythonType) -> vfpy.PyObj_t:
        if (p.name == 'tuple'):
            return vfpy.PyTuple_t(vf.List.from_list(list(map(lambda x: vf.ImmInductive(self.pytype__to__PyObj_t(x)), p.type_args))))
        if (p.name == 'int'):
            return "PyLong_t"
        elif (p.name == 'float'):
            return "PyFloat_t"
        elif (p.name == 'bool'):
            return "PyBool_t"
        elif (p.name == 'string'):
            return "PyUnicode_t"
        elif (p.name == "list"):
            return "PyList_t("+",".join([str(self.pytype__to__PyObj_t(x)) for x in p.type_args])+")"
        else:
            return vfpy.PyClass_t(self.pytype__to__PyClass(p))

    def pytype__to__hasvalpredname(self, t: type) -> str:
        if (t.name == "int"):
            return "pyobj_hasPyLongval"
        elif (t.name == "bool"):
            return "pyobj_hasPyBoolval"
        elif (t.name == "float"):
            return "pyobj_hasPyFloatval"
        elif (t.name == "string"):
            return "pyobj_hasPyUnicodeval"
        elif (t.name == "tuple"):
            return "pyobj_hasPyTupleval()"
        elif (t.name == "none"):
            return "pyobj_hasPyNoneval"
        # TODO: support pytype here
        elif (t.name == "list"):
            return "pyobj_hasPyListval("+str(self.pytype__to__PyObj_t(t.type_args[0]))+")"
        else:
            return "pyobj_hasPyClassInstanceval("+str(self.pytype__to__PyClass(t))+")"

    def is_predless(self, node: ast.AST, ctx: Context) -> bool:
        # check there is an occurence of Acc or any predicate in the node (then unpure, otherwise pure)
        if (isinstance(node, ast.Call)):
            # predicates are stored in ctx.module.predicates
            if (node.func.id == "Implies"):
                return self.is_predless(node.args[1], ctx)
            if (node.func.id in ["Forall", "Forall2", "Forall3", "Forall4", "Forall5"]):
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
