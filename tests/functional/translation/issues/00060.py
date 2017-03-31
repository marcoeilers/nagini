#:: IgnoreFile(60)


from nagini_contracts.contracts import (
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
