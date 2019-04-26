# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.lock import Lock
from nagini_contracts.contracts import *
from nagini_contracts.obligations import Level, WaitLevel, MustTerminate
from nagini_contracts.thread import Thread


class Cell:
    def __init__(self, val: int) -> None:
        self.value = val
        self.rds = 0
        Ensures(Acc(self.value) and self.value == val)
        Ensures(Acc(self.rds) and self.rds == 0)


class CellLock(Lock[Cell]):

    @Predicate
    def invariant(self) -> bool:
        return Acc(self.get_locked().rds) and self.get_locked().rds >= 0 and \
               Acc(self.get_locked().value, 1 - self.get_locked().rds * ARP())


class Writer:
    def write(self, data: Cell) -> None:
        Requires(Acc(data.value))
        Requires(MustTerminate(2))
        Ensures(Acc(data.value))


class Reader:
    def read(self, data: Cell) -> None:
        Requires(Rd(data.value))
        Requires(MustTerminate(2))
        Ensures(Rd(data.value))


class RWController:
    def __init__(self, c: Cell) -> None:
        Requires(Acc(c.rds) and Acc(c.value) and c.rds == 0)
        Ensures(Acc(self.c) and self.c == c and Acc(self.lock) and self.lock.get_locked() is self.c)
        Ensures(WaitLevel() < Level(self.lock))
        self.c = c  # type: Cell
        self.lock = CellLock(self.c)  # type: CellLock

    def do_write(self, writer: Writer) -> None:
        Requires(writer is not None)
        Requires(Rd(self.lock) and Rd(self.c) and self.lock.get_locked() is self.c)
        Requires(WaitLevel() < Level(self.lock))
        Ensures(Rd(self.lock) and Rd(self.c))
        self.lock.acquire()
        if self.c.rds != 0:
            #:: UnexpectedOutput(silicon)(lock.invariant.not.established:assertion.false, 320)
            self.lock.release()
            self.do_write(writer)  # try again
        else:
            writer.write(self.c)   # lock acquired successfully
            self.lock.release()

    def do_read(self, reader: Reader) -> None:
        Requires(reader is not None)
        Requires(Rd(self.lock) and Rd(self.c) and self.lock.get_locked() is self.c)
        Requires(WaitLevel() < Level(self.lock))
        Ensures(Rd(self.lock) and Rd(self.c))
        self.lock.acquire()
        self.c.rds += 1
        #:: UnexpectedOutput(silicon)(lock.invariant.not.established:assertion.false, 320)
        self.lock.release()
        reader.read(self.c)
        self.lock.acquire()
        self.c.rds -= 1
        self.lock.release()
