# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
A variation of example 1 where client handling is performed in a
separate function that in theory can be forked.
"""


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
    end_io,
    End,
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
from library import (
    accept_io,
    accept,
    close_io,
    close,
    create_server_socket_io,
    create_server_socket,
    get_address,
    output_io,
    print_io,
    print_int,
    read_all_io,
    read_all,
    send_io,
    send,
    Socket,
)


@IOOperation
def handle_client_io(
        t_pre: Place,
        client_socket: Socket) -> bool:
    Terminates(True)
    TerminationMeasure(3)
    return IOExists4(Place, Place, Place, str)(
        lambda t2, t3, t4, data: (
            read_all_io(t_pre, client_socket, 1, data, t2) and
            output_io(t2, client_socket, data, t3) and
            close_io(t3, client_socket, t4) and
            end_io(t4)
        )
    )


@IOOperation
def listener_loop_io(
        t_pre: Place,
        server_socket: Socket) -> bool:
    Terminates(False)
    return IOExists4(Place, Place, Place, Socket)(
        lambda t2, t3, t4, client_socket: (
            accept_io(t_pre, server_socket, client_socket, t2) and
            split_io(t2, t3, t4) and
            handle_client_io(t3, client_socket) and
            listener_loop_io(t4, server_socket)
        )
    )


@IOOperation
def listener_io(
        t_pre: Place) -> bool:
    Terminates(False)
    return IOExists2(Place, Socket)(
        lambda t2, server_socket: (
            create_server_socket_io(t_pre, server_socket, t2) and
            listener_loop_io(t2, server_socket)
        )
    )


def handle_client(client_socket: Socket, t1: Place) -> None:
    Requires(client_socket is not None)
    Requires(token(t1, 2) and handle_client_io(t1, client_socket))
    Requires(MustTerminate(2))

    Open(handle_client_io(t1, client_socket))

    data, t4 = read_all(t1, client_socket, timeout=1)

    Open(output_io(t4, client_socket, data))

    if data is not None:
        t5, t6 = Split(t4)

        t7 = print_int(t6, get_address(client_socket))

        t8 = send(t5, client_socket, data)

        t9 = Join(t8, t7)
    else:
        t9 = NoOp(t4)

    t10 = close(t9, client_socket)

    End(t10)


def run(t1: Place) -> None:
    Requires(token(t1, 2) and listener_io(t1))
    Ensures(False)

    Open(listener_io(t1))

    server_socket, t_loop = create_server_socket(t1)

    while True:
        Invariant(
            token(t_loop, 1) and
            listener_loop_io(t_loop, server_socket) and
            server_socket != None
        )

        Open(listener_loop_io(t_loop, server_socket))

        client_socket, t3 = accept(t_loop, server_socket)

        t4, t_loop = Split(t3)

        handle_client(client_socket, t4)
