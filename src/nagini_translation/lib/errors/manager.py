"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Error handling state is stored in singleton ``manager``."""


from collections import namedtuple
from uuid import uuid1

from typing import Any, List, Optional

from nagini_translation.lib.errors.wrappers import Error
from nagini_translation.lib.errors.rules import Rules
from nagini_translation.lib.jvmaccess import JVM
from nagini_translation.lib.program_nodes import PythonMethod, PythonNode
from nagini_translation.models.extractor import Extractor


Item = namedtuple('Item', 'node vias reason_string py_node')


class ErrorManager:
    """A singleton object that stores the state needed for error handling."""

    def __init__(self) -> None:
        self._items = {}                # type: Dict[str, Item]
        self._conversion_rules = {}     # type: Dict[str, Rules]

    def add_error_information(
            self, node: 'ast.Node', vias: List[Any], reason_string: str, py_node: PythonNode,
            conversion_rules: Rules = None) -> str:
        """Add error information to state."""
        item_id = str(uuid1())
        assert item_id not in self._items
        self._items[item_id] = Item(node, vias, reason_string, py_node)
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
            jvm: JVM,
            modules, sif) -> List[Error]:
        """Convert Viper errors into Nagini errors.

        It does that by wrapping in ``Error`` subclasses.
        """
        new_errors = [
            self._convert_error(error, jvm, modules, sif)
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

    def _try_get_rules_workaround(
            self, node: 'ast.Node', jvm: Optional[JVM]) -> Optional[Rules]:
        """Try to extract rules out of ``node``.

        Due to optimizations, Silicon sometimes returns not the correct
        offending node, but an And that contains it. This method tries
        to work around this problem.

        .. todo::

            In the long term we should discuss with Malte how to solve
            this problem properly.
        """
        rules = self._get_conversion_rules(node.pos())
        if rules or not jvm:
            return rules
        if (isinstance(node, jvm.viper.silver.ast.And) or
                isinstance(node, jvm.viper.silver.ast.Implies)):
            return (self._get_conversion_rules(node.left().pos()) or
                    self._get_conversion_rules(node.right().pos()) or
                    self._try_get_rules_workaround(node.left(), jvm) or
                    self._try_get_rules_workaround(node.right(), jvm))
        return

    def transformError(self, error: 'AbstractVerificationError') -> 'AbstractVerificationError':
        """ Transform silver error to a fixpoint. """
        old_error = None
        while old_error != error:
            old_error = error
            error = error.transformedError()
        return error

    def _convert_error(
            self, original_error: 'AbstractVerificationError',
            jvm: JVM, modules, sif) -> Error:
        error = self.transformError(original_error)
        reason_pos = error.reason().offendingNode().pos()
        reason_item = self._get_item(reason_pos)
        position = error.pos()
        rules = self._try_get_rules_workaround(
            error.offendingNode(), jvm)
        if rules is None:
            rules = self._try_get_rules_workaround(
                error.reason().offendingNode(), jvm)
        if rules is None:
            rules = {}
        error_item = self._get_item(position)

        if error_item is not None and original_error.counterexample().isDefined() and isinstance(error_item.py_node, PythonMethod):
            pymethod = error_item.py_node
            ce = original_error.counterexample().get()
            if sif:
                ce = getattr(jvm.viper.silicon.sif, 'CounterexampleSIFTransformerO').transformCounterexample(ce, pymethod.sil_name)
            inputs = Extractor().extract_counterexample(jvm, pymethod, ce, modules)
        else:
            inputs = None

        if error_item:
            return Error(error, rules, reason_item, error_item.node,
                         error_item.vias, inputs=inputs)
        else:
            return Error(error, rules, reason_item, inputs=inputs)




manager = ErrorManager()     # pylint: disable=invalid-name
