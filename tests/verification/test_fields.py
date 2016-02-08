from contracts.contracts import *


class SuperClass:
    def construct(self) -> None:
        Requires(self != None)
        Requires(Acc(self.superfield))  # type: ignore
        Requires(Acc(self.__privatefield))  # type: ignore
        Requires(Acc(self.typedfield))  # type: ignore
        Ensures(Acc(self.superfield) and self.superfield == 12)  # type: ignore
        Ensures(Acc(
            self.__privatefield) and self.__privatefield == 15)  # type: ignore
        Ensures(Acc(self.typedfield)  # type: ignore
                and isinstance(self.typedfield, SuperClass))  # type: ignore
        self.superfield = 12
        self.__privatefield = 15
        self.typedfield = SuperClass()

    @Pure
    def getprivate(self) -> int:
        Requires(self != None)
        Requires(Acc(self.__privatefield))
        return self.__privatefield

    @Pure
    def getpublic(self) -> int:
        Requires(self != None)
        Requires(Acc(self.superfield))
        return self.superfield


class SubClass(SuperClass):
    def constructsub(self) -> None:
        Requires(self != None)
        Requires(Acc(self.__privatefield))  # type: ignore
        Requires(Acc(self.superfield))  # type: ignore
        Ensures(Acc(
            self.__privatefield) and self.__privatefield == 35)  # type: ignore
        Ensures(Acc(self.superfield) and self.superfield == 45)  # type: ignore
        self.__privatefield = 35
        self.superfield = 45

    def setprivate(self, i: int) -> None:
        Requires(self != None)
        Requires(Acc(self.__privatefield))
        Ensures(Acc(self.__privatefield) and self.__privatefield == i)
        self.__privatefield = i

    @Pure
    def getprivatesub(self) -> int:
        Requires(self != None)
        Requires(Acc(self.__privatefield))
        return self.__privatefield

    @Pure
    def getpublicsub(self) -> int:
        Requires(self != None)
        Requires(Acc(self.superfield))
        return self.superfield


def main() -> None:
    sub = SubClass()
    sub.construct()
    Assert(sub.getprivate() == 15)
    Assert(sub.getpublic() == 12)
    Assert(sub.getpublic() == sub.getpublicsub())
    sub.constructsub()
    Assert(sub.getprivate() == 15)
    Assert(sub.getprivatesub() == 35)
    Assert(sub.getprivate() != sub.getprivatesub())
    Assert(sub.getpublic() == 45)
    Assert(sub.getpublic() == sub.getpublicsub())
    Assert(sub.getpublic() == sub.superfield)
    sub.superfield = 77
    Assert(sub.getpublic() == 77)
    Assert(sub.getpublicsub() == 77)
    sub.setprivate(15)
    Assert(sub.getprivate() == sub.getprivatesub())
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(sub.getprivate() == 99)
