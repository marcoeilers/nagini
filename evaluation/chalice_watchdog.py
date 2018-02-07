"""
This test is a ported version of
``obligations/largerExamples/watchdog.chalice`` test from Chalice2Silver
test suite.
"""


from nagini_contracts.contracts import (
    Acc,
    Assert,
    Ensures,
    Fold,
    Implies,
    Invariant,
    Predicate,
    Requires,
    Unfold
)
from nagini_contracts.obligations import *
from nagini_contracts.lock import Lock
from nagini_contracts.thread import Thread


class Data:
    def __init__(self) -> None:
        self.d = 0
        self.lock = DataLock(self)
        Ensures(Acc(self.lock) and
                WaitLevel() < Level(self.lock) and
                self.lock.get_locked() is self)


class DataLock(Lock[Data]):
    @Predicate
    def invariant(self) -> bool:
        return Acc(self.get_locked().d)


class WatchDog:

    def __init__(self) -> None:
        self.running = False
        Ensures(Acc(self.running))

    def delay(self, t: int) -> None:
        Requires(MustTerminate(t))

    def watch(self, d: Data) -> None:
        Requires(Acc(self.running))
        Requires(Acc(d.lock, 1/2))
        Requires(WaitLevel() < Level(d.lock))
        self.running = True     # TODO: self.running should be in Lock
                                # invariant.
        d.lock.acquire()
        while (self.running):
            Invariant(Acc(self.running))
            Invariant(Acc(d.lock, 1/2))
            Invariant(MustRelease(d.lock, 1))
            Invariant(WaitLevel() < Level(d.lock))
            Invariant(d.lock.invariant())
            # TODO: Check some property here.
            d.lock.release()
            self.delay(5)
            d.lock.acquire()
        d.lock.release()


def main() -> None:
    data = Data()
    w = WatchDog()
    wthread = Thread(None, w.watch, None, (data,))
    wthread.start(w.watch)
    data.lock.acquire()
    Unfold(data.lock.invariant())
    data.d = 0
    while True:
        Invariant(Acc(data.lock, 1/4))
        Invariant(data.lock.get_locked() is data)
        Invariant(WaitLevel() < Level(data.lock))
        Invariant(MustRelease(data.lock, 1))
        Invariant(Acc(data.d))
        data.d = data.d + 1
        Fold(data.lock.invariant())
        data.lock.release()
        data.lock.acquire()
        Unfold(data.lock.invariant())



"""

+class Data {
+    var d : int
+}
+
+class Watchdog {
+
+    var running : bool
+
+    //wait some amount of time
+    method delay(t:int) requires mustTerminate(t) { }
+
+    method watch(d : Data)
+        requires d != null
+        requires acc(running)
+    {
+        running := true
+        acquire d
+        while (running)
+            invariant mustRelease(d, 1)
+            invariant acc(running)
+        {
+            //check property here
+            release d
+            call delay(5)
+            acquire d
+        }
+
+        release d
+    }
+}
+
+class Main {
+
+    method main() {
+
+        var data : Data := new Data
+        data.d := 0
+
+        var w : Watchdog := new Watchdog
+
+        fork w.watch(data)
+
+        acquire data
+        while (true)
+            invariant mustRelease(data, 1)
+            invariant acc(data.d)
+        {
+            data.d := data.d + 1
+            release data
+            acquire data
+        }
+    }
+}
"""