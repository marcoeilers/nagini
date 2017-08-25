from nagini_contracts.contracts import *
class DummyObj :
    def __init__(self, value : int) -> None :
        Ensures(Acc(self.val) and (self.val == value)) # type: ignore
        self.val = value

    def incr(self) -> None:
        Requires(Acc(self.val))
        Ensures(Acc(self.val) and (self.val == Old(self.val) + 1))
        self.val = self.val + 1

    def decr(self) -> None:
        Requires(Acc(self.val))
        Ensures(Acc(self.val) and (self.val == Old(self.val) - 1))
        self.val = self.val - 1

def test() -> None:
    x = DummyObj(1)
    t = Thread(DummyObj.incr,(x,))
    z = x
    x.val = 3
    
    t.start(DummyObj.incr,DummyObj.decr)
    y = x
    t.join(DummyObj.incr,DummyObj.decr)
    Assert(y.val == 4 and z.val == 4)


def ThreadJoinerforIncrDecr(t : Thread, struct : DummyObj, v : int) -> None: 
    Requires(v == t.getOld(0) and struct == t.getArg(0))
    Requires(Acc(t.state) and t.hasStarted())
    
    Ensures (Implies((Old(t.state) == STARTED()), 
                        (Implies(t.impl(DummyObj.incr),(Acc(struct.val) and struct.val == v + 1)))
                        and (Implies(t.impl(DummyObj.decr),Acc(struct.val) and struct.val == v + 2))))
    t.join(DummyObj.incr,DummyObj.decr)

def test2() -> None:
    x = DummyObj(1)
    t = Thread(DummyObj.incr,(x,))
    z = x
    x.val = 3
    t.start(DummyObj.incr,DummyObj.decr)
    y = x
    ThreadJoinerforIncrDecr(t,x,3)
    Assert(y.val == 4 and z.val == 4)

def test3() -> None:
    x = DummyObj(1)
    if(x.val < 2) :
        t = Thread(DummyObj.incr,(x,))
    else :
        t = Thread(DummyObj.decr,(x,))
    z = x
    t.start(DummyObj.incr,DummyObj.decr)
    y = x
    t.join(DummyObj.incr,DummyObj.decr)
    Assert(y.val == 2 and z.val == 2)


"""
impl, getArg, getOld : we keep the method, the arguments, and the old values of heap-dependant
variables of a thread somewhere. This gives us access to all of those as ghost variables.

t.postcond(methods list) : this could be a "macro" which would generate exactly what would be
inhaled during t.join(methods list) 

Ideas : a method "maystart" "mayjoin"
"""
