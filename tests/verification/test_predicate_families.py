from py2viper_contracts.contracts import *


class Super:
    def __init__(self, val: int) -> None:
        Ensures(Acc(self.field) and self.field == val) # type: ignore
        self.field = val

    @Predicate
    def meh(self, val: int) -> bool:
        return Acc(self.field) and self.field == val

    def set_sth(self, old_val: int, new_val: int) -> None:
        Requires(self.meh(old_val))
        Ensures(Acc(self.meh(new_val)))
        Unfold(Acc(self.meh(old_val)))
        self.field = new_val
        Fold(self.meh(new_val))


class Sub(Super):
    def __init__(self, val: int) -> None:
        Ensures(Acc(self.field) and self.field == val) # type: ignore
        Ensures(Acc(self.sub_field) and self.sub_field == 15) # type: ignore
        super().__init__(val)
        self.sub_field = 15

    @Predicate
    def meh(self, val: int) -> bool:
        return Acc(self.sub_field) and self.sub_field == 15


class Other:
    def __init__(self) -> None:
        Ensures(Acc(self.whatever_field)) # type: ignore
        self.whatever_field = 15

    @Predicate
    def meh(self, val: int) -> bool:
        return Acc(self.whatever_field)

def main() -> None:
    ss = Sub(25)
    Fold(ss.meh(25))
    ss.set_sth(25, 35)
    Unfold(ss.meh(35))