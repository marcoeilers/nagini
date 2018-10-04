from nagini_contracts.contracts import Result
from nagini_contracts.io_contracts import *


@IOOperation
def loop_io(
        t_pre: Place,
        value: int,
        ) -> bool:
    Terminates(False)


@IOOperation
def one_result_only(
        t_pre: Place,
        value: int = Result(),
        ) -> bool:
    Terminates(False)


@IOOperation
def postset_only(
        t_pre: Place,
        t_post: Place = Result(),
        ) -> bool:
    Terminates(False)
