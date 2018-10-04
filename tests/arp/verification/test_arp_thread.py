#:: IgnoreFile(silicon)(320)


from nagini_contracts.contracts import *
from nagini_contracts.thread import Thread, getARP, Joinable, getMethod, getArg, ThreadPost
from nagini_contracts.obligations import MustTerminate, WaitLevel, Level


class Clazz:

    def __init__(self) -> None:
        self.x = 0  # type: int
        Ensures(Acc(self.x) and self.x == 0)

    def readX(self) -> None:
        Requires(Rd(self.x))
        Requires(MustTerminate(2))
        Ensures(Rd(self.x))

    def startAndJoinWrite(self) -> None:
        Requires(Acc(self.x))
        Ensures(Acc(self.x))
        t1 = Thread(None, self.readX, args=())
        t2 = Thread(None, self.readX, args=())
        t1.start(self.readX)
        t2.start(self.readX)
        t1.join(self.readX)
        t2.join(self.readX)

    def startAndJoinRead(self) -> None:
        Requires(Rd(self.x))
        Ensures(Rd(self.x))
        t1 = Thread(None, self.readX, args=())
        t2 = Thread(None, self.readX, args=())
        t1.start(self.readX)
        t2.start(self.readX)
        t1.join(self.readX)
        t2.join(self.readX)

    def start1(self) -> Thread:
        Requires(Rd(self.x))
        Ensures(Acc(self.x, ARP() - getARP(Result())))
        t = Thread(None, self.readX, args=())
        t.start(self.readX)
        return t

    def start2(self) -> Thread:
        Requires(Rd(self.x))
        Ensures(Acc(self.x, ARP() - getARP(Result())))
        t1 = Thread(None, self.readX, args=())
        t2 = Thread(None, self.readX, args=())
        t1.start(self.readX)
        t2.start(self.readX)
        t1.join(self.readX)
        return t2

    def join1(self, t: Thread) -> None:
        Requires(getMethod(t) == Clazz.readX)
        Requires(getArg(t, 0) is self)
        Requires(Joinable(t))
        Requires(Acc(ThreadPost(t), 1))
        Requires(Acc(self.x, 1 - getARP(t)))
        Requires(WaitLevel() < Level(t))
        Ensures(Acc(self.x))
        t.join(self.readX)

    def join2(self, t1: Thread, t2: Thread) -> None:
        Requires(t1 is not t2)
        Requires(getMethod(t1) == Clazz.readX)
        Requires(getMethod(t2) == Clazz.readX)
        Requires(getArg(t1, 0) is self)
        Requires(getArg(t2, 0) is self)
        Requires(Joinable(t1))
        Requires(Joinable(t2))
        Requires(Acc(ThreadPost(t1)))
        Requires(Acc(ThreadPost(t2)))
        Requires(WaitLevel() < Level(t1))
        Requires(WaitLevel() < Level(t2))
        Ensures(Acc(self.x, getARP(t1) + getARP(t2)))
        t1.join(self.readX)
        t2.join(self.readX)
