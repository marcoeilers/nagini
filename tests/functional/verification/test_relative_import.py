from nagini_contracts.contracts import *
from resources.import_for_00269 import foo

x = foo()
Assert(x > 2)
#:: ExpectedOutput(assert.failed:assertion.false)
Assert(x == 4)