# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

def test() -> None:
    #:: ExpectedOutput(type.error:Name 'foo' is not defined)
    foo()  # noqa: F821
