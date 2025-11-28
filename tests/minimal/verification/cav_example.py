# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate
from typing import List, Tuple


class SoldoutException(Exception):
    pass

@ContractOnly
def get_seats(id: int, num: int) -> List[Tuple[int ,int]]:
    Requires(num > 0)
    Requires(MustTerminate(1))
    Ensures(list_pred(Result()))
    Ensures(len(Result()) == num)
    Exsures(SoldoutException, True)


class Ticket:
    def __init__(self, show: int, row: int, seat: int) -> None:
        Requires(MustTerminate(1))
        self.show_id = show
        self.row, self.seat = row, seat
        Fold(self.state())
        Ensures(self.state() and MayCreate(self, 'discount_code'))

    def set_discount(self, code: str) -> None:
        Requires(MayCreate(self, 'discount_code'))
        self.discount_code = code

    @Predicate
    def state(self) -> bool:
        return Acc(self.show_id) and Acc(self.row) and Acc(self.seat)


def order_tickets(num: int, show_id: int, code: str = None) -> List[Ticket]:
    Requires(num > 0)
    Requires(MustTerminate(2))
    Exsures(SoldoutException, True)
    seats = get_seats(show_id, num)
    res = []  # type: List[Ticket]
    for row, seat in seats:
        Invariant(list_pred(res) and len(res) == len(Previous(row)))
        Invariant(Forall(res, lambda t: t.state() and
                         Implies(code is not None, Acc(t.discount_code))))
        Invariant(MustTerminate(len(seats) - len(res)))
        ticket = Ticket(show_id, row, seat)
        if code is not None:
            ticket.discount_code = code
        res.append(ticket)
    return res