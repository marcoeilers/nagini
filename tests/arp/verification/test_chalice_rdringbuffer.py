# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

# chaliceSuite/examples/RdRingBuffer.chalice

from nagini_contracts.contracts import *


class RingBuffer:

    def __init__(self) -> None:
        Ensures(Acc(self.data))
        Ensures(Acc(self.first))
        Ensures(Acc(self.datalen))
        self.data = PSeq()  # type: PSeq[int]
        self.first = 0  # type: int
        self.datalen = 0  # type: int

    @Predicate
    def valid(self) -> bool:
        return Acc(self.data) and Acc(self.first) and Acc(self.datalen) and \
               0 <= self.first and 0 <= self.datalen and \
               Implies(len(self.data) == 0, self.datalen == 0 and self.first == 0) and \
               Implies(len(self.data) > 0, self.datalen <= len(self.data) and self.first < len(self.data))

    @Pure
    def contents(self) -> PSeq[int]:
        Requires(Rd(self.valid()))
        return Unfolding(Rd(self.valid()),
                         self.data.drop(self.first).take(self.datalen)
                         if self.first + self.datalen <= len(self.data)
                         else self.data.drop(self.first) + self.data.take(self.first + self.datalen - len(self.data)))

    @Pure
    def capacity(self) -> int:
        Requires(Rd(self.valid()))
        return Unfolding(Rd(self.valid()), len(self.data))

    def create(self, n: int) -> None:
        Requires(0 <= n)
        Requires(Acc(self.data) and Acc(self.first) and Acc(self.datalen))
        Ensures(self.valid())
        Ensures(len(self.contents()) == 0 and self.capacity() == n)
        self.data = PSeq()
        i = n
        while i > 0:
            Invariant(Acc(self.data) and 0 <= i and len(self.data) == n - i)
            self.data = self.data + PSeq(0)
            i -= 1
        self.first = 0
        self.datalen = 0
        Fold(self.valid())

    def clear(self) -> None:
        Requires(self.valid())
        Ensures(self.valid())
        Ensures(len(self.contents()) == 0 and self.capacity() == Old(self.capacity()))
        Unfold(self.valid())
        self.datalen = 0
        Fold(self.valid())

    @Pure
    def head(self) -> int:
        Requires(Rd(self.valid()))
        Requires(len(self.contents()) != 0)
        # TODO: The next one apparently should not be necessary but is, unfortunately.
        Requires(Unfolding(Rd(self.valid()), self.first >= 0 and self.first < len(self.data)))
        Ensures(Result() == self.contents()[0])
        return Unfolding(Rd(self.valid()), self.data[self.first])

    def push(self, x: int) -> None:
        Requires(self.valid())
        Requires(len(self.contents()) != self.capacity())
        Ensures(self.valid())
        Ensures(self.contents() == Old(self.contents()) + PSeq(x))
        Ensures(self.capacity() == Old(self.capacity()))
        Unfold(self.valid())
        nextEmpty = self.first + self.datalen if self.first + self.datalen < len(self.data) else self.first + self.datalen - len(self.data)
        self.data = self.data.update(nextEmpty, x)
        self.datalen += 1
        Fold(self.valid())

    def pop(self) -> int:
        Requires(self.valid())
        Requires(len(self.contents()) != 0)
        Ensures(self.valid())
        Ensures(Result() == Old(self.contents())[0])
        Ensures(self.contents() == Old(self.contents()).drop(1))
        Ensures(self.capacity() == Old(self.capacity()))
        Unfold(self.valid())
        res = self.data[self.first]
        self.first = 0 if self.first + 1 == len(self.data) else self.first + 1
        self.datalen -= 1
        Fold(self.valid())
        return res


class Client:

    def testHarness(self, x: int, y: int, z: int) -> None:
        b = RingBuffer()
        b.create(2)
        b.push(x)
        b.push(y)
        h = b.pop()
        Assert(h == x)
        b.push(z)
        h = b.pop()
        Assert(h == y)
        h = b.pop()
        Assert(h == z)
