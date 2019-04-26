# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/


def from_type() -> None:
    #:: ExpectedOutput(type.error:Exception must be derived from BaseException)
    raise Exception() from 2