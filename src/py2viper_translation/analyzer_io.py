"""
Analyzer that collects information about IO operations.
"""


import ast
import py2viper_translation


from mypy.types import AnyType
from py2viper_contracts.io import IO_OPERATION_PROPERTY_FUNCS
from py2viper_translation.lib.constants import BOOL_TYPE
from py2viper_translation.lib.program_nodes import (
    ProgramNodeFactory,
    PythonClass,
    PythonIOOperation,
    PythonType,
    PythonVar,
    )
from py2viper_translation.lib.util import (
    InvalidProgramException,
    UnsupportedException,
    )
from typing import List


class IOOperationAnalyzer(ast.NodeVisitor):
    """
    Walks through IO operation AST and collects the needed information.
    """

    def __init__(
            self, parent: 'py2viper_translation.analyzer.Analyzer',
            node_factory: ProgramNodeFactory) -> None:
        self._parent = parent
        self._program = parent.program
        self._types = parent.types
        self._node_factory = node_factory
        self._place_class = parent.get_class('Place') # type: PythonClass

        self._current_io_operation = None # type: PythonIOOperation
        self._current_node = None # type: ast.FunctionDef
        self._in_property = False

    def _raise_invalid_operation(
            self,
            error_type: str,
            node: ast.AST = None):
        """ Raises InvalidProgramException.
        """
        node = node or self._current_node
        raise InvalidProgramException(
            node,
            'invalid.io_operation.' + error_type,
            )

    def _create_io_operation(
            self,
            node: ast.FunctionDef
            ) -> PythonIOOperation:
        """
        Creates non-initialized IO operation from an AST node and adds
        it to program.
        """
        name = node.name
        assert isinstance(name, str)
        operation = self._node_factory.create_python_io_operation(
            name,
            node,
            self._program,
            self._node_factory,
            )
        self._program.io_operations[name] = operation
        return operation

    def _check_type(self) -> None:
        """ Checks if operation type is ``bool``.
        """
        scope_prefix = self._current_io_operation.get_scope_prefix()
        func_type = self._types.get_func_type(scope_prefix)
        if isinstance(func_type, AnyType):
            self._raise_invalid_operation('return_type_not_bool')
        operation_type = self._parent.convert_type(func_type)
        if not operation_type or operation_type.name != BOOL_TYPE:
            self._raise_invalid_operation('return_type_not_bool')

    def _check_arg_types(self) -> None:
        """
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
                not default.func.id == 'Result'):           # type: ignore
                self._raise_invalid_operation('default_argument')

    def _typeof(self, node: ast.AST) -> PythonType:
        """ Returns the type of the given AST node.
        """
        assert isinstance(node, ast.arg)
        typ, _ = self._parent.types.get_type(
            [self._current_io_operation.name],
            node.arg)
        return self._parent.convert_type(typ)

    def _set_preset(self, inputs: List[ast.arg]) -> List[ast.arg]:
        """
        Checks that exactly one place is in preset, sets operation
        preset and returns input list with all places removed.
        """
        if (not inputs or
            self._typeof(inputs[0]) != self._place_class):
            self._raise_invalid_operation('invalid_preset')
        for input in inputs[1:]:
            if self._typeof(input) == self._place_class:
                self._raise_invalid_operation('invalid_preset')
        in_place = self._node_factory.create_python_var(
            inputs[0].arg, inputs[0], self._place_class)
        self._current_io_operation.set_preset([in_place])
        return inputs[1:]

    def _set_postset(self, outputs: List[ast.arg]) -> List[ast.arg]:
        """
        Checks that exactly one place is in postset, sets operation
        postset and returns input list with all places removed.
        """
        counter = 0
        for output in outputs:
            if self._typeof(output) == self._place_class:
                counter += 1
        if counter > 1:
            self._raise_invalid_operation('invalid_postset')
        elif counter == 1:
            if self._typeof(outputs[-1]) != self._place_class:
                self._raise_invalid_operation('invalid_postset')
            out_place = self._node_factory.create_python_var(
                outputs[-1].arg, outputs[-1], self._place_class)
            self._current_io_operation.set_postset([out_place])
            return outputs[:-1]

    def _parse_arguments(self) -> None:
        """ Parses and checks operation arguments.
        """
        node = self._current_node

        self._check_arg_types()

        inputs = node.args.args[:-len(node.args.defaults)]
        outputs = node.args.args[len(node.args.defaults)-1:]

        inputs = self._set_preset(inputs)
        outputs = self._set_postset(outputs)

        def node_to_var(node: ast.arg) -> PythonVar:
            return self._node_factory.create_python_var(
                node.arg, node, self._typeof(node))

        self._current_io_operation.set_inputs(
                list(map(node_to_var, inputs)))
        self._current_io_operation.set_outputs(
                list(map(node_to_var, outputs)))

    def analyze_io_operation(self, node: ast.FunctionDef) -> None:
        """
        Analyzes AST node representing IO operation and extracts
        information from it.
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

    def visit_Call(self, node: ast.Call) -> None:
        assert self._current_io_operation is not None
        assert self._current_node is not None

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
                raise UnsupportedException(node)
            self._in_property = True
            for arg in node.args:
                self.visit(arg)
            self._in_property = False
        else:
            for arg in node.args:
                self.visit(arg)

    def visit_Name(self, node: ast.Name) -> None:
        if self._in_property:
            if not self._current_io_operation.is_input(node.id):
                self._raise_invalid_operation('depends_on_not_imput', node)
