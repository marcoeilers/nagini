import ast
from copy import deepcopy
from functools import reduce
from itertools import chain
from typing import Dict, List, Tuple, Union
from nagini_translation.lib.constants import ERROR_NAME, PRIMITIVES
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
    StmtsAndExpr,
    Function,
    Method,
    Position
)
from nagini_translation.lib.util import InvalidProgramException
from nagini_translation.translators.common import CommonTranslator
from nagini_translation.call_slot_analyzers import (
    is_call_slot_proof,
    is_closure_call,
    is_precondition,
    is_postcondition,
    is_fold,
    is_unfold,
    is_assume
)


class CallSlotTranslator(CommonTranslator):

    def __init__(self, config: 'TranslatorConfig', jvm: 'JVM', source_file: str,
                 type_info: TypeInfo, viper_ast: 'ViperAST') -> None:
        super().__init__(config, jvm, source_file, type_info, viper_ast)
        self._var_replacer = _VarReplacer()

    def translate_call_slot(self, call_slot: CallSlot, ctx: Context) -> Tuple[Function, Union[Method, Function]]:

        old_function = ctx.current_function
        ctx.current_function = call_slot

        position = self.to_position(call_slot.node, ctx)
        info = self.no_info(ctx)

        call_slot_holds = self.viper.Function(
            call_slot.sil_name,
            [arg.decl for arg in call_slot.get_args()],
            self.viper.Bool,
            [],
            [],
            None,
            position,
            info
        )

        args = [arg.decl for arg in chain(call_slot.get_args(), call_slot.uq_variables.values())]

        if call_slot.pure:

            pres = []
            for arg in chain(call_slot.get_args(), call_slot.uq_variables.values()):
                if arg.type.name in PRIMITIVES:
                    continue
                pres.append(self.type_check(arg.ref(), arg.type, position, ctx))
            for pre, _ in call_slot.precondition:
                pres.append(self._translate_pure_expr(
                    pre, ctx, target_type=self.viper.Bool, impure=True))

            if call_slot.pure and call_slot.type is not None:
                old_posts = call_slot.postcondition
                call_slot.postcondition = [
                    (
                        self._var_replacer.replace(deepcopy(post), {
                            call_slot.return_variables[0].id:
                                ast.Call(ast.Name('Result', ast.Load), [], [])
                        }),
                        aliases
                    )
                    for post, aliases in old_posts
                ]
            posts = []

            if call_slot.type is not None and call_slot.type.name not in PRIMITIVES:
                viper_type = self.translate_type(call_slot.type, ctx)
                posts.append(self.type_check(
                    self.viper.Result(viper_type, position, info),
                    call_slot.type, position, ctx
                ))

            for post, _ in call_slot.postcondition:
                posts.append(self._translate_pure_expr(
                    post, ctx, target_type=self.viper.Bool, impure=True))

            if call_slot.pure and call_slot.type is not None:
                call_slot.postcondition = old_posts

            _type = self.translate_type(call_slot.type, ctx)
            call_slot_apply = self.viper.Function(
                call_slot.sil_application_name, args, _type, pres, posts,
                None, position, info
            )

        else:
            pres, posts = self.extract_contract(call_slot, ERROR_NAME, False, ctx)
            call_slot_apply = self.create_method_node(
                ctx,
                call_slot.sil_application_name,
                args,
                [res.decl for res in call_slot.get_results()],
                pres,
                posts,
                [],
                [self.viper.Inhale(self.viper.FalseLit(position, info), position, info)],
                position,
                info,
                method=call_slot
            )

        ctx.current_function = old_function

        return call_slot_holds, call_slot_apply

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

        stmts = [self._application_call_slot_justification(call_slot, justification, ctx)]

        assert len(call_slot.get_args()) == len(justification.func.args)
        arg_map = {
            py_var.name: arg
            for py_var, arg in zip(
                chain(call_slot.get_args(), call_slot.uq_variables.values()),
                chain(justification.func.args, justification.args)
            )
        }

        assert len(call.args) == len(call_slot.call.args)
        for arg_call, arg_slot in zip(call.args, call_slot.call.args):
            stmts.append(self._application_call_slot_arg_match(
                arg_call, arg_slot, arg_map, ctx))

        stmts.append(self._application_call_slot_arg_match(
            call.func, call_slot.call.func, arg_map, ctx))

        formal_args = []
        if call_slot.pure:
            for arg in call_slot.get_args():
                formal_args.append(arg.decl)
            for arg in call_slot.uq_variables.values():
                formal_args.append(arg.decl)

        call_stmts, call_expr = self._translate_normal_call(
            call_slot.sil_application_name, call_slot, justification.func.args + justification.args,
            self.to_position(call, ctx), ctx, pure_call=call_slot.pure, formal_args=formal_args
        )

        return stmts + call_stmts, call_expr

    def _application_call_slot_justification(
        self,
        call_slot: CallSlot,
        justification: ast.Call,
        ctx: Context
    ) -> Stmt:

        assert isinstance(justification.func, ast.Call)  # uq vars
        justification = deepcopy(justification)

        justification.func.id = call_slot.sil_name
        expr = self._translate_pure_expr(justification.func, ctx, target_type=self.viper.Bool)
        return self.viper.Assert(expr, self.to_position(justification.func, ctx), self.no_info(ctx))

    def _application_call_slot_arg_match(
        self,
        call_arg: ast.expr,
        slot_arg: ast.expr,
        arg_map: Dict[str, ast.expr],
        ctx: Context
    ) -> Stmt:

        slot_arg = deepcopy(slot_arg)
        slot_arg = self._var_replacer.replace(slot_arg, arg_map)

        viper_call_arg = self._translate_pure_expr(call_arg, ctx)

        viper_slot_arg = self._translate_pure_expr(slot_arg, ctx)

        return self.viper.Assert(
            self.viper.EqCmp(
                viper_call_arg,
                viper_slot_arg,
                self.to_position(call_arg, ctx),
                self.no_info(ctx)
            ),
            self.to_position(call_arg, ctx),
            self.no_info(ctx)
        )

    def _translate_normal_call(
        self,
        name: str,
        target: PythonMethod,
        args: List[ast.expr],
        position: Position,
        ctx: Context,
        pure_call: bool = False,
        formal_args: List[Expr] = []
    ) -> StmtsAndExpr:

        result_var = None
        if target.type is not None and not pure_call:
            result_var = ctx.current_function.create_variable(
                target.name + '_res', target.type, self.translator).ref()

        stmts: List[Stmt] = []
        arg_exprs: List[Expr] = []

        for arg in args:
            expr = self._translate_pure_expr(arg, ctx)
            arg_exprs.append(expr)

        if pure_call:
            _type = self.translate_type(target.type, ctx)
            expr = self.viper.FuncApp(
                name, arg_exprs, position, self.no_info(ctx), _type, formal_args
            )
        else:
            stmts = self.create_method_call_node(
                ctx, name, arg_exprs, [result_var] if result_var else [],
                position, self.no_info(ctx), target_method=target
            )
            expr = result_var

        return stmts, expr

    def _application_static_dispatch(self, call: ast.Call, justification: ast.Name, ctx: Context) -> StmtsAndExpr:

        stmts: List[Stmt] = []
        position = self.to_position(call, ctx)
        info = self.no_info(ctx)
        target = self.get_target(justification, ctx)
        assert isinstance(target, PythonMethod)

        closure_expr = self._translate_pure_expr(call.func, ctx)

        justification_expr = self._translate_pure_expr(justification, ctx)

        stmts.append(self.viper.Assert(
            self.viper.EqCmp(
                closure_expr,
                justification_expr,
                position,
                info
            ),
            position,
            info
        ))

        method = ctx.module.get_func_or_method(justification.id)

        formal_args = []
        if target.pure:
            for arg in target.get_args():
                formal_args.append(arg.decl)

        call_stmts, call_expr = self._translate_normal_call(
            method.sil_name, method, call.args, self.to_position(call, ctx),
            ctx, pure_call=target.pure, formal_args=formal_args
        )
        stmts.extend(call_stmts)

        return stmts, call_expr

    def translate_call_slot_proof(self, proof_node: ast.FunctionDef, ctx: Context) -> List[Stmt]:
        assert is_call_slot_proof(proof_node)

        proof = ctx.current_function.call_slot_proofs[proof_node]
        old_proof = ctx.current_call_slot_proof
        ctx.current_call_slot_proof = proof

        call_slot = self._get_call_slot(proof, ctx)
        cl_map = self._get_cl_map(proof, call_slot)

        with ctx.aliases_context():
            vars_stmts = self._proof_extract_vars(proof, ctx)

            body_stmts = self._proof_translate_body(proof, call_slot, cl_map, ctx)

        while_loop = self._proof_create_non_deterministic_while_loop(
            proof, body_stmts, ctx
        )

        instantiation = deepcopy(proof.call_slot_instantiation)
        instantiation.func.id = call_slot.sil_name

        instantiation_expr = self._translate_pure_expr(
            instantiation, ctx, target_type=self.viper.Bool)

        instantiation_stmt = self.viper.Inhale(
            instantiation_expr, self.to_position(instantiation, ctx), self.no_info(ctx)
        )

        ctx.current_call_slot_proof = old_proof

        return vars_stmts + [while_loop] + [instantiation_stmt]

    def _proof_extract_vars(self, proof: CallSlotProof, ctx: Context) -> List[Stmt]:

        vars = proof.get_args()
        values = proof.call_slot_instantiation.args

        stmts: List[Stmt] = []

        assert len(vars) == len(values)
        for var, value in zip(vars, values):
            stmts.extend(self._proof_extract_var(var, value, ctx))

        return stmts

    def _get_call_slot(self, proof: CallSlotProof, ctx: Context) -> CallSlot:
        call_slot_name = proof.call_slot_instantiation.func.id
        if call_slot_name not in ctx.module.call_slots:
            raise InvalidProgramException(
                proof.node,
                'call_slots.proof_annotation.invalid_call_slot'
            )

        return ctx.module.call_slots[call_slot_name]

    def _get_cl_map(self, proof: CallSlotProof, call_slot: CallSlot) -> Dict[str, ast.expr]:

        proof_nv = proof.args.values()
        cl_nv = call_slot.args.values()
        if len(proof_nv) != len(cl_nv):
            raise InvalidProgramException(
                proof.node,
                'call_slots.proof_annotation.invalid_call_slot'
            )

        proof_uqv = proof.uq_variables.values()
        cl_uqv = call_slot.uq_variables.values()
        if len(proof_uqv) != len(cl_uqv):
            raise InvalidProgramException(
                proof.node,
                'call_slots.proof_annotation.invalid_call_slot'
            )

        proof_rv = [proof.locals[rv.id] for rv in proof.return_variables]
        cl_rv = [call_slot.locals[rv.id] for rv in call_slot.return_variables]
        if len(proof_rv) != len(cl_rv):
            raise InvalidProgramException(
                proof.node,
                'call_slots.proof_annotation.invalid_call_slot'
            )

        return {
            cl_var.name: ast.Name(
                proof_var.name,
                ast.Load,
                lineno=proof_var.node.lineno,
                col_offset=proof_var.node.col_offset,
            )
            for cl_var, proof_var in zip(
                chain(cl_nv, cl_uqv, cl_rv),
                chain(proof_nv, proof_uqv, proof_rv)
            )
        }

    def _proof_extract_var(self, var: PythonVar, val: ast.expr, ctx: Context) -> Stmt:
        viper_val = self._translate_pure_expr(val, ctx)

        proof_var = ctx.current_function.create_variable(
            '__proof_' + var.name, var.type, self.config.translator
        )

        stmts: List[Stmt] = []
        position = self.to_position(val, ctx)
        info = self.no_info(ctx)
        stmts.append(self.set_var_defined(
            proof_var, position, info))

        if proof_var.type.name not in PRIMITIVES:
            stmts.append(self.viper.Inhale(
                self.var_type_check(
                    proof_var.name, proof_var.type, position, ctx
                ),
                position,
                info
            ))

        ctx.set_alias(var.name, proof_var, var)

        stmts.append(self.viper.LocalVarAssign(
            proof_var.ref(proof_var.node, ctx),
            viper_val,
            self.to_position(proof_var.node, ctx),
            self.no_info(ctx)
        ))

        return stmts

    def _proof_create_non_deterministic_while_loop(
        self,
        proof: CallSlotProof,
        body: List[Stmt],
        ctx: Context
    ) -> Stmt:

        non_deterministic_bool = ctx.current_function.create_variable(
            '__proof_non_deterministic_choice', ctx.module.global_module.classes['bool'].try_unbox(), self.translator
        )

        position = self.to_position(proof.node, ctx)
        info = self.no_info(ctx)

        return self.viper.While(
            non_deterministic_bool.ref(), [], [],
            self.translate_block(body, position, info),
            position, info
        )

    def _proof_translate_body(
        self,
        proof: CallSlotProof,
        call_slot: CallSlot,
        cl_map: Dict[str, ast.expr],
        ctx: Context
    ) -> List[Stmt]:

        stmts: List[Stmt] = []
        position = self.to_position(proof.node, ctx)
        info = self.no_info(ctx)

        stmts.extend(self._proof_introduce_uq_ret_vars(proof, ctx))

        stmts.append(self.viper.Inhale(
            self._proof_translate_contract(proof, call_slot.precondition, cl_map, ctx),
            position,
            info
        ))

        stmts.append(self.viper.Label(proof.old_label, position, info))

        call_counter = ctx.current_function.create_variable(
            '__proof_call_counter', ctx.module.global_module.classes['int'].try_unbox(), self.translator
        )

        stmts.append(self.viper.LocalVarAssign(
            call_counter.ref(),
            self.viper.IntLit(0, position, info),
            position,
            info
        ))

        stmts.extend(self._proof_translate_body_only(
            proof.body,
            proof,
            call_slot,
            call_counter,
            cl_map,
            ctx
        ))

        stmts.append(self.viper.Exhale(
            self._proof_translate_contract(proof, call_slot.postcondition, cl_map, ctx),
            position,
            info
        ))

        stmts.append(self.viper.Assert(
            self.viper.EqCmp(
                call_counter.ref(),
                self.viper.IntLit(1, position, info),
                position,
                info
            ),
            position,
            info
        ))

        return stmts

    def _proof_introduce_uq_ret_vars(self, proof: CallSlotProof, ctx: Context) -> List[Stmt]:
        stmts: List[Stmt] = []

        for var in proof.uq_variables.values():
            proof_var = ctx.current_function.create_variable(
                '__proof_' + var.name, var.type, self.translator
            )

            position = self.to_position(proof_var.node, ctx)
            info = self.no_info(ctx)

            stmts.append(self.set_var_defined(proof_var, position, info))

            if proof_var.type.name not in PRIMITIVES:
                stmts.append(self.viper.Inhale(
                    self.var_type_check(
                        proof_var.name, proof_var.type, position, ctx
                    ),
                    position,
                    info
                ))

            ctx.set_alias(var.name, proof_var, var)

        if proof.return_variables:
            ret_var = proof.locals[proof.return_variables[0].id]
            proof_var = ctx.current_function.create_variable(
                '__proof_' + ret_var.name, ret_var.type, self.translator
            )
            ctx.set_alias(ret_var.name, proof_var, ret_var)

        return stmts

    def _proof_translate_contract(
        self,
        proof: CallSlotProof,
        contract: List[Tuple[ast.expr, Dict]],
        cl_map: Dict[str, ast.expr],
        ctx: Context
    ) -> Expr:

        position = self.to_position(proof.node, ctx)
        info = self.no_info(ctx)

        contract = [
            self._translate_pure_expr(self._var_replacer.replace(deepcopy(pre[0]), cl_map),
                ctx, impure=True, target_type=self.viper.Bool)
            for pre in contract
        ]

        return reduce(
            lambda left, right: self.viper.And(left, right, position, info),
            contract, self.viper.TrueLit(position, info)
        )

    def _proof_translate_body_only(
        self,
        body: List[ast.stmt],
        proof: CallSlotProof,
        call_slot: CallSlot,
        call_counter: PythonVar,
        cl_map: Dict[str, ast.expr],
        ctx: Context
    ) -> List[Stmt]:

        viper_stmts: List[Stmt] = []

        for stmt in body:

            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                if is_precondition(stmt.value) or is_postcondition(stmt.value):
                    continue  # ignore
                if is_fold(stmt.value) or is_unfold(stmt.value) or is_assume(stmt.value):
                    viper_stmts.extend(self.translate_stmt(stmt, ctx))
                    continue

                assert is_closure_call(stmt.value)

                for arg_call, arg_slot in zip(stmt.value.args[0].args, call_slot.call.args):
                    viper_stmts.append(self._application_call_slot_arg_match(
                        arg_call, arg_slot, cl_map, ctx
                    ))
                viper_stmts.append(self._application_call_slot_arg_match(
                    stmt.value.args[0].func, call_slot.call.func, cl_map, ctx
                ))

                if call_slot.pure:
                    if isinstance(stmt.value.args[1], ast.Name):
                        target = self.get_target(stmt.value.args[1].id, ctx)
                    else:
                        target = self.get_target(stmt.value.args[1].func.func.id)

                    if not target.pure:
                        raise InvalidProgramException(
                            stmt.value,
                            'call_slots.impure_closure_call.inside_pure_proof'
                        )

                viper_stmts.extend(self.translate_stmt(stmt, ctx))

                position = self.to_position(stmt, ctx)
                info = self.no_info(ctx)
                viper_stmts.append(self.viper.LocalVarAssign(
                    call_counter.ref(),
                    self.viper.Add(
                        call_counter.ref(),
                        self.viper.IntLit(1, position, info),
                        position,
                        info
                    ),
                    position,
                    info
                ))

            elif isinstance(stmt, ast.Assign):

                assert is_closure_call(stmt.value)

                for arg_call, arg_slot in zip(stmt.value.args[0].args, call_slot.call.args):
                    viper_stmts.append(self._application_call_slot_arg_match(
                        arg_call, arg_slot, cl_map, ctx
                    ))
                viper_stmts.append(self._application_call_slot_arg_match(
                    stmt.value.args[0].func, call_slot.call.func, cl_map, ctx
                ))

                viper_stmts.extend(self.translate_stmt(stmt, ctx))

                position = self.to_position(stmt, ctx)
                info = self.no_info(ctx)
                viper_stmts.append(self.viper.LocalVarAssign(
                    call_counter.ref(),
                    self.viper.Add(
                        call_counter.ref(),
                        self.viper.IntLit(1, position, info),
                        position,
                        info
                    ),
                    position,
                    info
                ))

                continue

            elif isinstance(stmt, ast.Assert):
                viper_stmts.extend(self.translate_stmt(stmt, ctx))

            elif isinstance(stmt, ast.FunctionDef):
                assert is_call_slot_proof(stmt)
                viper_stmts.extend(self.translate_stmt(stmt, ctx))

            elif isinstance(stmt, ast.If):
                position = self.to_position(stmt, ctx)
                info = self.no_info(ctx)

                cond = self._translate_pure_expr(
                    stmt.test, ctx, target_type=self.viper.Bool
                )

                then_body = self._proof_translate_body_only(
                    stmt.body, proof, call_slot, call_counter, cl_map, ctx
                )
                then_block = self.translate_block(then_body, position, info)

                else_body = self._proof_translate_body_only(
                    stmt.orelse, proof, call_slot, call_counter, cl_map, ctx
                )
                else_block = self.translate_block(else_body, position, info)

                viper_stmts.append(self.viper.If(
                    cond, then_block, else_block, position, info
                ))

            else:
                assert False

        return viper_stmts

    def _translate_pure_expr(
        self,
        node: ast.expr,
        ctx: Context,
        target_type: object = None,
        impure: bool = False
    ) -> Expr:
        stmts, expr = self.translate_expr(node, ctx, target_type=target_type, impure=impure)
        if stmts:
            raise InvalidProgramException(node, 'purity.violated')
        return expr


class _VarReplacer(ast.NodeTransformer):

    def replace(self, node: ast.expr, arg_map: Dict[str, ast.expr]) -> ast.expr:
        self.arg_map = arg_map
        return self.visit(node)

    def visit_Name(self, name: ast.Name) -> ast.expr:
        return deepcopy(self.arg_map[name.id]) if name.id in self.arg_map else name
