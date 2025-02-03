"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Visitors for collecting conditions that guard AST nodes."""


import ast


class GuardCollectingVisitor(ast.NodeVisitor):
    """Visitor that maintains guard information.

    For each assertion, a list of conditions that have to be true for
    that assertion to be enabled is stored in ``current_guard``
    property.
    """

    def __init__(self) -> None:
        super().__init__()
        self.current_guard = None   # type: Optional[List[ast.AST]]

    def traverse(self, node: ast.AST) -> None:
        """Traverse ``node``."""
        assert self.current_guard is None
        self.current_guard = []
        self.visit(node)
        assert self.current_guard is not None
        assert len(self.current_guard) == 0
        self.current_guard = None

    def visit_Call(self, node: ast.Call) -> None:
        """Add ``Implies`` condition to guard."""
        if (isinstance(node.func, ast.Name) and
                node.func.id == 'Implies'):
            assert len(node.args) == 2
            self.current_guard.append(node.args[0])
            self.visit(node.args[1])
            self.current_guard.pop()
        else:
            self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> None:
        """Add ``If`` condition to guard."""
        # Visit then branch.
        self.current_guard.append(node.test)
        self.visit(node.body)
        self.current_guard.pop()
        # Visit else branch.
        condition = ast.UnaryOp(ast.Not(), node.test)
        self.current_guard.append(condition)
        self.visit(node.orelse)
        self.current_guard.pop()
