# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def some_string_ops() -> None:
    str1 = "asd"
    str2 = "asd"
    str5 = "asf"
    str3 = "asdasdasd"
    Assert(isinstance(str1, str))
    Assert(len(str1) == 3)
    Assert(str1 == str2)
    Assert(str1 != str3)
    Assert(str1 != str5)
    str4 = str1 + str2
    Assert(str4 != str3)
    Assert(len(str4) == 6)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(str2 == str3)