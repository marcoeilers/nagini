from typing import Callable, Optional
from nagini_contracts.contracts import (
    Implies,
    Requires,
    Ensures,
    Result,
    Old,
    Invariant,
    Predicate,
    Fold,
    Unfold,
    Unfolding,
    Pure,
    Acc,
    CallSlot,
    CallSlotProof,
    UniversallyQuantified,
    ClosureCall,
    Assert,
)


class State:

    def __init__(
        self,
        counter: int,
        value: int,
        offset: int,
        next: Optional['State']
    ) -> None:

        self.counter = counter
        self.value = value
        self.offset = offset
        self.next = next
        Ensures(Acc(self.counter) and Acc(self.value))
        Ensures(Acc(self.offset) and Acc(self.next))
        Ensures(self.counter == counter and self.value == value)
        Ensures(self.offset == offset and self.next == next)


cond_t = Callable[[State], bool]
body_t = Callable[[State], Optional[object]]


@Predicate
def inv(s: State, inv_token: int) -> bool:
    return (
        (
            Acc(s.counter) and Acc(s.value, 1 / 2) and
            s.counter <= s.value
        ) if inv_token == 1 else
        True
    )


@Pure
def cond_expr(s: State, inv_token: int) -> bool:
    Requires(inv(s, inv_token))
    return Unfolding(
        inv(s, inv_token),
        s.counter < s.value if inv_token == 1 else
        True
    )


@Pure
@CallSlot
def cond_slot(
    cond: cond_t,
    inv_token: int
) -> None:

    @UniversallyQuantified
    def uq(s: State) -> None:
        Requires(inv(s, inv_token))

        b = cond(s)

        Ensures(b == cond_expr(s, inv_token))


@CallSlot
def body_slot(body: body_t, inv_token: int) -> None:

    @UniversallyQuantified
    def uq(s: State) -> None:
        Requires(inv(s, inv_token))
        Requires(cond_expr(s, inv_token))

        body(s)

        Ensures(inv(s, inv_token))


def while_loop(
    cond: cond_t,
    body: body_t,
    s: State,
    inv_token: int
) -> None:

    Requires(inv(s, inv_token))
    Requires(cond_slot(cond, inv_token))
    Requires(body_slot(body, inv_token))

    Ensures(inv(s, inv_token))
    Ensures(not cond_expr(s, inv_token))

    b = ClosureCall(
        cond(s),
        cond_slot(cond, inv_token)(s)
    )  # type: bool

    assert b == cond_expr(s, inv_token)

    while b:
        Invariant(inv(s, inv_token))
        Invariant(b == cond_expr(s, inv_token))

        ClosureCall(
            body(s),
            body_slot(body, inv_token)(s)
        )

        b = ClosureCall(
            cond(s),
            cond_slot(cond, inv_token)(s)
        )


@Pure
def count_to_cond(s: State) -> bool:
    Requires(Acc(s.counter) and Acc(s.value))
    Ensures(Result() == (s.counter < s.value))
    return s.counter < s.value


def count_to_body(s: State) -> Optional[object]:
    Requires(Acc(s.counter) and Acc(s.value, 1 / 2))
    Requires(s.counter < s.value)

    Ensures(Acc(s.counter) and Acc(s.value, 1 / 2))
    Ensures(s.counter <= s.value)
    Ensures(s.counter == Old(s.counter) + 1)

    s.counter += 1
    return None


def while_loop_client() -> None:

    cond_f = count_to_cond
    body_f = count_to_body

    s = State(0, 20, 0, None)

    @CallSlotProof(cond_slot(cond_f, 1))
    def cond_slot(
        cond: cond_t,
        inv_token: int
    ) -> None:

        @UniversallyQuantified
        def uq(s: State) -> None:
            Requires(inv(s, inv_token))

            Unfold(inv(s, inv_token))
            b = ClosureCall(cond(s), count_to_cond)  # type: bool
            Fold(inv(s, inv_token))

            Ensures(b == cond_expr(s, inv_token))

    @CallSlotProof(body_slot(body_f, 1))
    def body_slot(body: body_t, inv_token: int) -> None:

        @UniversallyQuantified
        def uq(s: State) -> None:
            Requires(inv(s, inv_token))
            Requires(Unfolding(inv(s, inv_token), cond_expr(s, inv_token)))

            Unfold(inv(s, inv_token))
            ClosureCall(body(s), count_to_body)
            Fold(inv(s, inv_token))

            Ensures(inv(s, inv_token))

    Fold(inv(s, 1))
    while_loop(cond_f, body_f, s, 1)
    Unfold(inv(s, 1))

    assert s.counter == 20 and s.value == 20
