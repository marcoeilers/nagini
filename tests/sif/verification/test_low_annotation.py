from nagini_contracts.contracts import *

class Container:
    def __init__(self) -> None:
        self.f = 0
        Ensures(Acc(self.f))

def get_secret() -> int:
    return 12

@Predicate
def contPred(c: Container) -> bool:
    return Acc(c.f)

@AllLow
def inc(c: Container) -> None:
    Requires(Acc(c.f))
    Ensures(Acc(c.f))
    Ensures(c.f == Old(c.f) + 1)
    c.f = c.f + 1

@PreservesLow
def add_preserving(amount: int, c: Container) -> None:
    Requires(Acc(c.f))
    Ensures(Acc(c.f))
    Ensures(c.f == Old(c.f) + amount)
    c.f += amount

@AllLow
def addLoop(amount: int, c: Container) -> None:
    Requires(Acc(c.f))
    Requires(amount >= 0)
    Ensures(Acc(c.f))
    Ensures(c.f == Old(c.f) + amount)
    i = 0
    while i < amount:
        Invariant(Acc(c.f))
        Invariant(0 <= i and i <= amount)
        Invariant(c.f == Old(c.f) + i)
        inc(c)
        i += 1

@PreservesLow
def inc_preserving(c: Container) -> None:
    Requires(Acc(c.f))
    Ensures(Acc(c.f))
    Ensures(c.f == Old(c.f) + 1)
    c.f = c.f + 1

@PreservesLow
def add_loop_preserving(amount: int, c: Container) -> None:
    Requires(Acc(c.f))
    Requires(amount >= 0)
    Ensures(Acc(c.f))
    Ensures(c.f == Old(c.f) + amount)
    i = 0
    while i < amount:
        Invariant(Acc(c.f))
        Invariant(0 <= i and i <= amount)
        Invariant(c.f == Old(c.f) + i)
        inc_preserving(c)
        i += 1

@AllLow
def incPred(c: Container) -> None:
    Requires(contPred(c))
    Ensures(contPred(c))
    Ensures(Unfolding(contPred(c), c.f == Old(Unfolding(contPred(c), c.f)) + 1))
    Unfold(contPred(c))
    c.f = c.f + 1
    Fold(contPred(c))

@AllLow
def addPredLoop(amount: int, c: Container) -> None:
    Requires(contPred(c))
    Requires(amount >= 0)
    Ensures(contPred(c))
    Ensures(Unfolding(contPred(c), c.f == Old(Unfolding(contPred(c), c.f)) + amount))
    i = 0
    while i < amount:
        Invariant(contPred(c))
        Invariant(0 <= i and i <= amount)
        Invariant(Unfolding(contPred(c), c.f == Old(Unfolding(contPred(c), c.f)) + i))
        incPred(c)
        i += 1

@AllLow
def addPred(amount: int, c: Container) -> None:
    Requires(contPred(c))
    Ensures(contPred(c))
    Unfold(contPred(c))
    c.f += amount
    Fold(contPred(c))

@PreservesLow
def addPred_preserving(amount: int, c: Container) -> None:
    Requires(contPred(c))
    Ensures(contPred(c))
    Unfold(contPred(c))
    c.f += amount
    Fold(contPred(c))

@PreservesLow
def pred_assert_low(amount: int, c: Container) -> None:
    Requires(contPred(c))
    Assert(contPred(c))
    Unfold(contPred(c))
    c.f = get_secret()
    #:: ExpectedOutput(fold.failed:sif.fold)
    Fold(contPred(c))

@AllLow
def low_m(a: int) -> int:
    return a + 1

def test_inc_preserving(secret: bool, c: Container) -> None:
    Requires(LowEvent())
    Requires(Acc(c.f))
    Requires(Low(c))
    Requires(Low(c.f))
    Ensures(Acc(c.f))
    Ensures(Low(c))
    Ensures(LowVal(c.f))
    if secret:
        inc_preserving(c)
    else:
        inc_preserving(c)


def test_inc_all_low(secret: bool, c: Container) -> None:
    Requires(LowEvent())
    Requires(Low(c))
    Requires(Acc(c.f))
    Requires(Low(c.f))
    Ensures(Low(c))
    Ensures(Acc(c.f))
    Ensures(Low(c.f))
    if secret:
        x = 1 # do something
    inc(c)

def test_inc_predicate(secret: bool, c: Container) -> None:
    Requires(contPred(c) and Low(c) and Unfolding(contPred(c), Low(c.f)))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(contPred(c) and Low(c) and Unfolding(contPred(c), Low(c.f)))
    if secret:
        incPred(c)

def test_add_predicate(secret: int, c: Container) -> None:
    Requires(contPred(c))
    Ensures(contPred(c))
    #:: ExpectedOutput(call.precondition:assertion.false)|ExpectedOutput(carbon)(call.precondition:assertion.false)
    addPred(secret, c)

def test_add_preserving(secret: int, c: Container) -> None:
    Requires(Acc(c.f))
    Requires(Low(c) and Low(c.f))
    Ensures(Acc(c.f))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Low(c) and Low(c.f))
    add_preserving(secret, c)
