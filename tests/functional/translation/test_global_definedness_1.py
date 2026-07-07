# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

a = 12

b = a + 1

#:: ExpectedOutput(type.error:Name "c" is used before definition  [used-before-def])
b = c + 1  # noqa: F821

c = 12