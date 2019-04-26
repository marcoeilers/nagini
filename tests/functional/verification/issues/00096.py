# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate
from nagini_contracts.thread import Thread


class Cell:

     def __init__(self) -> None:
         Ensures(Acc(self.x))
         self.x = 0  # type: int

     def void(self) -> None:
         Requires(Acc(self.x, 1/4))
         Requires(MustTerminate(2))
         Ensures(Acc(self.x, 1/4))

     def a12(self, a: int) -> None:
         Requires(Acc(self.x, 1/2))
         Ensures(Acc(self.x, 1/2))
         i = 0  # type: int
         while i < a:
             Invariant(Acc(self.x, 1/2))
             t1 = Thread(None, self.void, args=())
             t1.start(self.void)
             t1.join(self.void)
             i += 1
