# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class Something:

    def __init__(self, val: int) -> None:
        Ensures(Acc(self.value) and self.value == val)  # type: ignore
        self.value = val


class Other:
    pass


def main(b: bool) -> int:
    Ensures(Result() == (45 if b else 33))
    obj = None  # type: object
    if b:
        obj = Something(45)
    else:
        obj = Other()
    if isinstance(obj, Something):
        # access a field that we only know exists because of isinstance
        return obj.value
    else:
        return 33
