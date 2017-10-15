import ast
from copy import deepcopy
from typing import Dict, List, Tuple, Union
from nagini_translation.lib.context import Context
from nagini_translation.lib.program_nodes import (
    CallSlot,
    CallSlotProof,
    PythonMethod,
    PythonVar,
    TypeInfo
)
from nagini_translation.lib.typedefs import (
    Expr,
    Stmt,
    StmtsAndExpr
)
from nagini_translation.lib.util import UnsupportedException
from nagini_translation.translators.common import CommonTranslator
from nagini_translation.call_slot_analyzers import is_call_slot_proof


class CallSlotTranslator(CommonTranslator):

    def __init__(self, config: 'TranslatorConfig', jvm: 'JVM', source_file: str,
                 type_info: TypeInfo, viper_ast: 'ViperAST') -> None:
        super().__init__(config, jvm, source_file, type_info, viper_ast)
        self.arg_replacer = _ArgReplacer()

    def translate_call_slot_check(
        self, target: CallSlot, args: List[Expr],
        formal_args: List[Expr], arg_stmts: List[Stmt],
        position: 'silver.ast.Position', node: ast.AST,
        ctx: Context
    ) -> StmtsAndExpr:
        check = self.viper.FuncApp(
            target.sil_name,
            args,
            position,
            self.no_info(ctx),
            self.viper.Bool,
            formal_args
        )
        return arg_stmts, check

    def translate_call_slot_application(self, closureCall: ast.Call, ctx: Context) -> StmtsAndExpr:
        call, justification = closureCall.args

        assert isinstance(call, ast.Call)
        assert isinstance(justification, (ast.Call, ast.Name))
        if isinstance(justification, ast.Call):
            return self._application_call_slot(call, justification, ctx)
        else:
            return self._application_static_dispatch(call, justification, ctx)

    def _application_call_slot(self, call: ast.Call, justification: ast.Call, ctx: Context) -> StmtsAndExpr:
        assert isinstance(call.func, ast.Name)
        assert isinstance(justification.func, ast.Call)
        assert isinstance(justification.func.func, ast.Name)

        call_slot = ctx.module.call_slots[justification.func.func.id]

        stmts = self._application_call_slot_justification(justification, ctx)

        assert len(call.args) == len(justification.func.args)
        arg_map = {
            py_var.name: arg
            for py_var, arg in zip(call_slot.get_args(), call_slot.call.args)
        }

        for arg_call, arg_slot in zip(call.args, justification.func.args):
            stmts.extend(self._application_call_slot_arg_match(
                arg_call, arg_slot, arg_map, ctx))

        stmts.extend(self._application_call_slot_arg_match(
            call.func, call_slot.call.func, arg_map, ctx))

        call_stmts, call_expr = self._translate_normal_call(
            call_slot, call.args + justification.func.args, ctx
        )

        return stmts + call_stmts, call_expr

    def _application_call_slot_justification(self, justification: ast.Call, ctx: Context) -> List[Stmt]:

        assert isinstance(justification.func, ast.Call)  # uq vars
        stmts, expr = self.translate_expr(justification.func, ctx, self.viper.Bool)
        return stmts + [
            self.viper.Assert(expr, self.to_position(justification.func, ctx), self.no_info(ctx)) ]

    def _application_call_slot_arg_match(self, call_arg: ast.expr,
                                         slot_arg: ast.expr, arg_map: Dict[str, ast.expr],
                                         ctx: Context) -> List[Stmt]:
        slot_arg = deepcopy(slot_arg)
        slot_arg = self.arg_replacer.replace(slot_arg, arg_map)

        call_arg_stmts, viper_call_arg = self.translate_expr(call_arg, ctx)

        slot_arg_stmts, viper_slot_arg = self.translate_expr(slot_arg, ctx)

        return call_arg_stmts + slot_arg_stmts + [
            self.viper.Assert(
                self.viper.EqCmp(
                    viper_call_arg,
                    viper_slot_arg,
                    self.to_position(call_arg, ctx),
                    self.no_info(ctx)
                ),
                self.to_position(call_arg, ctx),
                self.no_info(ctx)
            )
        ]

    def _translate_normal_call(self, target: PythonMethod, args: List[ast.expr], ctx: Context) -> StmtsAndExpr:

        result_var = None
        if target.return_type is not None:
            result_var = ctx.current_function.create_variable(
                target.name + '_res', target.return_type, self.translator).ref()

        arg_stmts: List[Stmt] = []
        arg_exprs: List[Expr] = []

        for arg in args:
            stmts, expr = self.translate_expr(arg, ctx)
            arg_stmts.extend(stmts)
            arg_exprs.append(expr)

        call = self.viper.MethodCall(
            target.name + '_apply', arg_exprs, [result_var],
            self.to_position(target.node, ctx), self.no_info(ctx)
        )

        return arg_stmts + [call], result_var

    def _application_static_dispatch(self, call: ast.Call, justification: ast.Name, ctx: Context) -> StmtsAndExpr:
        # TODO: implement
        assert False

    def translate_call_slot_proof(self, proof_node: ast.FunctionDef, ctx: Context) -> List[Stmt]:
        assert is_call_slot_proof(proof_node)

        proof = ctx.current_function.call_slot_proofs[proof_node]
        vars_stmts, nv_map = self._proof_extract_vars(proof, ctx)

        body_stmts = self._proof_translate_body(proof, ctx)

        return stmts

    def _proof_extract_vars(self, proof: CallSlotProof, ctx: Context) -> Tuple[List[Stmt], Dict[str, PythonVar]]:

        vars = proof.get_args()
        values = proof.call_slot_instantiation.args

        stmts: List[Stmt] = []
        vars_map: Dict[str, PythonVar] = {}

        assert len(vars) == len(values)
        for var, value in zip(vars, values):
            var_stmts, proof_var = self._proof_extract_var(var, value, ctx)
            stmts.extend(var_stmts)
            vars_map[var.name] = proof_var

        return stmts, vars_map

    def _proof_extract_var(self, var: PythonVar, val: ast.expr, ctx: Context) -> Tuple[List[Stmt], PythonVar]:
        stmts, viper_val = self.translate_expr(val, ctx)

        proof_var = ctx.current_function.create_variable(
            '__proof_' + var.name, var.type, self.config.translator
        )

        stmts.append(self.viper.LocalVarAssign(
            proof_var.ref(proof_var.node, ctx),
            viper_val,
            self.to_position(proof_var.node, ctx),
            self.no_info(ctx)
        ))

        return stmts, proof_var

    def _proof_translate_body(self, proof: CallSlotProof, ctx: Context) -> List[Stmt]:
        pass

    def _proof_introduce_uq_ret_vars(self, proof: CallSlotProof, ctx: Context) -> Dict[str, PythonVar]:
        return {
        }


class _ArgReplacer(ast.NodeTransformer):

    def replace(self, node: ast.expr, arg_map: Dict[str, ast.expr]) -> ast.expr:
        self.arg_map = arg_map
        return self.visit(node)

    def visit_Name(self, name: ast.Name) -> ast.expr:
        return deepcopy(self.arg_map[name.id]) if name.id in self.arg_map else name
