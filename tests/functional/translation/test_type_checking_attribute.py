# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

import typing


def running() -> int:
    #:: ExpectedOutput(unsupported:TYPE_CHECKING is only supported as the test of a module-level if without else that holds only imports)
    return 1 if typing.TYPE_CHECKING else 2
