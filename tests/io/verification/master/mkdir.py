# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    Acc,
    Assert,
    ContractOnly,
    Ensures,
    Exsures,
    Implies,
    Requires,
    Result,
    RaisedException,
)
from nagini_contracts.io_contracts import *
from nagini_contracts.io_builtins import (
    no_op_io,
    NoOp,
    split_io,
    Split,
    join_io,
    Join,
)
from nagini_contracts.obligations import (
    MustTerminate,
)
from typing import Tuple


class OSErrorWrapper(Exception):

    def __init__(self, exception: Exception, place: Place) -> None:
        Ensures(Acc(self.exception) and self.exception is exception)
        Ensures(Acc(self.place) and self.place is place)
        #super().__init__() TODO
        self.exception = exception      # type: Exception
        self.place = place              # type: Place


@IOOperation
def mkdir_io(
        t_pre: Place,
        path: str,
        exception: OSErrorWrapper = Result(),
        t_post: Place = Result()) -> bool:
    Terminates(True)


@ContractOnly
def mkdir(t1: Place, path: str) -> Place:
    IOExists2(Place, OSErrorWrapper)(
        lambda t2, ex: (
            Requires(
                path is not None and
                token(t1, 1) and
                mkdir_io(t1, path, ex, t2) and
                MustTerminate(1)
            ),
            Ensures(
                token(t2) and
                t2 == Result() and
                ex is None
            ),
            Exsures(OSErrorWrapper,
                ex is RaisedException() and
                Acc(ex.place) and ex.place == t2 and token(t2) and
                Acc(ex.exception) and isinstance(ex.exception, Exception)
            ),
        )
    )


@IOOperation
def is_dir_io(
        t_pre: Place,
        path: str,
        exception: OSErrorWrapper = Result(),
        result: bool = Result(),
        t_post: Place = Result()) -> bool:
    Terminates(True)


@ContractOnly
def is_dir(t1: Place, path: str) -> Tuple[bool, Place]:
    IOExists3(Place, OSErrorWrapper, bool)(
            lambda t2, ex, success: (
                Requires(
                    path is not None and
                    token(t1, 1) and
                    is_dir_io(t1, path, ex, success, t2) and
                    MustTerminate(1)
                ),
                Ensures(
                    token(t2) and
                    t2 == Result()[1] and
                    ex is None and
                    success == Result()[0]
                ),
                Exsures(OSErrorWrapper,
                    ex is RaisedException() and
                    Acc(ex.place) and ex.place == t2 and token(t2) and
                    Acc(ex.exception) and isinstance(ex.exception, Exception)
                ),
            )
    )


@IOOperation
def ensure_dir_exists_io(
        t_pre: Place,
        path: str,
        result: bool = Result(),
        t_post: Place = Result()) -> bool:
    """Ensure that directory exists IO.

    Should force the implementation to handle exceptions because the
    methods that throw exceptions should not be able to set the
    ``result``.
    """
    Terminates(True)
    TerminationMeasure(2)
    return IOExists4(OSErrorWrapper, OSErrorWrapper, Place, bool)(
        lambda ex1, ex2, t2, is_dir_res: (
            mkdir_io(t_pre, path, ex1, t2) and
            (
                (
                    no_op_io(t2, t_post) and
                    result == True
                )
                if ex1 is None
                else (
                    is_dir_io(t2, path, ex2, is_dir_res, t_post) and
                    Implies(ex2 is None, result == is_dir_res) and
                    Implies(ex2 is not None, result == False)
                )
            )
        )
    )


def ensure_dir_exists(t1: Place, path: str) -> Tuple[bool, Place]:
    IOExists2(Place, bool)(
        lambda t2, success: (
            Requires(
                path is not None and
                token(t1, 2) and
                ensure_dir_exists_io(t1, path, success, t2) and
                MustTerminate(2)
            ),
            Ensures(
                token(t2) and t2 == Result()[1] and
                Result()[0] == success
            ),
        )
    )

    Open(ensure_dir_exists_io(t1, path))

    try:

        t3 = mkdir(t1, path)

        t2 = NoOp(t3)

        return True, t2

    except OSErrorWrapper as ex1:

        try:

            res, t2 = is_dir(ex1.place, path)

            return res, t2

        except OSErrorWrapper as ex2:

            return False, ex2.place


@IOOperation
def ensure_dir_exists_io2(
        t_pre: Place,
        path: str,
        exception: OSErrorWrapper = Result(),
        t_post: Place = Result()) -> bool:
    """Ensure that directory exists IO.

    This IO allows the implementation to propagate exceptions. However,
    it strictly specifies which exceptions can be propagated (in this
    case only ``ex1``).
    """
    Terminates(True)
    TerminationMeasure(2)
    return IOExists4(OSErrorWrapper, OSErrorWrapper, Place, bool)(
        lambda ex1, ex2, t2, is_dir_res: (
            mkdir_io(t_pre, path, ex1, t2) and
            (
                (
                    no_op_io(t2, t_post) and
                    exception is None
                )
                if ex1 is None
                else (
                    is_dir_io(t2, path, ex2, is_dir_res, t_post) and
                    (
                        (
                            Implies(is_dir_res, exception is None) and
                            Implies(not is_dir_res, exception is ex1)
                        )
                        if ex2 is None
                        else (
                            exception == ex1
                        )
                    )
                )
            )
        )
    )


# TODO: When issue #55 is fixed and this one passes, encode failing
# variations.
def ensure_dir_exists2(t1: Place, path: str) -> Place:
    IOExists2(Place, OSErrorWrapper)(
        lambda t2, ex: (
            Requires(
                path is not None and
                token(t1, 2) and
                ensure_dir_exists_io2(t1, path, ex, t2) and
                MustTerminate(2)
            ),
            Ensures(
                token(t2) and t2 == Result() and ex is None
            ),
            Exsures(OSErrorWrapper,
                #:: UnexpectedOutput(postcondition.violated:assertion.false, 55) | UnexpectedOutput(carbon)(postcondition.violated:assertion.false, 168)
                ex is RaisedException() and
                Acc(ex.place) and ex.place == t2 and token(t2) and
                Acc(ex.exception) and isinstance(ex.exception, Exception)
            ),
        )
    )

    Open(ensure_dir_exists_io2(t1, path))

    res = True

    try:

        t3 = mkdir(t1, path)

        t2 = NoOp(t3)

        return t2

    except OSErrorWrapper as ex1:

        try:

            res, t2 = is_dir(ex1.place, path)

        except OSErrorWrapper as ex2:

            raise ex1

        else:

            if not res:

                raise ex1

            else:

                return t2
