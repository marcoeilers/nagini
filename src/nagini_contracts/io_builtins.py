"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Built-in IO operations."""

# pragma pylint: disable=invalid-name,unused-argument


from typing import Callable, Tuple, TypeVar

from nagini_contracts.contracts import (
    ContractOnly,
    Ensures,
    Ghost,
    Result,
    Requires,
)
from nagini_contracts.io_contracts import (
    ctoken,
    IOExists1,
    IOExists2,
    IOExists3,
    IOOperation,
    Place,
    Terminates,
    token,
)
from nagini_contracts.obligations import (
    MustTerminate,
)


@IOOperation
def no_op_io(
        t_pre: Place,
        t_post: Place = Result()) -> bool:
    """No op IO operation."""
    Terminates(True)


@Ghost
@ContractOnly
def NoOp(t_pre: Place) -> Place:
    """Perform ``no_op_io``."""
    IOExists1(Place)(
        lambda t_post: (
            Requires(
                token(t_pre, 1) and
                no_op_io(t_pre, t_post) and
                MustTerminate(1)
            ),
            Ensures(
                token(t_post) and
                t_post == Result()
            ),
        )
    )


@IOOperation
def split_io(
        t_pre: Place,
        t_post1: Place = Result(),
        t_post2: Place = Result()) -> bool:
    """Split one place into two places."""
    Terminates(True)


@Ghost
@ContractOnly
def Split(t_pre: Place) -> Tuple[Place, Place]:
    """Perform ``split_io``."""
    IOExists2(Place, Place)(
        lambda t_post1, t_post2: (
            Requires(
                token(t_pre, 1) and
                split_io(t_pre, t_post1, t_post2) and
                MustTerminate(1)
            ),
            Ensures(
                token(t_post1) and
                t_post1 == Result()[0] and
                token(t_post2) and
                t_post2 == Result()[1]
            ),
        )
    )


@IOOperation
def join_io(
        t_pre1: Place,
        t_pre2: Place,
        t_post: Place = Result()) -> bool:
    """Join to input places into one output place."""
    Terminates(True)


@Ghost
@ContractOnly
def Join(t_pre1: Place, t_pre2: Place) -> Place:
    """Perform ``join_io``."""
    IOExists1(Place)(
        lambda t_post: (
            Requires(
                token(t_pre1, 1) and
                token(t_pre2, 1) and
                join_io(t_pre1, t_pre2, t_post) and
                MustTerminate(1)
            ),
            Ensures(
                token(t_post) and
                t_post == Result()
            ),
        )
    )


@IOOperation
def gap_io(
        t_pre: Place,
        t_post: Place = Result()) -> bool:
    """Convert ``token`` to ``ctoken``."""
    Terminates(True)


@Ghost
@ContractOnly
def Gap(t_pre: Place) -> Place:
    """Perform ``gap_io``."""
    IOExists1(Place)(
        lambda t_post: (
            Requires(
                token(t_pre, 1) and
                gap_io(t_pre, t_post) and
                MustTerminate(1)
            ),
            Ensures(
                ctoken(t_post) and
                t_post == Result()
            ),
        )
    )


@IOOperation
def end_io(t_pre: Place) -> bool:
    """Terminate Petri Net."""
    Terminates(True)


@Ghost
@ContractOnly
def End(t_pre: Place) -> Place:
    """Perform ``end_io``."""
    Requires(
        token(t_pre, 1) and
        end_io(t_pre) and
        MustTerminate(1)
    )


@IOOperation
def set_var_io(
        t_pre: Place,
        value: int,
        result: int = Result(),
        t_post: Place = Result()) -> bool:
    """Set variable given at ``result`` position to provided ``value``."""
    Terminates(True)


@Ghost
@ContractOnly
def SetVar(t_pre: Place, value: int) -> Tuple[int, Place]:
    """Perform ``set_var_io``.

    .. note::

        Mypy does not allow generics as function arguments. Therefore,
        we have to use a concrete type for ``value``.
    """
    IOExists2(Place, int)(
        lambda t_post, result: (
            Requires(
                token(t_pre, 1) and
                set_var_io(t_pre, value, result, t_post) and
                MustTerminate(1)
            ),
            Ensures(
                token(t_post) and
                t_post == Result()[1] and
                result == Result()[0] and
                value == result
            ),
        )
    )


T = TypeVar('T')
V = TypeVar('V')


@IOOperation
def eval_io(
        t_pre: Place,
        func: Callable[[T], V],
        arg: T,
        result: object = Result(),
        t_post: Place = Result()) -> bool:
    """Evaluate func in the current state."""
    Terminates(True)


@Ghost
@ContractOnly
def Eval(t_pre: Place, func: Callable[[T], V], arg: T) -> Tuple[V, Place]:
    IOExists2(Place, object)(
        lambda t_post, result: (
            Requires(
                token(t_pre, 1) and
                eval_io(t_pre, func, arg, result, t_post) and
                MustTerminate(1)
            ),
            Ensures(
                token(t_post) and
                t_post is Result()[1] and
                result is Result()[0]
                # and resul result == func(arg)
                # This is part of the contract but guaranteed via additional inhales after
                # any call to Eval, and cannot be part of the contract written here
                # because the fact that func can have an arbitrary precondition would make
                # the contract of Eval not well-formed.
            ),
        )
    )