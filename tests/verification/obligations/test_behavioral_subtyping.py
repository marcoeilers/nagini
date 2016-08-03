from py2viper_contracts.contracts import (
    Requires,
)
from py2viper_contracts.obligations import *


class Super:

    #:: Label(Super__do_stuff)
    def do_stuff(self) -> None:
        Requires(MustTerminate(2))


class SubIncreased(Super):

    #:: ExpectedOutput(leak_check.failed:must_terminate.not_taken,Super__do_stuff)
    def do_stuff(self) -> None:
        """Measure increased. Error."""
        Requires(MustTerminate(3))


class SubDecreased(Super):

    def do_stuff(self) -> None:
        """Measure decreased. Ok."""
        Requires(MustTerminate(1))


class SubUnchanged(Super):

    def do_stuff(self) -> None:
        """Measure the same. Ok."""
        Requires(MustTerminate(2))
