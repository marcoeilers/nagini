"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Base classes for all other nodes."""

# pragma pylint: disable=abstract-method


import abc

from nagini_translation.lib.typedefs import Info
from nagini_translation.lib.typedefs import Node as NodeType
from nagini_translation.lib.typedefs import Position


class Node(abc.ABC):
    """A base class for all nodes."""

    @abc.abstractmethod
    def translate(self, translator: 'AbstractTranslator', ctx: 'Context',
                  position: Position, info: Info) -> NodeType:
        """Translate to Silver."""


class Statement(Node):
    """A base class for all statements."""


class Expression(Node):
    """A base class for all expressions."""

    @abc.abstractmethod
    def __eq__(self, other: 'Expression') -> 'Expression':
        """Check equality."""

    @abc.abstractmethod
    def __ne__(self, other: 'Expression') -> 'Expression':
        """Check inequality."""


__all__ = (
    'Node',
    'Statement',
    'Expression',
)
