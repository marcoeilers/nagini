# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

a = 1

import resources.test_import_execution_1

assert a == 2

from resources.test_import_execution_2 import wow

assert a == 3

#:: ExpectedOutput(assert.failed:assertion.false)
assert a == 4