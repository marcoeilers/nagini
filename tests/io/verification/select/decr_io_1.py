from nagini_contracts.contracts import *
from nagini_contracts.io_contracts import *

@IOOperation
def decr_io_1(
        t_pre: Place,
        value: int,
        t_post: Place = Result()) -> bool:
    Terminates(True)
    TerminationMeasure(max(value, 2))
    #:: ExpectedOutput(termination_check.failed:measure.non_decreasing)
    return decr_io_1(t_pre, value, t_post)


@IOOperation
def decr_io_2(
        t_pre: Place,
        value: int,
        t_post: Place = Result()) -> bool:
    Terminates(True)
    TerminationMeasure(max(value, 2))
    #ExpectedOutput(termination_check.failed:measure.non_decreasing)  # not selected
    return decr_io_2(t_pre, value, t_post)