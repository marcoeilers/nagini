# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

x = 5
s1 = str(x)
s2 = str(x)

assert s1 == s2
#:: ExpectedOutput(assert.failed:assertion.false)
assert s1 is s2