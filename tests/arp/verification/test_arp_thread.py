from nagini_contracts.contracts import *
from nagini_contracts.thread import Thread
from nagini_contracts.obligations import MustTerminate


class Clazz:

    def __init__(self) -> None:
        self.x = 0
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
