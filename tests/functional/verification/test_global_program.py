# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import Invariant, Acc

c = [True]
try:
    cur = 10
    while cur > 0:
        Invariant(Acc(cur))
        Invariant(cur >= 0 and cur >= 0)
        cur-= 1
    c = [c[cur]]
except Exception as e:
    c = [False]

assert c
#:: ExpectedOutput(assert.failed:assertion.false)
assert False