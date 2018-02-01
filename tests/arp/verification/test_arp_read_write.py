from nagini_contracts.lock import Lock
from nagini_contracts.contracts import *
from nagini_contracts.obligations import Level, WaitLevel
from nagini_contracts.thread import Thread


class Cell:
    def __init__(self, val: int) -> None:
        self.value = val
        Ensures(Acc(self.value) and self.value == val)


class CellLock(Lock[Cell]):

    def __init__(self, locked_object: Cell) -> None:
        super().__init__(locked_object)
        self.rds = 0
        Ensures(Acc(self.rds) and self.rds == 0)

    @Predicate
    def invariant(self) -> bool:
        return Acc(self.rds) and self.rds >= 0 and \
               Acc(self.get_locked().value, 1 - self.rds * ARP())


class Writer:
    def write(self, data: Cell) -> None:
        Requires(Acc(data.value))
        Ensures(Acc(data.value))


class Reader:
    def read(self, data: Cell) -> None:
        Requires(Rd(data.value))
        Ensures(Rd(data.value))


class RWController:
    def __init__(self, c: Cell) -> None:
        self.c = c
        self.lock = CellLock(self.c)
        Ensures(Acc(self.c) and self.c == c and Acc(self.lock) and self.lock.get_locked() is self.c)
        Ensures(WaitLevel() < Level(self.lock))

    def do_write(self, writer: Writer) -> None:
        Requires(writer is not None)
        Requires(Rd(self.lock) and Rd(self.c) and self.lock.get_locked() is self.c)
        Requires(WaitLevel() < Level(self.lock))
        Ensures(Rd(self.lock) and Rd(self.c))
        self.lock.acquire()
        Unfold(self.lock.invariant())
        if self.lock.rds != 0:
            Fold(self.lock.invariant())
            self.lock.release()
            self.do_write(writer)
        else:
            writer.write(self.c)
            Fold(self.lock.invariant())
            self.lock.release()

    def do_read(self, reader: Reader) -> None:
        Requires(reader is not None)
        Requires(Rd(self.lock) and Rd(self.c) and self.lock.get_locked() is self.c)
        Requires(WaitLevel() < Level(self.lock))
        Ensures(Rd(self.lock) and Rd(self.c))
        self.lock.acquire()
        Unfold(self.lock.invariant())
        self.lock.rds += 1
        Fold(self.lock.invariant())
        self.lock.release()
        reader.read(self.c)
        self.lock.acquire()
        Unfold(self.lock.invariant())
        self.lock.rds -= 1
        Fold(self.lock.invariant())
        self.lock.release()
