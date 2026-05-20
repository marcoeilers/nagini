# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

b_bar = 12


def baz(b: object = b_bar) -> int:
    return 12


#:: ExpectedOutput(type.error:Name "a_bar" is used before definition  [used-before-def])
def foo(a: object = a_bar) -> int:  # noqa: F821
    return 12

a_bar = 12