from nagini_contracts.contracts import *

class Container:
    def __init__(self) -> None:
        Ensures(Acc(self.v))  # type: ignore
        Ensures(Acc(self.P()))
        self.v = 14
        self.v2 = 15
        Fold(self.P())

    @Predicate
    def P(self) -> bool:
        return Acc(self.v2)

    @Pure
    def needs_pred_full(self) -> int:
        Requires(self.P())
        return Unfolding(self.P(), self.v2)

    @Pure
    def needs_pred(self) -> int:
        Requires(Rd(self.P()))
        return Unfolding(self.P(), self.v2)

    @Pure
    def needs_field_full(self) -> int:
        Requires(Acc(self.v))
        return self.v

    @Pure
    def needs_field(self) -> int:
        Requires(Rd(self.v))
        return self.v

    def needs_fixed_pred(self) -> int:
        Requires(self.P())
        Ensures(self.P())
        return Unfolding(self.P(), self.v2)

    def needs_fixed_field(self) -> int:
        Requires(Acc(self.v))
        Ensures(Acc(self.v))
        return self.v


def client() -> None:
    c = Container()
    fixed_write_client(c)
    fixed_client(c)
    c.v = 1
    Unfold(c.P())
    Fold(c.P())
    rd_client(c)
    #:: ExpectedOutput(assignment.failed:insufficient.permission)
    c.v = 1


def rd_client(c: Container) -> None:
    Requires(Rd(c.P()))
    Requires(Rd(c.v))
    Ensures(Rd(c.P()))
    Ensures(Rd(c.v))
    a = c.needs_pred()
    b = c.needs_pred2()
    d = c.needs_field()
    e = c.needs_field2()
    #:: ExpectedOutput(call.precondition:insufficient.permission)
    f = c.needs_fixed_pred()


def fixed_write_client(c: Container) -> None:
    Requires(Acc(c.P()))
    Requires(Acc(c.v))
    Ensures(Acc(c.P()))
    Ensures(Acc(c.v))
    a = c.needs_pred()
    b = c.needs_pred2()
    d = c.needs_field()
    e = c.needs_field2()
    f = c.needs_fixed_pred()


def fixed_client(c: Container) -> None:
    Requires(Acc(c.P(), 1/10000))
    Requires(Acc(c.v, 1/10000))
    Ensures(Acc(c.P(), 1/10000))
    Ensures(Acc(c.v, 1/10000))
    a = c.needs_pred()
    b = c.needs_pred2()
    d = c.needs_field()
    e = c.needs_field2()
    #:: ExpectedOutput(call.precondition:insufficient.permission)
    f = c.needs_fixed_field()


def none_client_1(c: Container) -> None:
    #:: ExpectedOutput(application.precondition:insufficient.permission)
    a = c.needs_pred()


def none_client_2(c: Container) -> None:
    #:: ExpectedOutput(application.precondition:insufficient.permission)
    a = c.needs_pred2()


def none_client_3(c: Container) -> None:
    #:: ExpectedOutput(application.precondition:insufficient.permission)|ExpectedOutput(carbon)(application.precondition:assertion.false)
    a = c.needs_field()


def none_client_4(c: Container) -> None:
    #:: ExpectedOutput(application.precondition:insufficient.permission)|ExpectedOutput(carbon)(application.precondition:assertion.false)
    a = c.needs_field2()