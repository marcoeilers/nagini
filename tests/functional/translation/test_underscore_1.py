# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/


def id(i: int) -> int:
    return i


def read_under(i: int) -> int:
    _ = id(i)
    #:: ExpectedOutput(invalid.program:wildcard.variable.read)
    return _
