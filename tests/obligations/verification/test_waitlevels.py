from nagini_contracts.contracts import (
    Acc,
    Assert,
    Invariant,
    Implies,
    Requires,
    Ensures,
    Result,
)
from nagini_contracts.obligations import *
from nagini_contracts.lock import Lock


# Creating locks.

def create_lock() -> None:
    l = Lock(object())
    l.acquire()
    l.release()
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(False)


#:: ExpectedOutput(carbon)(leak_check.failed:method_body.leaks_obligations)
def create_lock_unknown_order_1() -> None:
    l1 = Lock(object())
    l2 = Lock(object())
    l1.acquire()
    #:: ExpectedOutput(call.precondition:assertion.false)
    l2.acquire()


#:: ExpectedOutput(carbon)(leak_check.failed:method_body.leaks_obligations)
def create_lock_unknown_order_2() -> None:
    l1 = Lock(object())
    l2 = Lock(object())
    l2.acquire()
    #:: ExpectedOutput(call.precondition:assertion.false)
    l1.acquire()


def create_lock_above_1() -> None:
    l1 = Lock(object())
    l2 = Lock(object(), above=l1)
    l1.acquire()
    l2.acquire()
    l1.release()
    l2.release()


def create_lock_above_2() -> None:
    l1 = Lock(object())
    l2 = Lock(object(), above=l1)
    l2.acquire()
    #:: ExpectedOutput(call.precondition:assertion.false)
    l1.acquire()


def create_lock_below_1() -> None:
    l1 = Lock(object())
    l2 = Lock(object(), below=l1)
    l1.acquire()
    #:: ExpectedOutput(call.precondition:assertion.false)
    l2.acquire()


def create_lock_below_2() -> None:
    l1 = Lock(object())
    l2 = Lock(object(), below=l1)
    l2.acquire()
    l1.acquire()
    l1.release()
    l2.release()


def create_lock_below_3() -> None:
    l1 = Lock(object())
    l1.acquire()
    #:: ExpectedOutput(call.precondition:assertion.false)
    l2 = Lock(object(), below=l1)


#:: ExpectedOutput(carbon)(leak_check.failed:method_body.leaks_obligations)
def create_lock_between_1() -> None:
    l1 = Lock(object())
    l3 = Lock(object(), below=l1)
    l2 = Lock(object(), above=l3, below=l1)
    l3.acquire()
    l2.acquire()
    l1.acquire()
    l3.release()
    #:: ExpectedOutput(call.precondition:assertion.false)
    l3.acquire()


def create_lock_between_2() -> None:
    l1 = Lock(object())
    l3 = Lock(object(), below=l1)
    l2 = Lock(object(), above=l3, below=l1)
    l1.acquire()
    #:: ExpectedOutput(call.precondition:assertion.false)
    l2.acquire()
    l3.acquire()


def create_lock_between_3() -> None:
    l1 = Lock(object())
    l3 = Lock(object(), above=l1)
    #:: ExpectedOutput(call.precondition:assertion.false)
    l2 = Lock(object(), above=l3, below=l1)


# Methods.


def release(l: Lock) -> None:
    Requires(MustRelease(l, 2))
    l.release()


#:: ExpectedOutput(carbon)(leak_check.failed:method_body.leaks_obligations)
def acquire(l: Lock) -> None:
    Requires(l is not None)
    #:: ExpectedOutput(call.precondition:assertion.false)
    l.acquire()


def double_acquire(l: Lock) -> None:
    Requires(l is not None)
    Requires(WaitLevel() < Level(l))
    l.acquire()
    #:: ExpectedOutput(call.precondition:assertion.false)
    l.acquire()


def acquire_release_multiple(l: Lock) -> None:
    Requires(l is not None)
    Requires(WaitLevel() < Level(l))
    Ensures(MustRelease(l))
    l.acquire()
    l.release()
    l.acquire()
    l.release()
    l.acquire()


def acquire_release_multiple_caller_1() -> None:
    l = Lock(object())
    acquire_release_multiple(l)
    l.release()


#:: ExpectedOutput(carbon)(leak_check.failed:method_body.leaks_obligations)
def acquire_release_multiple_caller_2(l: Lock) -> None:
    Requires(l is not None)
    #:: ExpectedOutput(call.precondition:assertion.false)
    acquire_release_multiple(l)


def change_level(l: Lock) -> None:
    Requires(l is not None)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(WaitLevel() < Level(l))


# Loops.


def locks_creating_loop() -> Lock:
    Ensures(WaitLevel() < Level(Result()))
    l = Lock(object())
    i = 0
    while i < 5:
        Invariant(l is not None)
        Invariant(WaitLevel() < Level(l))
        l.acquire()
        l.release()
        l = Lock(object())
        i += 1
    return l

def locks_creating_loop_nested() -> Lock:
    Ensures(WaitLevel() < Level(Result()))
    l = Lock(object())
    i = 0
    while i < 5:
        Invariant(l is not None)
        Invariant(WaitLevel() < Level(l))
        l.acquire()
        l.release()
        j = 0
        while j < 5:
            Invariant(l is not None)
            Invariant(WaitLevel() < Level(l))
            l.acquire()
            l.release()
            l = Lock(object())
            j += 1
        i += 1
    return l
