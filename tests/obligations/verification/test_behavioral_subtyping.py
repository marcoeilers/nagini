# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    Predicate,
    Requires,
)
from nagini_contracts.obligations import *
from nagini_contracts.lock import Lock


class SuperLock(Lock['Super']):
    @Predicate
    def invariant(self) -> bool:
        return True


class Super:

    #:: Label(Super__do_stuff)
    def do_stuff(self) -> None:
        Requires(MustTerminate(2))

    #:: Label(Super__release)
    def release(self, lock: SuperLock) -> None:
        Requires(MustRelease(lock, 3))
        lock.release()


class SubIncreased(Super):

    #:: ExpectedOutput(leak_check.failed:caller.has_unsatisfied_obligations, Super__do_stuff)
    def do_stuff(self) -> None:
        """Measure increased. Error."""
        Requires(MustTerminate(3))

    #:: ExpectedOutput(call.precondition:insufficient.permission, Super__release)
    def release(self, lock: SuperLock) -> None:
        """Measure increased. Error."""
        Requires(MustRelease(lock, 4))
        lock.release()


class SubIncreased2(Super):

    #:: ExpectedOutput(leak_check.failed:caller.has_unsatisfied_obligations, Super__do_stuff)
    def do_stuff(self) -> None:
        """Measure increased. Error."""
        Requires(MustTerminate(3))
        Requires(MustTerminate(3))


class SubDecreased(Super):

    def do_stuff(self) -> None:
        """Measure decreased. Ok."""
        Requires(MustTerminate(1))

    def release(self, lock: SuperLock) -> None:
        """Measure decreased. Ok."""
        Requires(MustRelease(lock, 2))
        lock.release()


class SubUnchanged(Super):

    def do_stuff(self) -> None:
        """Measure the same. Ok."""
        Requires(MustTerminate(2))

    def release(self, lock: SuperLock) -> None:
        """Measure the same. Ok."""
        Requires(MustRelease(lock, 3))
        lock.release()