"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Classes for performing well-formedness checks of IO stuff."""


import ast

from typing import List

from nagini_translation.lib.util import InvalidProgramException


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
            module: 'lib.program_nodes.PythonModule',
            translator: 'Translator') -> None:
        super().__init__()
        self._body = body
        self._results = {var.name for var in results}
        self._existentials = dict(
            (var.name, var) for var in io_existentials)
        self._undefined_existentials = set(self._existentials.keys())
        self._module = module
        self._translator = translator
        self._counter = 0

    def check(self) -> None:
        """Check that body is well formed."""
        self.visit(self._body)

    def visit_Name(self, node: ast.Name) -> None:
        """Check that only allowed names are used in the body."""
        name = node.id
        if name == 'Acc':
            _raise_error(node, 'non_pure')
        if name in self._undefined_existentials:
            _raise_error(node, 'use_of_undefined_existential')

    def visit_Call(self, node: ast.Call) -> None:
        """Check IO operation use and define existential variables."""
        containers = [self._module]
        containers.extend(self._module.get_included_modules())
        target = None
        if not isinstance(node.func, ast.Call):
            target = self._translator.get_target(node, containers, None)
        if target and target.__class__.__name__ == 'PythonIOOperation':
            operation = target
            parameter_count = len(operation.get_parameters())
            results = node.args[parameter_count:]
            for i, arg in enumerate(results):
                if not isinstance(arg, ast.Name):
                    _raise_error(node, 'not_variable_in_result_position')
                elif (arg.id not in self._existentials and
                      arg.id not in self._results):
                    _raise_error(node, 'variable_not_existential')
                elif arg.id in self._undefined_existentials:
                    self._undefined_existentials.remove(arg.id)
                    var = self._existentials[arg.id]
                    var.set_defining_info(self._counter, node,
                                          operation.get_results()[i])
                    self._counter += 1
        self.visit(node.func)
        for arg in node.args:
            self.visit(arg)
