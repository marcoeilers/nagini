# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

class Test:
    @property
    def val(self) -> int:
        Requires(Acc(self._val))
        return self._val

    def __init__(self) -> None:
        self._val = 5