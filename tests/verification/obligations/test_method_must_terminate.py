from py2viper_contracts.contracts import (
    Requires,
    Invariant,
    Implies,
    Assert,
)
from py2viper_contracts.io import IOExists1
from py2viper_contracts.obligations import *


# Test that measures are always positive.

def over_in_minus_one() -> None:
    #:: Label(over_in_minus_one__MustTerminate)
    Requires(MustTerminate(-1))
    # Negative measure is equivalent to False.
    Assert(False)


def check_over_in_minus_one() -> None:
    #:: ExpectedOutput(call.precondition:obligation_measure.non_positive,over_in_minus_one__MustTerminate)
    over_in_minus_one()


def over_in_minus_one_conditional(b: bool) -> None:
    Requires(Implies(b, MustTerminate(1)))
    #:: Label(over_in_minus_one_conditional__MustTerminate__False)
    Requires(Implies(not b, MustTerminate(-1)))
    # Negative measure is equivalent to False.
    Assert(Implies(not b, False))
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(False)


def check_over_in_minus_one_conditional_1() -> None:
    over_in_minus_one_conditional(True)


def check_over_in_minus_one_conditional_2() -> None:
    #:: ExpectedOutput(call.precondition:obligation_measure.non_positive,over_in_minus_one_conditional__MustTerminate__False)
    over_in_minus_one_conditional(False)
