from nagini_contracts.contracts import *


class A:
    def __init__(self) -> None:
        self.a = 12
        Ensures(Acc(self.a))
        Ensures(MaySet(self, 'b'))

    def set(self, v: int) -> None:
        Requires(MaySet(self, 'b'))
        self.b = v
        Ensures(Acc(self.b))

    def set2(self, v: int) -> None:
        Requires(MayCreate(self, 'b'))
        self.b = v
        Ensures(Acc(self.b))

    def set3(self, v: int) -> None:
        Requires(MayCreate(self, 'b'))
        self.b = v
        Ensures(MaySet(self, 'b'))

    def set4(self, v: int) -> None:
        Requires(MaySet(self, 'b'))
        self.b = v
        #:: ExpectedOutput(postcondition.violated:assertion.false)
        Ensures(False)

    def set5(self, v: int) -> None:
        Requires(MayCreate(self, 'b'))
        self.b = v
        #:: ExpectedOutput(postcondition.violated:assertion.false)
        Ensures(False)

    def set6(self, v: int) -> None:
        Requires(MayCreate(self, 'b'))
        self.b = v
        #:: ExpectedOutput(postcondition.violated:assertion.false)
        Ensures(False)

    def del1(self) -> None:
        Requires(Acc(self.b))
        #:: ExpectedOutput(postcondition.violated:insufficient.permission)
        Ensures(Acc(self.b))
        del self.b

    def del2(self) -> None:
        Requires(Acc(self.b))
        Ensures(MayCreate(self, 'b'))
        del self.b

    def del3(self) -> None:
        Requires(Acc(self.b))
        Ensures(MaySet(self, 'b'))
        del self.b

    def del4(self) -> None:
        Requires(MaySet(self, 'b'))
        #:: ExpectedOutput(exhale.failed:insufficient.permission)
        del self.b

    def del5(self) -> None:
        Requires(MayCreate(self, 'b'))
        #:: ExpectedOutput(exhale.failed:insufficient.permission)
        del self.b

    def get(self) -> int:
        Requires(Acc(self.b))
        Ensures(Acc(self.b) and Result() == self.b)
        return self.b


def client_1_1() -> None:
    a = A()
    a.set(56)
    assert a.get() == a.b
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert a.b == 56


def client_1_2() -> None:
    a = A()
    a.set2(56)
    assert a.get() == a.b
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert a.b == 56


def client_2() -> None:
    a = A()
    #:: ExpectedOutput(call.failed:insufficient.permission)
    a.get()


def client_3_1() -> None:
    a = A()
    a.set(56)
    a.set(43)
    assert a.get() == a.b
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert a.b == 56


def client_3_2() -> None:
    a = A()
    a.set2(56)
    #:: ExpectedOutput(call.failed:insufficient.permission)
    a.set(43)


def client_4() -> None:
    a = A()
    a.set(56)
    a.b = 12
    assert a.b == 12
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert a.b == 56


def client_5() -> None:
    a = A()
    a.set3(23)
    #:: ExpectedOutput(assignment.failed:insufficient.permission)
    b = a.b


def client_6() -> None:
    a = A()
    a.set3(23)
    a.b = 2323
    b = a.b
    assert b == 2323
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False

def client_7_1() -> None:
    a = A()
    a.b = 15
    a.del2()
    #:: ExpectedOutput(assignment.failed:insufficient.permission)
    c = a.b

def client_7_2() -> None:
    a = A()
    a.b = 15
    a.del3()
    #:: ExpectedOutput(assignment.failed:insufficient.permission)
    c = a.b
