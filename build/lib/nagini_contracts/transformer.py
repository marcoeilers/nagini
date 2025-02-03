"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import ast

from nagini_contracts.contracts import GHOST_PREFIX


contract_keywords = frozenset(["Requires", "Ensures", "Exsures",
                               "Invariant",
                               "Assume", "Assert",
                               "Old",
                               "Result",
                               "Implies",
                               "Forall", "Exists",
                               "Acc",
                               "Fold", "Unfold", "Unfolding",
                               "Pure", "Predicate",
                               "Ghost",])


class GhostCollector(ast.NodeVisitor):
    """
    AST visitor to collect ghost variables and functions.
    """
    def __init__(self):
        self.ghost_vars = set()
        self.ghost_funcs = set()

    @classmethod
    def collect(cls, tree):
        """
        Collects and returns two sets containing the names of ghost variables
        and functions.
        :param tree: The AST of the program.
        :return: Tuple of sets (ghost_vars, ghost_funcs).
        """
        collector = cls()
        collector.visit(tree)
        return collector.ghost_vars, collector.ghost_funcs

    def visit_Name(self, node):
        if node.id.startswith(GHOST_PREFIX):
            self.ghost_vars.add(node.id)

    def visit_Attribute(self, node):
        if node.attr.startswith(GHOST_PREFIX):
            self.ghost_vars.add(node.attr)

    def visit_FunctionDef(self, node):
        decorator_list = [dec.id for dec in node.decorator_list]
        if "Ghost" in decorator_list:
            self.ghost_funcs.add(node.name)


class NoOpCollector(ast.NodeVisitor):
    """
    AST visitor that collects @pure, @predicate and @ghost annotations.
    """
    def __init__(self, ghost_vars, ghost_funcs):
        self.ghost_vars = ghost_vars
        self.ghost_funcs = ghost_funcs
        self.noop_stmts = set()
        self._cur_stmt = None

    @property
    def _cur_stmt(self):
        return self.__cur_stmt

    @_cur_stmt.setter
    def _cur_stmt(self, stmt):
        assert stmt is None or \
               isinstance(stmt, ast.stmt), "_cur_stmt is not a stmt or None"
        self.__cur_stmt = stmt

    @classmethod
    def collect(cls, tree, ghost_vars, ghost_funcs):
        """
        Collects and returns statements that need to be turned into no-ops
        (i.e., deleted from the AST).

        :param tree: The AST of the program.
        :param ghost_vars: A set containing the names of ghost variables.
        :param ghost_funcs: A set containing the names of ghost functions.
        :return: A set containing ast.stmt's that need to be deleted.
        """
        collector = cls(ghost_vars, ghost_funcs)
        collector.visit(tree)
        return collector.noop_stmts

    def visit_Module(self, node):
        for stmt in node.body:
            self._cur_stmt = stmt
            self.visit(stmt)

    def visit_Name(self, node):
        if node.id.startswith(GHOST_PREFIX):
            self.noop_stmts.add(self._cur_stmt)

    def visit_Attribute(self, node):
        if node.attr.startswith(GHOST_PREFIX):
            self.noop_stmts.add(self._cur_stmt)

    def visit_FunctionDef(self, node):
        if node.name in self.ghost_funcs:
            self.noop_stmts.add(node)
            return

        self.generic_visit(node)

    def visit_Call(self, node):
        func_name = None
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        if func_name in contract_keywords or func_name in self.ghost_funcs:
            self.noop_stmts.add(self._cur_stmt)
            return

        self.generic_visit(node)

    def visit_Delete(self, node):
        self._cur_stmt = node
        self.generic_visit(node)

    def visit_Assign(self, node):
        self._cur_stmt = node
        self.generic_visit(node)

    def visit_AugAssign(self, node):
        self._cur_stmt = node
        self.generic_visit(node)

    def visit_Expr(self, node):
        self._cur_stmt = node
        self.generic_visit(node)

    def visit_For(self, node):
        self._cur_stmt = node
        self.generic_visit(node)

    def visit_While(self, node):
        self._cur_stmt = node
        self.generic_visit(node)

    def visit_If(self, node):
        self._cur_stmt = node
        self.generic_visit(node)


class EmptyBodyCollector(ast.NodeVisitor):
    """
    Collects statement that have an empty body due to AST rewriting.
    """
    def __init__(self):
        self.noop_stmts = set()

    @classmethod
    def collect(cls, tree):
        """
        Collects and returns statements that need to be removed, because their
        body does not contain any statements (e.g., after removing all
        statements involving ghost variables).

        :param tree: The AST of the program.
        :return: Set containing ast.stmt's that need to be deleted.
        """
        collector = cls()
        collector.visit(tree)
        return collector.noop_stmts

    def visit_FunctionDef(self, node):
        if not node.body:
            self.noop_stmts.add(node)
            return

        self.generic_visit(node)

    def visit_ClassDef(self, node):
        if not node.body:
            self.noop_stmts.add(node)
            return

        self.generic_visit(node)

    def visit_For(self, node):
        if not node.body:
            self.noop_stmts.add(node)
            return

        self.generic_visit(node)

    def visit_While(self, node):
        if not node.body:
            self.noop_stmts.add(node)
            return

        self.generic_visit(node)

    def visit_If(self, node):
        if not node.body:
            self.noop_stmts.add(node)
            return

        self.generic_visit(node)

    def visit_Try(self, node):
        if not node.body:
            self.noop_stmts.add(node)
            return

        self.generic_visit(node)


class StmtEraser(ast.NodeTransformer):
    """
    AST visitor that deletes statements passed by 'noop_stmts'.
    """
    def __init__(self, noop_stmts):
        self.noop_stmts = noop_stmts

    @classmethod
    def erase(cls, tree, noop_stmts):
        """
        Removes statements in 'noop_stmts' from the AST.

        :param tree: The AST to be modified.
        :param noop_stmts: The statements to be removed.
        :return: The modified AST.
        """
        eraser = cls(noop_stmts)
        return eraser.visit(tree)

    def visit(self, node):
        if isinstance(node, ast.stmt) and node in self.noop_stmts:
            return None

        self.generic_visit(node)
        return node


def transform_ast(tree):
    """
    Applies necessary transformations to the AST to make code containing
    contracts run correctly.
    :param tree: source node of the AST
    :return: source node of the transformed AST
    """
    transformed_ast = tree
    # Collect ghost variables and functions.
    ghost_vars, ghost_funcs = GhostCollector.collect(tree)
    # Collect no-op statements.
    noop_stmts = NoOpCollector.collect(transformed_ast, ghost_vars, ghost_funcs)
    while noop_stmts:
        # Remove no-op statements from the AST.
        transformed_ast = StmtEraser.erase(transformed_ast, noop_stmts)
        # Collect statements with an empty body.
        noop_stmts = EmptyBodyCollector.collect(transformed_ast)

    return transformed_ast
