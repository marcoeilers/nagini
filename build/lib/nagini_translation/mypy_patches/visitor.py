"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
import re

from mypy.nodes import (
    Block, MypyFile, FuncBase, FuncItem, CallExpr, ClassDef, Decorator, FuncDef,
    ExpressionStmt, AssignmentStmt, OperatorAssignmentStmt, WhileStmt,
    ForStmt, ReturnStmt, AssertStmt, DelStmt, IfStmt, RaiseStmt,
    TryStmt, WithStmt, NameExpr, MemberExpr, OpExpr, SliceExpr, CastExpr, RevealExpr,
    UnaryExpr, ListExpr, TupleExpr, DictExpr, SetExpr, IndexExpr, AssignmentExpr,
    GeneratorExpr, ListComprehension, SetComprehension, DictionaryComprehension,
    ConditionalExpr, TypeApplication, ExecStmt, Import, ImportFrom,
    LambdaExpr, ComparisonExpr, OverloadedFuncDef, YieldFromExpr,
    YieldExpr, StarExpr, BackquoteExpr, AwaitExpr, PrintStmt, SuperExpr, Node, REVEAL_TYPE,
)


class TraverserVisitor:
    """
    A custom implementation of mypy's TraverserVisitor that we can subclass (cannot do that with the original one
    because it's compiled apparently) and that does not use accept methods (because they expect an instance of the
    original mypy visitor class) and instead uses reflection to call visit-methods.
    """

    def __init__(self) -> None:
        pass

    def visit(self, o):
        type_name = o.__class__.__name__
        visitor_name = 'visit' + re.sub('([A-Z]{1})', r'_\1', type_name).lower()
        if hasattr(self, visitor_name):
            getattr(self, visitor_name)(o)

    # Visit methods

    def visit_mypy_file(self, o: MypyFile) -> None:
        for d in o.defs:
            self.visit(d)

    def visit_block(self, block: Block) -> None:
        for s in block.body:
            self.visit(s)

    def visit_func(self, o: FuncItem) -> None:
        if o.arguments is not None:
            for arg in o.arguments:
                init = arg.initializer
                if init is not None:
                    self.visit(init)

            for arg in o.arguments:
                self.visit_var(arg.variable)
        self.visit(o.body)

    def visit_var(self, o: 'mypy.nodes.Var') -> None:
        pass

    def visit_func_def(self, o: FuncDef) -> None:
        self.visit_func(o)

    def visit_overloaded_func_def(self, o: OverloadedFuncDef) -> None:
        for item in o.items:
            self.visit(item)
        if o.impl:
            self.visit(o.impl)

    def visit_class_def(self, o: ClassDef) -> None:
        for d in o.decorators:
            self.visit(d)
        for base in o.base_type_exprs:
            self.visit(base)
        if o.metaclass:
            self.visit(o.metaclass)
        for v in o.keywords.values():
            self.visit(v)
        self.visit(o.defs)
        if o.analyzed:
            self.visit(o.analyzed)

    def visit_decorator(self, o: Decorator) -> None:
        self.visit(o.func)
        self.visit(o.var)
        for decorator in o.decorators:
            self.visit(decorator)

    def visit_expression_stmt(self, o: ExpressionStmt) -> None:
        self.visit(o.expr)

    def visit_assignment_stmt(self, o: AssignmentStmt) -> None:
        self.visit(o.rvalue)
        for l in o.lvalues:
            self.visit(l)

    def visit_operator_assignment_stmt(self, o: OperatorAssignmentStmt) -> None:
        self.visit(o.rvalue)
        self.visit(o.lvalue)

    def visit_while_stmt(self, o: WhileStmt) -> None:
        self.visit(o.expr)
        self.visit(o.body)
        if o.else_body:
            self.visit(o.else_body)

    def visit_for_stmt(self, o: ForStmt) -> None:
        self.visit(o.index)
        self.visit(o.expr)
        self.visit(o.body)
        if o.else_body:
            self.visit(o.else_body)

    def visit_return_stmt(self, o: ReturnStmt) -> None:
        if o.expr is not None:
            self.visit(o.expr)

    def visit_assert_stmt(self, o: AssertStmt) -> None:
        if o.expr is not None:
            self.visit(o.expr)
        if o.msg is not None:
            self.visit(o.msg)

    def visit_del_stmt(self, o: DelStmt) -> None:
        if o.expr is not None:
            self.visit(o.expr)

    def visit_if_stmt(self, o: IfStmt) -> None:
        for e in o.expr:
            self.visit(e)
        for b in o.body:
            self.visit(b)
        if o.else_body:
            self.visit(o.else_body)

    def visit_raise_stmt(self, o: RaiseStmt) -> None:
        if o.expr is not None:
            self.visit(o.expr)
        if o.from_expr is not None:
            self.visit(o.from_expr)

    def visit_try_stmt(self, o: TryStmt) -> None:
        self.visit(o.body)
        for i in range(len(o.types)):
            tp = o.types[i]
            if tp is not None:
                self.visit(tp)
            self.visit(o.handlers[i])
        for v in o.vars:
            if v is not None:
                self.visit(v)
        if o.else_body is not None:
            self.visit(o.else_body)
        if o.finally_body is not None:
            self.visit(o.finally_body)

    def visit_with_stmt(self, o: WithStmt) -> None:
        for i in range(len(o.expr)):
            self.visit(o.expr[i])
            targ = o.target[i]
            if targ is not None:
                self.visit(targ)
        self.visit(o.body)

    def visit_member_expr(self, o: MemberExpr) -> None:
        self.visit(o.expr)

    def visit_yield_from_expr(self, o: YieldFromExpr) -> None:
        self.visit(o.expr)

    def visit_yield_expr(self, o: YieldExpr) -> None:
        if o.expr:
            self.visit(o.expr)

    def visit_call_expr(self, o: CallExpr) -> None:
        for a in o.args:
            self.visit(a)
        self.visit(o.callee)
        if o.analyzed:
            self.visit(o.analyzed)

    def visit_op_expr(self, o: OpExpr) -> None:
        self.visit(o.left)
        self.visit(o.right)

    def visit_comparison_expr(self, o: ComparisonExpr) -> None:
        for operand in o.operands:
            self.visit(operand)

    def visit_slice_expr(self, o: SliceExpr) -> None:
        if o.begin_index is not None:
            self.visit(o.begin_index)
        if o.end_index is not None:
            self.visit(o.end_index)
        if o.stride is not None:
            self.visit(o.stride)

    def visit_cast_expr(self, o: CastExpr) -> None:
        self.visit(o.expr)

    def visit_reveal_expr(self, o: RevealExpr) -> None:
        if o.kind == REVEAL_TYPE:
            assert o.expr is not None
            self.visit(o.expr)
        else:
            # RevealLocalsExpr doesn't have an inner expression
            pass

    def visit_assignment_expr(self, o: AssignmentExpr) -> None:
        self.visit(o.target)
        self.visit(o.value)

    def visit_unary_expr(self, o: UnaryExpr) -> None:
        self.visit(o.expr)

    def visit_list_expr(self, o: ListExpr) -> None:
        for item in o.items:
            self.visit(item)

    def visit_tuple_expr(self, o: TupleExpr) -> None:
        for item in o.items:
            self.visit(item)

    def visit_dict_expr(self, o: DictExpr) -> None:
        for k, v in o.items:
            if k is not None:
                self.visit(k)
            self.visit(v)

    def visit_set_expr(self, o: SetExpr) -> None:
        for item in o.items:
            self.visit(item)

    def visit_index_expr(self, o: IndexExpr) -> None:
        self.visit(o.base)
        self.visit(o.index)
        if o.analyzed:
            self.visit(o.analyzed)

    def visit_generator_expr(self, o: GeneratorExpr) -> None:
        for index, sequence, conditions in zip(o.indices, o.sequences,
                                               o.condlists):
            self.visit(sequence)
            self.visit(index)
            for cond in conditions:
                self.visit(cond)
        self.visit(o.left_expr)

    def visit_dictionary_comprehension(self, o: DictionaryComprehension) -> None:
        for index, sequence, conditions in zip(o.indices, o.sequences,
                                               o.condlists):
            self.visit(sequence)
            self.visit(index)
            for cond in conditions:
                self.visit(cond)
        self.visit(o.key)
        self.visit(o.value)

    def visit_list_comprehension(self, o: ListComprehension) -> None:
        self.visit(o.generator)

    def visit_set_comprehension(self, o: SetComprehension) -> None:
        self.visit(o.generator)

    def visit_conditional_expr(self, o: ConditionalExpr) -> None:
        self.visit(o.cond)
        self.visit(o.if_expr)
        self.visit(o.else_expr)

    def visit_type_application(self, o: TypeApplication) -> None:
        self.visit(o.expr)

    def visit_lambda_expr(self, o: LambdaExpr) -> None:
        self.visit_func(o)

    def visit_star_expr(self, o: StarExpr) -> None:
        self.visit(o.expr)

    def visit_backquote_expr(self, o: BackquoteExpr) -> None:
        self.visit(o.expr)

    def visit_await_expr(self, o: AwaitExpr) -> None:
        self.visit(o.expr)

    def visit_super_expr(self, o: SuperExpr) -> None:
        self.visit(o.call)

    def visit_import(self, o: Import) -> None:
        for a in o.assignments:
            self.visit(a)

    def visit_import_from(self, o: ImportFrom) -> None:
        for a in o.assignments:
            self.visit(a)

    def visit_print_stmt(self, o: PrintStmt) -> None:
        for arg in o.args:
            self.visit(arg)

    def visit_exec_stmt(self, o: ExecStmt) -> None:
        self.visit(o.expr)
        if o.globals:
            self.visit(o.globals)
        if o.locals:
            self.visit(o.locals)
