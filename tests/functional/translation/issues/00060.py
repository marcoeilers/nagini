#:: IgnoreFile(/py2viper/issue/60/)


from py2viper_contracts.contracts import (
    Requires,
    Acc,
)


class C:

    def __init__(self) -> None:
        self.f = 0

    def test(self) -> None:
        Requires(
            Acc(self.f) == 1
        )
