"""Error handling state is stored in singleton ``manager``."""


from collections import namedtuple
from uuid import uuid1

from typing import Any, List, Optional

from py2viper_translation.lib.errors.wrappers import Error
from py2viper_translation.lib.errors.rules import Rules
from py2viper_translation.lib.jvmaccess import JVM


Item = namedtuple('Item', 'node vias reason_string')


class ErrorManager:
    """A singleton object that stores the state needed for error handling."""

    def __init__(self) -> None:
        self._items = {}                # type: Dict[str, Item]
        self._conversion_rules = {}     # type: Dict[str, Rules]

    def add_error_information(
            self, node: 'ast.Node', vias: List[Any], reason_string: str,
            conversion_rules: Rules = None) -> str:
        """Add error information to state."""
        item_id = str(uuid1())
        assert item_id not in self._items
        self._items[item_id] = Item(node, vias, reason_string)
        if conversion_rules is not None:
            self._conversion_rules[item_id] = conversion_rules
        return item_id

    def clear(self) -> None:
        """Clear all state."""
        self._items.clear()
        self._conversion_rules.clear()

    def convert(
            self,
            errors: List['AbstractVerificationError'],
            jvm: Optional[JVM]) -> List[Error]:
        """Convert Viper errors into py2viper errors.

        It does that by wrapping in ``Error`` subclasses.
        """
        new_errors = [
            self._convert_error(error, jvm)
            for error in errors
        ]
        return new_errors

    def get_vias(self, node_id: str) -> List[Any]:
        """Get via information for the given ``node_id``."""
        item = self._items[node_id]
        return item.vias

    def _get_item(self, pos: 'ast.AbstractSourcePosition') -> Optional[Item]:
        if hasattr(pos, 'id'):
            node_id = pos.id()
            return self._items[node_id]
        return None

    def _get_conversion_rules(
            self, position: 'ast.AbstractSourcePosition') -> Optional[Rules]:
        if hasattr(position, 'id'):
            node_id = position.id()
            if node_id in self._conversion_rules:
                return self._conversion_rules[node_id]
        return None

    def _convert_error(
            self, error: 'AbstractVerificationError',
            jvm: Optional[JVM]) -> Error:
        reason_pos = error.reason().offendingNode().pos()
        reason_item = self._get_item(reason_pos)
        position = error.pos()
        rules = self._get_conversion_rules(position)
        if rules is None and jvm:
            # TODO: Due to optimizations, Silicon sometimes returns not
            # the correct offending node, but an And that contains it.
            # This is an attempt to work around this problem.
            # In the long term we should discuss with Malte how to solve
            # this problem properly.
            node = error.offendingNode()
            if isinstance(node, jvm.viper.silver.ast.And):
                rules = (self._get_conversion_rules(node.left().pos()) or
                         self._get_conversion_rules(node.right().pos()))
        if rules is None:
            rules = self._get_conversion_rules(reason_pos) or {}
        error_item = self._get_item(position)
        if error_item:
            return Error(error, rules, reason_item, error_item.node,
                         error_item.vias)
        else:
            return Error(error, rules, reason_item)


manager = ErrorManager()     # pylint: disable=invalid-name
