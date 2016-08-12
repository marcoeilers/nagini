"""Base classes for all other nodes."""

# pragma pylint: disable=abstract-method


import abc

from py2viper_translation.lib.typedefs import Info
from py2viper_translation.lib.typedefs import Node as NodeType
from py2viper_translation.lib.typedefs import Position


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
    def __eq__(self, other) -> 'Expression':
        """Check equality."""

    @abc.abstractmethod
    def __ne__(self, other) -> 'Expression':
        """Check inequality."""


__all__ = (
    'Node',
    'Statement',
    'Expression',
)
