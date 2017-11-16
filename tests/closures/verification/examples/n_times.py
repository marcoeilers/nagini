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


f_type = Callable[[State], Optional[object]]


@Predicate
def n_inv(s: State, i: int, n_inv_token: int) -> bool:
    return (
            Acc(s.counter) and Acc(s.value) and
            s.counter == i and s.value == i * (i + 1) // 2
        if n_inv_token == 1 else
        True
    )


@CallSlot
def n_times_slot(f: f_type, n_inv_token: int) -> None:

    @UniversallyQuantified
    def uq(s: State, i: int) -> None:
        Requires(n_inv(s, i, n_inv_token))

        f(s)

        Ensures(n_inv(s, i + 1, n_inv_token))


def n_times(f: f_type, n: int, s: State, n_inv_token: int) -> None:
    Requires(0 <= n)
    Requires(n_inv(s, 0, n_inv_token))
    Requires(n_times_slot(f, n_inv_token))
    Ensures(n_inv(s, n, n_inv_token))

    i = 0
    while i < n:
        Invariant(0 <= i and i <= n)
        Invariant(n_inv(s, i, n_inv_token))

        ClosureCall(f(s), n_times_slot(f, n_inv_token)(s, i))
        i += 1

    # FIXME: this shouldn't be necessary
    # (would be impossible with proper 'parametric assertions')
    # However while i == n, theyr values as Ref types seem to be uneqal
    Unfold(n_inv(s, i, n_inv_token))
    Fold(n_inv(s, n, n_inv_token))


def sum_range(s: State) -> Optional[object]:
    Requires(Acc(s.counter) and Acc(s.value))
    Ensures(Acc(s.counter) and Acc(s.value))
    Ensures(s.counter == Old(s.counter) + 1)
    Ensures(s.value == Old(s.value + s.counter + 1))

    s.counter += 1
    s.value += s.counter

    return None


def n_times_client() -> None:

    s = State(0, 0, 0, None)

    f = sum_range

    @CallSlotProof(n_times_slot(f, 1))
    def n_times_slot(f: f_type, n_inv_token: int) -> None:

        @UniversallyQuantified
        def uq(s: State, i: int) -> None:
            Requires(n_inv(s, i, n_inv_token))
            Unfold(n_inv(s, i, n_inv_token))

            assert i == s.counter
            assert s.value == i * (i + 1) // 2
            ClosureCall(f(s), sum_range)

            assert s.counter == i + 1
            assert s.value == i * (i + 1) // 2 + i + 1
            assert s.value == i * (i + 1) // 2 + i + 1
            assert s.value == i * (i + 1) // 2 + 2 * (i + 1) // 2
            assert s.value == (i * (i + 1) + 2 * (i + 1)) // 2

            Fold(n_inv(s, i + 1, n_inv_token))
            Ensures(n_inv(s, i + 1, n_inv_token))

    Fold(n_inv(s, 0, 1))
    n_times(f, 23, s, 1)
    Unfold(n_inv(s, 23, 1))
    assert s.value == 276
    assert s.counter == 23
