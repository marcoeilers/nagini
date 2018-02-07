from nagini_contracts.lock import Lock
from nagini_contracts.contracts import *
from nagini_contracts.obligations import Level, WaitLevel, MustTerminate
from nagini_contracts.thread import Thread, getARP


class Cell:
    def __init__(self, val: int) -> None:
        self.value = val
        Ensures(Acc(self.value) and self.value == val)


class TreeTask:

    def __init__(self, c: Cell) -> None:
        self.data = c
        self.result = 0
        Ensures(Acc(self.data) and self.data == c)
        Ensures(Acc(self.result) and self.result == 0)

    def run(self) -> None:
        Requires(Rd(self.data) and Rd(self.data.value) and Acc(self.result))
        Ensures(Rd(self.data) and Rd(self.data.value) and Acc(self.result))
        subs = Sequence()  # type: Sequence[Thread]
        tasks = Sequence()  # type: Sequence[TreeTask]

        i = 0
        while i < 10:
            #:: ExpectedOutput(not.supported)
            Invariant(Acc(self.data, 1 - sum(getARP(t) for t in subs)))
            tt = TreeTask(self.data)
            t = Thread(None, tt.run, args=())
            t.start(tt.run)
            subs = subs + Sequence(t)
            tasks = tasks + Sequence(tt)

        while len(subs) > 0:
            Invariant(Acc(self.data, 1 - sum(getARP(t) for t in subs)))
            t = subs[0]
            tt = tasks[0]
            subs = subs.drop(1)
            tasks = tasks.drop(1)
            t.join(tt.run)
            self.result += tt.result
