# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

a_bar = 12


class C:
    baz = a_bar


class D:
    #:: ExpectedOutput(expression.undefined:undefined.global.name)
    baz = b_bar  # noqa: F821

b_bar = 12