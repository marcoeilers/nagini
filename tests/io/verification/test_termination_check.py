# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    Implies,
    Pure,
    Result,
)
from nagini_contracts.io_contracts import *
from nagini_contracts.io_builtins import (
    end_io,
    gap_io,
    no_op_io,
)

# Helpers.

@Pure
def max(a: int, b: int) -> int:
    return a if a > b else b

@IOOperation
def random_bool_io(
        t_pre: Place,
        value: bool = Result(),
        t_post: Place = Result()) -> bool:
    Terminates(True)

@IOOperation
def non_terminating_io(
        t_pre: Place,
        t_post: Place = Result()) -> bool:
    Terminates(False)

@IOOperation
def terminating_io(
        t_pre: Place,
        t_post: Place = Result()) -> bool:
    Terminates(True)

@IOOperation
def conditionally_terminating_io(
        t_pre: Place,
        value: bool,
        t_post: Place = Result()) -> bool:
    Terminates(value)

# Termination measure.

@IOOperation
def test_measure_io1_basic(
        t_pre: Place,
        value: int,
        t_post: Place = Result()) -> bool:
    Terminates(True)
    TerminationMeasure(max(value, 1))

@IOOperation
def test_measure_io1_non_basic(
        t_pre: Place,
        value: int,
        t_post: Place = Result()) -> bool:
    Terminates(True)
    TerminationMeasure(max(value, 2))
    return no_op_io(t_pre, t_post)

@IOOperation
def test_measure_io2_basic(
        t_pre: Place,
        value: int,
        t_post: Place = Result()) -> bool:
    TerminationMeasure(value)

@IOOperation
def test_measure_io2_non_basic(
        t_pre: Place,
        value: int,
        t_post: Place = Result()) -> bool:
    TerminationMeasure(value)
    return no_op_io(t_pre, t_post)

@IOOperation
def test_measure_io3_basic(
        t_pre: Place,
        value: int,
        t_post: Place = Result()) -> bool:
    Terminates(True)
    #:: ExpectedOutput(termination_check.failed:termination_measure.non_positive)
    TerminationMeasure(value)

@IOOperation
def test_measure_io3_non_basic(
        t_pre: Place,
        value: int,
        t_post: Place = Result()) -> bool:
    Terminates(True)
    #:: ExpectedOutput(termination_check.failed:termination_measure.non_positive)
    TerminationMeasure(value)
    #:: ExpectedOutput(carbon)(termination_check.failed:measure.non_decreasing)
    return no_op_io(t_pre, t_post)

# Gap.

@IOOperation
def test_gap_io1(
        t_pre: Place,
        t_post: Place = Result()) -> bool:
    TerminationMeasure(2)
    return gap_io(t_pre, t_post)

@IOOperation
def test_gap_io2(
        t_pre: Place,
        t_post: Place = Result()) -> bool:
    Terminates(True)
    TerminationMeasure(2)
    #:: ExpectedOutput(termination_check.failed:gap.enabled)
    return gap_io(t_pre, t_post)

@IOOperation
def test_gap_io3(
        t_pre: Place,
        value: bool,
        t_post: Place = Result()) -> bool:
    Terminates(value)
    TerminationMeasure(2)
    #:: ExpectedOutput(termination_check.failed:gap.enabled)
    return (Implies(value, gap_io(t_pre, t_post)) and
            no_op_io(t_pre, t_post))

@IOOperation
def test_gap_io4(
        t_pre: Place,
        value: bool,
        t_post: Place = Result()) -> bool:
    Terminates(value)
    TerminationMeasure(2)
    return (Implies(not value, gap_io(t_pre, t_post))
            and no_op_io(t_pre, t_post))

@IOOperation
def test_gap_io5(
        t_pre: Place,
        value: bool,
        t_post: Place = Result()) -> bool:
    Terminates(value)
    TerminationMeasure(2)
    #:: ExpectedOutput(termination_check.failed:gap.enabled)
    return gap_io(t_pre, t_post) if value else no_op_io(t_pre, t_post)

@IOOperation
def test_gap_io6(
        t_pre: Place,
        value: bool,
        t_post: Place = Result()) -> bool:
    Terminates(value)
    TerminationMeasure(2)
    return gap_io(t_pre, t_post) if not value else no_op_io(t_pre, t_post)

@IOOperation
def test_gap_io7(
        t_pre: Place,
        value: bool,
        t_post: Place = Result()) -> bool:
    Terminates(value)
    TerminationMeasure(2)
    return IOExists2(Place, Place)(
        lambda t1, t2: (
            no_op_io(t_pre, t1) and
            Implies(not value, gap_io(t1, t2)) and
            no_op_io(t1, t2) and
            no_op_io(t2, t_post)
        )
    )

@IOOperation
def test_gap_io8(
        t_pre: Place,
        value: bool,
        t_post: Place = Result()) -> bool:
    Terminates(value)
    TerminationMeasure(2)
    return IOExists2(Place, Place)(
        lambda t1, t2: (
            no_op_io(t_pre, t1) and
            #:: ExpectedOutput(termination_check.failed:gap.enabled)
            Implies(value, gap_io(t1, t2)) and
            no_op_io(t1, t2) and
            no_op_io(t2, t_post)
        )
    )

@IOOperation
def test_gap_io9(
        t_pre: Place,
        t_post: Place = Result()) -> bool:
    Terminates(True)
    TerminationMeasure(2)
    return IOExists3(Place, Place, bool)(
        lambda t1, t2, value: (
            random_bool_io(t_pre, value, t1) and
            #:: ExpectedOutput(termination_check.failed:gap.enabled)
            Implies(value, gap_io(t1, t2)) and
            no_op_io(t1, t2) and
            no_op_io(t2, t_post)
        )
    )

@IOOperation
def test_gap_io10(
        t_pre: Place) -> bool:
    TerminationMeasure(2)
    Terminates(True)
    return end_io(t_pre)

# Termination condition implication.

@IOOperation
def test_condition_io1(
        t_pre: Place,
        value: bool,
        t_post: Place = Result()) -> bool:
    Terminates(value)
    TerminationMeasure(2)
    #:: ExpectedOutput(termination_check.failed:child_termination.not_implied)
    return non_terminating_io(t_pre, t_post)

@IOOperation
def test_condition_io2(
        t_pre: Place,
        value: bool,
        t_post: Place = Result()) -> bool:
    Terminates(value)
    TerminationMeasure(2)
    return terminating_io(t_pre, t_post)

@IOOperation
def test_condition_io3(
        t_pre: Place,
        value: bool,
        t_post: Place = Result()) -> bool:
    Terminates(value)
    TerminationMeasure(2)
    return conditionally_terminating_io(t_pre, value, t_post)

@IOOperation
def test_condition_io4(
        t_pre: Place,
        value: bool,
        t_post: Place = Result()) -> bool:
    Terminates(value)
    TerminationMeasure(2)
    #:: ExpectedOutput(termination_check.failed:child_termination.not_implied)
    return (Implies(value, non_terminating_io(t_pre, t_post)) and
            no_op_io(t_pre, t_post))

@IOOperation
def test_condition_io5(
        t_pre: Place,
        value: bool,
        t_post: Place = Result()) -> bool:
    Terminates(value)
    TerminationMeasure(2)
    return (Implies(not value, non_terminating_io(t_pre, t_post)) and
            no_op_io(t_pre, t_post))

@IOOperation
def test_condition_io6(
        t_pre: Place,
        t_post: Place = Result()) -> bool:
    Terminates(True)
    TerminationMeasure(2)
    return IOExists3(Place, Place, bool)(
        lambda t1, t2, value: (
            random_bool_io(t_pre, value, t1) and
            #:: ExpectedOutput(termination_check.failed:child_termination.not_implied)
            Implies(value, non_terminating_io(t1, t2)) and
            no_op_io(t1, t2) and
            no_op_io(t2, t_post)
        )
    )

@IOOperation
def test_condition_io7(
        t_pre: Place,
        t_post: Place = Result()) -> bool:
    Terminates(True)
    TerminationMeasure(2)
    return IOExists3(Place, Place, bool)(
        lambda t1, t2, value: (
            random_bool_io(t_pre, value, t1) and
            #:: ExpectedOutput(termination_check.failed:child_termination.not_implied)
            Implies(not value, non_terminating_io(t1, t2)) and
            no_op_io(t1, t2) and
            no_op_io(t2, t_post)
        )
    )

@IOOperation
def test_condition_io8(
        t_pre: Place,
        t_post: Place = Result()) -> bool:
    Terminates(True)
    TerminationMeasure(2)
    return IOExists3(Place, Place, bool)(
        lambda t1, t2, value: (
            random_bool_io(t_pre, value, t1) and
            #:: ExpectedOutput(termination_check.failed:child_termination.not_implied)
            conditionally_terminating_io(t1, value, t2) and
            no_op_io(t2, t_post)
        )
    )

@IOOperation
def test_condition_io9(
        t_pre: Place,
        t_post: Place = Result()) -> bool:
    Terminates(True)
    TerminationMeasure(2)
    return IOExists3(Place, Place, bool)(
        lambda t1, t2, value: (
            random_bool_io(t_pre, value, t1) and
            Implies(value, conditionally_terminating_io(t1, value, t2)) and
            no_op_io(t1, t2) and
            no_op_io(t2, t_post)
        )
    )

# Termination measure.

@IOOperation
def test_measure_decreasing_io1(
        t_pre: Place,
        value: int,
        t_post: Place = Result()) -> bool:
    Terminates(True)
    TerminationMeasure(max(value, 2))
    #:: ExpectedOutput(termination_check.failed:measure.non_decreasing)
    return test_measure_decreasing_io1(t_pre, value, t_post)

@IOOperation
def test_measure_decreasing_io2(
        t_pre: Place,
        value: int,
        t_post: Place = Result()) -> bool:
    Terminates(True)
    TerminationMeasure(max(value, 2))
    #:: ExpectedOutput(termination_check.failed:measure.non_decreasing)
    return test_measure_decreasing_io2(t_pre, value-1, t_post)

@IOOperation
def test_measure_decreasing_io3(
        t_pre: Place,
        value: int,
        t_post: Place = Result()) -> bool:
    Terminates(True)
    TerminationMeasure(max(value+2, 2))
    return (test_measure_decreasing_io3(t_pre, value-1, t_post)
            if value > 0
            else
            no_op_io(t_pre, t_post))
