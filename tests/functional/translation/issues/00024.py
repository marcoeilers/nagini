# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

def bla() -> None:
    #:: ExpectedOutput(type.error:Cannot resolve name "a" (possible cyclic definition)  [misc])
    a = a  # noqa: F821
