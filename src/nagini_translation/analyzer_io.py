"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Analyzer that collects information about IO operations."""


import ast

from mypy.types import AnyType
from nagini_contracts.io_contracts import IO_OPERATION_PROPERTY_FUNCS
from typing import cast, List

from nagini_translation.lib import program_nodes as nodes
from nagini_translation.lib.constants import (
    BOOL_TYPE,
    EVAL_IO_SIGNATURE,
    OBJECT_TYPE,
)
from nagini_translation.lib.util import (
    construct_lambda_prefix,
    InvalidProgramException,
    UnsupportedException,
)


class IOOperationAnalyzer(ast.NodeVisitor):
    """Walks through IO operation AST and collects the needed information."""

    def __init__(
            self, parent: 'nagini_translation.analyzer.Analyzer',
            node_factory: nodes.ProgramNodeFactory) -> None:
        self._parent = parent
        self._types = parent.types
        self._node_factory = node_factory
        self._place_class = parent.find_or_create_class(
            'Place', module=parent.module.global_module)
        self._place_class.superclass = parent.find_or_create_class(
            'object', module=parent.module.global_module)

        self._current_io_operation = None   # type: nodes.PythonIOOperation
        self._current_node = None           # type: ast.FunctionDef
        self._in_property = False
        self._current_lambdas = []

    def _raise_invalid_operation(
            self,
            error_type: str,
            node: ast.AST = None):
        """Raise InvalidProgramException."""
        node = node or self._current_node
        raise InvalidProgramException(
            node,
            'invalid.io_operation.' + error_type,
        )

    def _create_io_operation(
            self, node: ast.FunctionDef) -> nodes.PythonIOOperation:
        """Create IO operation.

        Creates non-initialized IO operation from an AST node and adds
        it to the module.
        """
        name = node.name
        assert isinstance(name, str)
        operation = self._node_factory.create_python_io_operation(
            name,
            node,
            self._parent.module,
            self._node_factory,
        )
        self._parent.module.io_operations[name] = operation
        return operation

    def _check_type(self) -> None:
        """Check if operation type is ``bool``."""
        op_name = self._current_io_operation.name
        func_type = self._parent.module.get_func_type([op_name])
        if isinstance(func_type, AnyType):
            self._raise_invalid_operation('return_type_not_bool')
        operation_type = self._parent.convert_type(func_type,
                                                   self._current_io_operation.node)
        if not operation_type or operation_type.name != BOOL_TYPE:
            self._raise_invalid_operation('return_type_not_bool')

    def _check_arg_types(self) -> None:
        """Allow only certain types of args.

        Do not allow ``*args`` and ``**kwargs``. Only ``Result()`` is
        allowed as default value.
        """
        node = self._current_node
        if node.args.vararg:
            self._raise_invalid_operation('vararg')
        if node.args.kwarg:
            self._raise_invalid_operation('kwarg')
        for default in node.args.defaults:
            if (not isinstance(default, ast.Call) or
                    not isinstance(default.func, ast.Name) or   # type: ignore
                    not default.func.id == 'Result'):  # type: ignore
                self._raise_invalid_operation('default_argument')

    def _typeof(self, node: ast.AST,
                lambda_: ast.Lambda = None) -> nodes.PythonType:
        """Get the type of the given AST node."""
        assert isinstance(node, ast.arg)
        if (self._current_io_operation.name == EVAL_IO_SIGNATURE[0] and
                node.arg == EVAL_IO_SIGNATURE[2]):
            return self._parent.module.global_module.classes[OBJECT_TYPE]
        scopes = [self._current_io_operation.name]
        scopes.extend(self._current_lambdas)
        if lambda_:
            prefix = construct_lambda_prefix(
                lambda_.lineno, lambda_.col_offset)
            scopes.append(prefix)
        typ, _ = self._parent.module.get_type(scopes, node.arg)
        # to avoid problems with boxed versions not being reference-equal,
        # always use unboxed versions
        result = self._parent.convert_type(typ, node).try_unbox()
        return result

    def _set_preset(self, inputs: List[ast.arg]) -> List[ast.arg]:
        """Check and set preset.

        Checks that exactly one place is in preset, sets operation
        preset and returns input list with all places removed.
        """
        if self._current_io_operation.name == 'join_io':
            # Special handling of built-in “join_io”.
            assert len(inputs) == 2
            in_places = []
            for i in range(2):
                assert self._typeof(inputs[i]) == self._place_class
                in_place = self._node_factory.create_python_var(
                    inputs[i].arg, inputs[i], self._place_class)
                in_places.append(in_place)
            self._current_io_operation.set_preset(in_places)
            return []
        if not inputs or self._typeof(inputs[0]) != self._place_class:
            self._raise_invalid_operation('invalid_preset')
        for inp in inputs[1:]:
            if self._typeof(inp) == self._place_class:
                self._raise_invalid_operation('invalid_preset')
        in_place = self._node_factory.create_python_var(
            inputs[0].arg, inputs[0], self._place_class)
        self._current_io_operation.set_preset([in_place])
        return inputs[1:]

    def _set_postset(self, outputs: List[ast.arg]) -> List[ast.arg]:
        """Check and set postset.

        Checks that exactly one place is in postset, sets operation
        postset and returns input list with all places removed.
        """
        counter = 0
        for output in outputs:
            if self._typeof(output) == self._place_class:
                counter += 1
        if counter > 1:
            if self._current_io_operation.name == 'split_io':
                # Special handling of built-in “split_io”.
                assert len(outputs) == 2
                out_places = []
                for i in range(2):
                    assert self._typeof(outputs[i]) == self._place_class
                    out_place = self._node_factory.create_python_var(
                        outputs[i].arg, outputs[i], self._place_class)
                    out_places.append(out_place)
                self._current_io_operation.set_postset(out_places)
                return []
            else:
                self._raise_invalid_operation('invalid_postset')
        elif counter == 1:
            if self._typeof(outputs[-1]) != self._place_class:
                self._raise_invalid_operation('invalid_postset')
            out_place = self._node_factory.create_python_var(
                outputs[-1].arg, outputs[-1], self._place_class)
            self._current_io_operation.set_postset([out_place])
            return outputs[:-1]
        else:
            return outputs

    def _parse_arguments(self) -> None:
        """Parse and check operation arguments."""
        node = self._current_node

        self._check_arg_types()

        if node.args.defaults:
            inputs = node.args.args[:-len(node.args.defaults)]
            outputs = node.args.args[-len(node.args.defaults):]
        else:
            inputs = node.args.args[:]
            outputs = []

        inputs = self._set_preset(inputs)
        outputs = self._set_postset(outputs)

        self._current_io_operation.set_inputs([
            self._node_factory.create_python_var(
                node.arg, node, self._typeof(node))
            for node in inputs])
        self._current_io_operation.set_outputs([
            self._node_factory.create_python_var(
                node.arg, node, self._typeof(node))
            for node in outputs])

    def analyze_io_operation(self, node: ast.FunctionDef) -> None:
        """Analyze AST node representing IO operation.

        That is: extract information and perform some basic
        well-formedness checks.
        """
        assert self._current_io_operation is None
        assert self._current_node is None

        self._current_node = node
        operation = self._create_io_operation(node)
        self._current_io_operation = operation
        self._check_type()
        self._parse_arguments()

        for child in node.body:
            self.visit(child)

        self._current_node = None
        self._current_io_operation = None

    def visit_Return(self, node: ast.Return) -> None:
        """Parse IO operation body.

        IO operation body must be a single expression that is returned.
        """
        body = node.value
        lambda_ = None

        if (isinstance(body, ast.Call) and
                isinstance(body.func, ast.Call) and
                isinstance(body.func.func, ast.Name) and
                body.func.func.id.startswith('IOExists')):
            lambda_ = cast(ast.Lambda, body.args[0])
            args = lambda_.args.args
            io_existential_creators = [
                self._node_factory.create_python_var_creator(
                    arg.arg, arg, self._typeof(arg, lambda_))
                for arg in args
            ]
            body = lambda_.body
        else:
            io_existential_creators = []
        if not self._current_io_operation.set_body(body):
            self._raise_invalid_operation(
                'duplicate_body',
                node)
        assert self._current_io_operation.set_io_existentials(
            io_existential_creators)
        if lambda_ is not None:
            prefix = construct_lambda_prefix(
                lambda_.lineno, lambda_.col_offset)
            self._current_lambdas.append(prefix)
            self.visit(node.value.args[0].body)
            self._current_lambdas.pop()
        else:
            self.visit(node.value)

    def visit_Call(self, node: ast.Call) -> None:
        """Parse IO operation properties.

        Currently, only parses properties such as ``Terminates`` and
        ``TerminationMeasure``.
        """
        assert self._current_io_operation is not None
        assert self._current_node is not None

        body_prefix = None

        if (isinstance(node.func, ast.Name) and
                node.func.id in IO_OPERATION_PROPERTY_FUNCS):

            for child in self._current_node.body:
                if (isinstance(child, ast.Expr) and
                        child.value == node):
                    break
            else:
                self._raise_invalid_operation(
                    'misplaced_property',
                    node)

            operation = self._current_io_operation
            arg = node.args[0]
            if node.func.id == 'Terminates':
                if not operation.set_terminates(arg):
                    self._raise_invalid_operation(
                        'duplicate_property',
                        node)
            elif node.func.id == 'TerminationMeasure':
                if not operation.set_termination_measure(arg):
                    self._raise_invalid_operation(
                        'duplicate_property',
                        node)
            else:
                raise UnsupportedException(node,
                                           'Unsupported property type.')
            self._in_property = True
            for arg in node.args:
                self.visit(arg)
            self._in_property = False
            return
        elif isinstance(node.func, ast.Name) and node.func.id in ('IOForall', 'Forall', 'Exists'):
            operation = self._current_io_operation
            assert len(node.args[1].args.args) == 1
            arg_type = self._parent.get_target(node.args[0], operation.module)
            lambda_ = node.args[1]
            body_prefix = construct_lambda_prefix(lambda_.lineno,
                                                  getattr(lambda_, 'col_offset',
                                                          None))
            for arg in lambda_.args.args:
                var = self._node_factory.create_python_var(arg.arg, arg,
                                                           arg_type)
                operation._io_universals.append(var)
        elif (isinstance(node.func, ast.Call) and isinstance(node.func.func, ast.Name)
              and node.func.func.id == 'IOExists'):
            lambda_ = node.args[0]
            arg = lambda_.args.args[0]
            body_prefix = construct_lambda_prefix(
                lambda_.lineno, lambda_.col_offset)
            creator = self._node_factory.create_python_var_creator(
                arg.arg, arg, self._typeof(arg, lambda_))
            current_existentials = self._current_io_operation.get_io_existentials()
            current_existentials.append(creator)
        if body_prefix:
            self._current_lambdas.append(body_prefix)
        for arg in node.args:
            self.visit(arg)
        if body_prefix:
            self._current_lambdas.pop()

    def visit_Name(self, node: ast.Name) -> None:
        """Check if node is an operation input.

        This method is expected to be called by ``visit_Call`` on IO
        operation property arguments. Checks if provided node is an
        operation input and raises an error, if it is not.
        """
        if self._in_property:
            if not self._current_io_operation.is_input(node.id):
                self._raise_invalid_operation('depends_on_not_imput', node)
