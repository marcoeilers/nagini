"""Classes for performing well-formedness checks of IO stuff."""


import ast

from typing import List

from py2viper_translation import lib    # pylint: disable=unused-import
from py2viper_translation.lib.util import InvalidProgramException


def _raise_error(node, error_type) -> None:
    """Raise error exception."""
    raise InvalidProgramException(
        node,
        'invalid.io_operation.body.' + error_type,
    )


class IOOperationBodyChecker(ast.NodeVisitor):
    """Perform some simple well formedness checks for IOOperation body.

    Performed checks:

    1.  ``IOExists`` are not nested.
    2.  Existential variables are defined before their use.
    """

    def __init__(
            self, body: ast.Expr,
            results: List['lib.program_nodes.PythonVar'],
            io_existentials: List['lib.program_nodes.PythonVarCreator'],
            program: 'lib.program_nodes.PythonProgram') -> None:
        super().__init__()
        self._body = body
        self._results = {var.name for var in results}
        self._existentials = {var.name for var in io_existentials}
        self._undefined_existentials = self._existentials.copy()
        self._program = program

    def check(self) -> None:
        """Check that body is well formed."""
        self.visit(self._body)

    def visit_Name(self, node: ast.Name) -> None:   # pylint: disable=invalid-name
        """Check that only allowed names are used in the body."""
        name = node.id
        if name.startswith('IOExists'):
            _raise_error(node, 'ioexists')
        if name in self._undefined_existentials:
            _raise_error(node, 'use_of_undefined_existential')

    def visit_Call(self, node: ast.Call) -> None:   # pylint: disable=invalid-name
        """Check IO operation use and define existential variables."""
        if (isinstance(node.func, ast.Name) and
                node.func.id in self._program.io_operations):
            operation = self._program.io_operations[node.func.id]
            result_count = len(operation.get_results())
            results = node.args[-result_count:]
            for arg in results:
                if not isinstance(arg, ast.Name):
                    _raise_error(node, 'not_variable_in_result_position')
                elif (arg.id not in self._existentials and
                      arg.id not in self._results):
                    _raise_error(node, 'variable_not_existential')
                elif arg.id in self._undefined_existentials:
                    self._undefined_existentials.remove(arg.id)
        self.visit(node.func)
        for arg in node.args:
            self.visit(arg)
