# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/


def f() -> bytes:
    #:: ExpectedOutput(unsupported:Unsupported variant of bytes().)
    return bytes("ab", "utf-8")
