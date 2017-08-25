from nagini_contracts.contracts import *
class DummyObj :
    def __init__(self, value : int) -> None :
        Ensures(Acc(self.val) and (self.val == value)) # type: ignore
        self.val = value

    def incr(self, n : int) -> None:
        Requires(Acc(self.val) and self.val == n)
        Ensures(Acc(self.val) and (self.val == n + 1))
        self.val = self.val + 1

    def decr(self,  n : int) -> None:
        Requires(Acc(self.val) and self.val == n)
        Ensures(Acc(self.val) and (self.val == n - 1))
        self.val = self.val - 1

def test() -> None:
    x = DummyObj(1)
    t = Thread(DummyObj.incr,(x,1,1))
    z = x
    t.start(DummyObj.incr,DummyObj.decr)
    y = x
    t.join(DummyObj.incr,DummyObj.decr)
    Assert(y.val == 2 and z.val == 2)

