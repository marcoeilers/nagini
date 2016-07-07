import ast

from py2viper_translation.lib.error_messages import ERRORS, REASONS
from typing import Optional


cache = {}


def error_msg(error: 'silver.verifier.AbstractError') -> str:
    """
    Creates an appropriate error message (referring to the responsible Python
    code) for the given Viper error.
    """
    pos_string = str(error.pos())
    got_proper_position = False
    error_id = error.fullId().split(':')
    reason_ = error.reason()
    reason_offending = error.reason().offendingNode()
    reason_pos = error.reason().offendingNode().pos()
    reason_string = None
    if hasattr(reason_pos, 'id'):
        reason_pos = reason_pos.id()
        reason_entry = cache[reason_pos]
        reason_node = reason_entry[0]
        reason_string = reason_entry[2]
        if reason_entry[1]:
            got_proper_position = True
        pos_string += ''.join(', via {0} at {1}'.format(reason, pos)
                              for reason, pos in reason_entry[1])
    else:
        reason_node = None
    reason = reason_string if reason_string else reason_node
    if not reason:
        reason = str(reason_offending)
    reason_msg = REASONS[error_id[1]](reason)
    error_pos = error.pos()
    if hasattr(error_pos, 'id'):
        error_pos = error_pos.id()
        error_entry = cache[error_pos]
        error_node = error_entry[0]
        if not got_proper_position:
            pos_string += ''.join(', via {0} at {1}'.format(reason, pos)
                                  for reason, pos in error_entry[1])
    else:
        off = error.offendingNode()
        off_pos = off.pos()
        error_node = None
    error_msg = ERRORS[error_id[0]](error_node)
    return '{0} {1} ({2})'.format(error_msg, reason_msg, pos_string)
