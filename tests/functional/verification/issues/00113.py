# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List, Tuple

a = [1,2]
#:: UnexpectedOutput(carbon)(application.precondition:assertion.false, 113)|UnexpectedOutput(application.precondition:insufficient.permission, 113)|UnexpectedOutput(carbon)(application.precondition:insufficient.permission, 113)|UnexpectedOutput(carbon)(application.precondition:assertion.false, 113)|UnexpectedOutput(carbon)(postcondition.violated:assertion.false, 113)
b = a[1]