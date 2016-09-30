"""Wrappers for Scala error objects."""


from typing import Any, List

from py2viper_translation.lib.errors.messages import ERRORS, REASONS
from py2viper_translation.lib.errors.rules import Rules


class Position:
    """Wrapper around ``AbstractSourcePosition``."""

    def __init__(self, position: 'ast.AbstractSourcePosition') -> None:
        self._position = position
        if hasattr(position, 'id'):
            self.node_id = position.id()
        else:
            self.node_id = None

    @property
    def line(self) -> int:
        """Return ``start.line``."""
        return self._position.line()

    @property
    def column(self) -> int:
        """Return ``start.column``."""
        return self._position.column()

    def __str__(self) -> str:
        return str(self._position)


class Reason:
    """Wrapper around ``AbstractErrorReason``."""

    def __init__(self, reason_id: str, reason: 'AbstractErrorReason',
                 node: 'ast.Node' = None, vias: List[Any] = None,
                 reason_string: str = None) -> None:
        self._reason = reason
        self._node = node
        self._reason_string = reason_string
        self.identifier = reason_id
        self.vias = vias
        self.offending_node = reason.offendingNode()
        self.position = Position(self.offending_node.pos())

    def __str__(self) -> str:
        reason = self._reason_string or self._node or str(self.offending_node)
        return REASONS[self.identifier](reason)


class Error:
    """Wrapper around ``AbstractVerificationError``."""

    def __init__(self, error: 'AbstractVerificationError', rules: Rules,
                 reason_item: Any, node: 'ast.Node' = None,
                 vias: List[Any] = None) -> None:

        # Translate error id.
        viper_reason = error.reason()
        error_id = error.id()
        reason_id = viper_reason.id()
        key = error_id, reason_id
        if key in rules:
            error_id, reason_id = rules[key]

        # Construct object.
        self._error = error
        self._node = node
        self._vias = vias
        self.identifier = error_id
        if reason_item:
            self.reason = Reason(
                reason_id, viper_reason, reason_item.node,
                reason_item.vias, reason_item.reason_string)
        else:
            self.reason = Reason(reason_id, viper_reason)
        self.position = Position(error.pos())

    def pos(self) -> 'ast.AbstractSourcePosition':
        """Get position.

        .. todo:: Marco

            This method is only for compatibility with current testing
            infrastructure and should be removed.
        """
        return self._error.pos()

    @property
    def full_id(self) -> str:
        """Full error identifier."""
        return '{}:{}'.format(self.identifier, self.reason.identifier)

    @property
    def offending_node(self) -> 'ast.Node':
        """AST node where the error occurred."""
        return self._error.offendingNode()

    @property
    def readable_message(self) -> str:
        """Readable error message."""
        return self._error.readableMessage()

    @property
    def position_string(self) -> str:
        """Full error position as a string."""
        vias = self.reason.vias or self._vias or []
        vias_string = ''.join(
            ', via {0} at {1}'.format(reason, pos)
            for reason, pos in vias)
        return '{}{}'.format(self.position, vias_string)

    @property
    def message(self) -> str:
        """Human readable error message."""
        return ERRORS[self.identifier](self._node)

    def __str__(self) -> str:
        """Format error.

        Creates an appropriate error message (referring to the
        responsible Python code) for the given Viper error.
        """
        return '{0} {1} ({2})'.format(
            self.message, self.reason, self.position_string)

    def string(self, ide_mode: bool) -> str:
        if ide_mode:
            return '{0}:{1}:{2}: error: {3} {4}'.format(self.position._position.file().toString(), self.position.line, self.position.column, self.message, self.reason)
        else:
            return str(self)
