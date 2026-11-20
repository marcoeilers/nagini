# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from typing import TYPE_CHECKING


def running() -> int:
    #:: ExpectedOutput(unsupported:TYPE_CHECKING is only supported as the test of a module-level if without else that holds only imports)
    if TYPE_CHECKING:
        return 1
    return 2
