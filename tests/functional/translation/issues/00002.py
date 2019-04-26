# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def test1() -> None:
    #:: ExpectedOutput(type.error:Name 'MyException' is not defined)
    raise MyException()
