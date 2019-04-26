# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    Assert,
    ContractOnly,
    Ensures,
    Implies,
    Invariant,
    Pure,
    Requires,
    Result,
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
from typing import Tuple, Optional


class Socket:
    pass


@IOOperation
def create_server_socket_io(
        t_pre: Place,
        result: Socket = Result(),
        t_post: Place = Result()) -> bool:
    """ An operation that creates a server socket. """
    Terminates(True)


@ContractOnly
def create_server_socket(t1: Place) -> Tuple[Socket, Place]:
    IOExists2(Socket, Place)(
        lambda socket, t2: (
            Requires(
                token(t1, 1) and
                create_server_socket_io(t1, socket, t2) and
                MustTerminate(1)
            ),
            Ensures(
                token(t2) and
                Result()[1] == t2 and
                socket != None and
                Result()[0] is socket
            ),
        )
    )


@IOOperation
def accept_io(
        t_pre: Place,
        server_socket: Socket,
        result: Socket = Result(),
        t_post: Place = Result()) -> bool:
    """ An operation that listens on the server socket for incoming
    connections.
    """


@ContractOnly
def accept(t1: Place, server_socket: Socket) -> Tuple[Socket, Place]:
    IOExists2(Socket, Place)(
        lambda client_socket, t2: (
            Requires(
                token(t1, 1) and
                accept_io(t1, server_socket, client_socket, t2)
            ),
            Ensures(
                token(t2) and
                Result()[1] == t2 and
                client_socket != None and
                client_socket is Result()[0]
            ),
        )
    )


@IOOperation
def read_all_io(
        t_pre: Place,
        client_socket: Socket,
        timeout: int,
        result: str = Result(),
        t_post: Place = Result()) -> bool:
    """ An operation that tries to read all data from the client socket
    for some period of time. If succeeds, then returns read data as a
    string. Otherwise – ``None``.
    """
    Terminates(timeout > 0)



@ContractOnly
def read_all(t1: Place, socket: Socket,
             timeout: int) -> Tuple[Optional[str], Place]:
    IOExists2(str, Place)(
        lambda data, t2: (
            Requires(
                token(t1, 1) and
                read_all_io(t1, socket, timeout, data, t2) and
                Implies(timeout > 0, MustTerminate(1))
            ),
            Ensures(
                token(t2) and
                Result()[1] == t2 and
                Result()[0] is data
            ),
        )
    )


@Pure
def get_address(socket: Socket) -> int:
    Requires(socket != None)
    Ensures(True)


@IOOperation
def print_io(
        t_pre: Place,
        value: int,
        t_post: Place = Result()) -> bool:
    """ Prints a given integer to stdout. """
    Terminates(True)


@ContractOnly
def print_int(t1: Place, value: int) -> Place:
    IOExists1(Place)(
        lambda t2: (
            Requires(
                token(t1, 1) and
                print_io(t1, value, t2) and
                MustTerminate(1)
            ),
            Ensures(
                token(t2) and
                t2 == Result()
            )
        )
    )


@IOOperation
def send_io(
        t_pre: Place,
        client_socket: Socket,
        data: str,
        t_post: Place = Result()) -> bool:
    """ Sends given data to the client. """
    Terminates(True)


@ContractOnly
def send(t1: Place, socket: Socket, data: str) -> Place:
    IOExists1(Place)(
        lambda t2: (
            Requires(
                token(t1, 1) and
                send_io(t1, socket, data, t2) and
                data is not None and
                socket != None and
                MustTerminate(1)
            ),
            Ensures(
                token(t2) and
                t2 == Result()
            ),
        )
    )


@IOOperation
def close_io(
        t_pre: Place,
        client_socket: Socket,
        t_post: Place = Result()) -> bool:
    """ Closes the socket. """
    Terminates(True)


@ContractOnly
def close(t1: Place, socket: Socket) -> Place:
    IOExists1(Place)(
        lambda t2: (
            Requires(
                token(t1, 1) and
                close_io(t1, socket, t2) and
                socket != None and
                MustTerminate(1)
            ),
            Ensures(
                token(t2) and
                t2 == Result()
            ),
        )
    )


@IOOperation
def output_io(
        t_pre: Place,
        client_socket: Socket,
        data: str,
        t_post: Place = Result()) -> bool:
    Terminates(True)
    TerminationMeasure(2)
    return IOExists4(Place, Place, Place, Place)(
        lambda t1, t2, t3, t4: (
            (
                split_io(t_pre, t1, t2) and
                send_io(t1, client_socket, data, t3) and
                print_io(t2, get_address(client_socket), t4) and
                join_io(t3, t4, t_post)
                )
            if data is not None
            else no_op_io(t_pre, t_post)
        )
    )
