# chaliceSuite/examples/RdRingBuffer.chalice

from nagini_contracts.contracts import *


class RingBuffer:

    def __init__(self) -> None:
        Ensures(Acc(self.data))
        Ensures(Acc(self.first))
        Ensures(Acc(self.len))
        self.data = []  # type: List[int]
        self.first = 0  # type: int
        self.len = 0  # type: int

    @Predicate
    def valid(self) -> bool:
        return Acc(self.data) and Acc(self.first) and Acc(self.len) and \
               0 <= self.first and 0 <= self.len and \
               Implies(len(self.data) == 0, self.len == 0 and self.first == 0) and \
               Implies(len(self.data) > 0, self.len <= len(self.data) and self.first < len(self.data))

    @Pure
    def contents(self) -> List[int]:
        Requires(Rd(self.valid()))
        #:: UnexpectedOutput(purity.violated)
        return Unfolding(Rd(self.valid()),
                         self.data[self.first:self.first + self.len]
                         if self.first + self.len <= len(self.data)
                         else self.data[self.first:] + self.data[:self.first + self.len - len(self.data)])

    @Pure
    def capacity(self) -> int:
        Requires(Rd(self.valid()))
        return Unfolding(Rd(self.valid()), len(self.data))

    def create(self, n: int) -> None:
        Requires(0 <= n)
        Requires(Acc(self.data) and Acc(self.first) and Acc(self.len))
        Ensures(self.valid())
        Ensures(self.contents() == [] and self.capacity() == n)
        self.data = []
        for i in range(n, 0, -1):
            Invariant(Acc(self.data) and 0 <= i and len(self.data) == n - i)
            self.data.append(0)
        self.first = 0
        self.first = 0
        Fold(self.valid())

    def clear(self) -> None:
        Requires(self.valid())
        Ensures(self.valid())
        Ensures(self.contents() == [] and self.capacity() == Old(self.capacity()))
        Unfold(self.valid())
        self.len = 0
        Fold(self.valid())

    def head(self) -> int:
        Requires(Rd(self.valid()))
        Requires(self.contents() != [])
        Ensures(Result() == self.contents()[0])
        return Unfolding(Rd(self.valid()), self.data[self.first])

    def push(self, x: int) -> None:
        Requires(self.valid())
        Requires(len(self.contents()) != self.capacity())
        Ensures(self.valid())
        Ensures(self.contents() == Old(self.contents()) + [x])
        Ensures(self.capacity() == Old(self.capacity()))
        Unfold(self.valid())
        nextEmpty = self.first + self.len if self.first + self.len < len(self.data) else self.first + self.len - len(self.data)
        self.data[nextEmpty] = x
        self.len += 1
        Fold(self.valid())

    def pop(self) -> int:
        Requires(self.valid())
        Requires(self.contents() != [])
        Ensures(self.valid())
        Ensures(Result() == Old(self.contents())[0])
        Ensures(self.contents() == Old(self.contents())[1:])
        Ensures(self.capacity() == Old(self.capacity()))
        Unfold(self.valid())
        res = self.data[self.first]
        self.first = 0 if self.first + 1 == len(self.data) else self.first + 1
        self.len -= 1
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
