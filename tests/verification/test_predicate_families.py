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

class A:

    def __init__(self) -> None:
        Ensures(Acc(self.afield))  # type: ignore
        self.afield = 14

    @Predicate
    def pred1(self, a: int) -> bool:
        return Acc(self.afield) and self.afield == a

    def set1(self, _old: int) -> None:
        Requires(self.pred1(_old))
        Ensures(self.pred1(_old + 1))
        self.set2(_old)

    def set2(self, oold: int) -> int:
        Requires(self.pred1(oold))
        Ensures(self.pred1(oold + 1))
        Unfold(self.pred1(oold))
        self.afield += 1
        res_val = self.afield
        Fold(self.pred1(oold + 1))
        return res_val

    def set3(self, oold: int) -> int:
        Requires(self.pred1(oold))
        Ensures(self.pred1(oold + 1))
        Unfold(self.pred1(oold))
        self.afield += 1
        res_val = self.afield
        Fold(self.pred1(oold + 1))
        return res_val

    def set4(self, oold: int) -> int:
        Requires(self.pred1(oold))
        Ensures(self.pred1(oold + 1))
        Unfold(self.pred1(oold))
        self.afield += 1
        res_val = self.afield
        Fold(self.pred1(oold + 1))
        return res_val


class B(A):

    def __init__(self) -> None:
        Ensures(self.pred1(14))
        super().__init__()
        self.bfield = 14
        Fold(self.pred1(14))

    @Predicate
    def pred1(self, b: int) -> bool:
        return Acc(self.bfield) and self.bfield == self.afield

    def set2(self, ooold: int) -> int:
        Requires(self.pred1(ooold))
        Ensures(self.pred1(ooold + 1))
        Unfold(self.pred1(ooold))
        super().set2(ooold)
        self.bfield = ooold + 1
        res_val = self.afield
        Fold(self.pred1(ooold + 1))
        return res_val

    def set4(self, oold: int) -> int:
        Requires(self.pred1(oold))
        Ensures(self.pred1(oold + 1))
        Unfold(self.pred1(oold))
        super().set2(oold)
        self.afield = oold + 1
        res_val = self.afield
        Fold(self.pred1(oold + 1))
        return res_val