import ast
from nagini_translation import analyzer as analzyer_pkg
from nagini_translation.lib.program_nodes import CallSlot
from nagini_translation.lib.util import (
    UnsupportedException,
    InvalidProgramException,
)


class CallSlotAnalyzer(ast.NodeVisitor):

    def __init__(self, analyzer: 'analyzer_pkg.Analyzer') -> None:
        self.analyzer = analyzer
        self.call_slot = None  # type: CallSlot

    def analyze(self, node: ast.FunctionDef) -> None:
        """
        Preprocess the call slot `node'.
        """
        assert is_call_slot(node)

        analyzer = self.analyzer
        scope = analyzer.module

        if analyzer.current_function:
            raise UnsupportedException(node, 'nested call slots')
        if analyzer.current_class:
            raise UnsupportedException(node, 'call slot as class member')
        if analyzer._is_illegal_magic_method_name(node.name):
            raise InvalidProgramException(node, 'illegal.magic.method')

        analyzer.define_new(scope, node.name, node)

        self.call_slot = analyzer.node_factory.crreate_call_slot(
            node.name,
            node,
            scope,
            analyzer.node_factory
        )

        scope.methods[node.name] = self.call_slot

        # TODO: set current_func (restore old current_func at the end)
        # TODO: visit args
        # self.__collect_normal_variables()
        # TODO: set call_slot.type
        # TODO: visit call slot body
        # TODO: other call slot preprocessing/checks

    def __collect_normal_variables(self) -> None:
        assert self.call_slot

        for arg in self.call_slot.node.args.args:
            self.__add_normal_variable(arg)

    def __add_normal_variable(self, arg: ast.arg) -> None:
        # FIXME: do we need to considere type variables here?
        arg_type = self.analyzer.typeof(arg)

        arg_var = self.analyzer.node_factory.create_python_var(arg.arg, arg, arg_type)
        # FIXME: has no get_alt_types
        arg_var.alt_types = self.get_alt_types(arg)

        self.call_slot.normal_variables[arg.arg] = arg_var



def is_call_slot(node: ast.FunctionDef) -> bool:
    """
    Whether node is a call slot declaration.
    """
    return _has_single_decorator(node, 'CallSlot')


def is_universally_quantified(node: ast.FunctionDef) -> bool:
    """
    Whether a function introduces universally quantified variables
    """
    return _has_single_decorator(node, 'UniversallyQuantified')


def is_call_slot_proof(node: ast.FunctionDef) -> bool:
    """
    Whether a function introduces universally quantified variables
    """
    return _has_single_decorator(node, 'CallSlotProof')


def _has_single_decorator(node: ast.FunctionDef, decorator: str) -> bool:
    """
    Whether `node' has only one decorator that equals to `decorator'
    """
    # NOTE: could be refactored out into a nagini 'util' package
    return (
        len(node.decorator_list) == 1 and
        node.decorator_list[0].id == decorator
    )
